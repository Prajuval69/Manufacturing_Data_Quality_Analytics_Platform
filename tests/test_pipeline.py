import json
import sqlite3
from contextlib import closing
import pandas as pd
import pytest
from src.config import TABLES, Settings
from src.pipeline.run import run
from src.pipeline.ingestion import ingest
from src.data.generate import generate
from src.quality.engine import weighted_score
from src.verification import verify, snapshot_fingerprint
from src.analytics.kpis import latest_inventory

def test_database_integrity(conn):
    assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert not conn.execute("PRAGMA foreign_key_check").fetchall()

def test_record_reconciliation(built, conn):
    summary = built[1]
    assert summary["raw_records"] == summary["curated_records"] + summary["quarantined_records"]
    assert summary["curated_records"] == sum(conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in TABLES)

def test_exception_per_failed_check(conn):
    assert conn.execute("SELECT SUM(records_failed) FROM dq_result").fetchone()[0] == conn.execute("SELECT COUNT(*) FROM dq_exception").fetchone()[0]
    assert conn.execute("SELECT COUNT(*) FROM dq_exception WHERE status='Resolved' AND resolution_note='Automatic canonical repair'").fetchone()[0] > 0

def test_all_dimensions_evaluated(conn):
    dimensions = {r[0] for r in conn.execute("SELECT DISTINCT dimension FROM dq_rule")}
    assert dimensions == {"completeness", "validity", "consistency", "uniqueness", "referential_integrity", "timeliness", "anomaly"}
    assert conn.execute("SELECT COUNT(*) FROM dq_result WHERE records_checked>0").fetchone()[0] == conn.execute("SELECT COUNT(*) FROM dq_rule WHERE active=1").fetchone()[0]

def test_persisted_score_recalculates(conn):
    checks = pd.read_sql_query("SELECT dimension,passed FROM dq_check", conn)
    run_record = conn.execute("SELECT weights_json,overall_score FROM dq_run").fetchone()
    assert weighted_score(checks, json.loads(run_record[0])) == run_record[1]

def test_nonnegative_fact_constraints(conn):
    conn.execute("PRAGMA foreign_keys=ON")
    key = conn.execute("SELECT order_id FROM fact_sales_order LIMIT 1").fetchone()[0]
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE fact_sales_order SET quantity=-1 WHERE order_id=?", (key,))
    conn.rollback()

def test_foreign_key_constraint(conn):
    conn.execute("PRAGMA foreign_keys=ON")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE fact_sales_order SET customer_id='ABSENT'")
    conn.rollback()

def test_master_keys_unique(conn):
    for table, (_, _, key, _, _) in TABLES.items():
        count, unique = conn.execute(f"SELECT COUNT(*),COUNT(DISTINCT {key}) FROM {table}").fetchone()
        assert count == unique

def test_governance_coverage(conn):
    assert conn.execute("SELECT COUNT(*) FROM metadata_catalog").fetchone()[0] == sum(len(t[4]) for t in TABLES.values())
    assert conn.execute("SELECT COUNT(*) FROM business_glossary").fetchone()[0] >= 15
    assert conn.execute("SELECT COUNT(*) FROM data_lineage").fetchone()[0] >= 5 * len(TABLES)
    assert conn.execute("SELECT COUNT(*) FROM data_lineage WHERE target='dq_exception'").fetchone()[0] == len(TABLES)
    assert conn.execute("SELECT MIN(metadata_coverage),MIN(ownership_coverage) FROM governance_coverage").fetchone()[:] == (1., 1.)

def test_kpis_reconcile(conn):
    summary = conn.execute("SELECT * FROM executive_kpis").fetchone()
    assert summary["total_orders"] == conn.execute("SELECT COUNT(*) FROM fact_sales_order").fetchone()[0]
    assert summary["sales_value"] == conn.execute("SELECT SUM(quantity*unit_price) FROM fact_sales_order").fetchone()[0]
    assert summary["production_quantity"] == conn.execute("SELECT SUM(quantity) FROM fact_production").fetchone()[0]
    expected = conn.execute("SELECT AVG(CASE WHEN delivery_date <= promised_date THEN 1.0 ELSE 0 END) FROM fact_shipment").fetchone()[0]
    assert abs(summary["on_time_delivery_rate"] - expected) < 1e-10

def test_inventory_snapshot_not_time_sum():
    frame = pd.DataFrame({"facility_id": ["F1"]*3, "product_id": ["P1"]*3, "warehouse_id": ["W1"]*3, "inventory_id": ["I1","I2","I3"], "stock_date": ["2025-01-01","2025-01-02","2025-01-02"], "quantity": [100,200,300]})
    assert latest_inventory(frame).quantity.sum() == 300

def test_exports_and_acceptance(built):
    assert verify(built[0])["failed"] == 0

def test_schema_drift_rejected(tmp_path):
    settings = Settings(root=tmp_path)
    generate(settings, .02)
    path = tmp_path / "data/raw/erp/customers.csv"
    pd.read_csv(path).drop(columns="country").to_csv(path, index=False)
    with pytest.raises(ValueError, match="Schema drift"):
        ingest(settings)

def test_pristine_pipeline_has_no_failures(tmp_path):
    settings = Settings(root=tmp_path, corruption_rate=0, database_url="sqlite:///data/processed/packright.db")
    generate(settings, .04)
    result = run(settings)
    assert result["exception_count"] == 0
    assert result["overall_score"] == 100
    assert result["quarantined_records"] == 0

def test_rerun_idempotency_preserves_resolution(built):
    settings = built[0]
    with closing(sqlite3.connect(settings.db_path)) as conn, conn:
        eid = conn.execute("SELECT exception_id FROM dq_exception WHERE status='Open' LIMIT 1").fetchone()[0]
        conn.execute("UPDATE dq_exception SET status='Accepted',resolution_note='Reviewed synthetic anomaly' WHERE exception_id=?", (eid,))
        conn.execute("UPDATE executive_kpis SET open_exceptions=(SELECT COUNT(*) FROM dq_exception WHERE status IN ('Open','In Review')),critical_exceptions=(SELECT COUNT(*) FROM dq_exception WHERE status IN ('Open','In Review') AND severity='Critical')")
    before = snapshot_fingerprint(settings)
    result = run(settings)
    after = snapshot_fingerprint(settings)
    assert before == after
    assert result["run_id"] == built[1]["run_id"]
    with closing(sqlite3.connect(settings.db_path)) as conn:
        assert conn.execute("SELECT status,resolution_note FROM dq_exception WHERE exception_id=?", (eid,)).fetchone() == ("Accepted", "Reviewed synthetic anomaly")
