"""Inspectable acceptance evidence: joins, counts, rules, exports and score."""
import hashlib
import json
import sqlite3
from contextlib import closing
import pandas as pd
from src.config import TABLES
from src.quality.engine import weighted_score, failure_mask
from src.pipeline.ingestion import references

def snapshot_fingerprint(settings):
    result = {}
    with closing(sqlite3.connect(settings.db_path)) as conn:
        for table in list(TABLES) + ["dq_rule", "dq_result", "dq_exception", "dq_check", "dq_score", "executive_kpis", "metadata_catalog", "business_glossary", "data_lineage"]:
            # Timestamps may change on execution, but measured rows and identities must not.
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})") if r[1] not in ["started_at", "completed_at", "executed_at", "detected_at", "resolved_at"]]
            rows = conn.execute(f"SELECT {','.join(cols)} FROM {table} ORDER BY {','.join(cols)}").fetchall()
            result[table] = {"count": len(rows), "sha256": hashlib.sha256(json.dumps(rows, default=str).encode()).hexdigest()}
    return result

def verify(settings):
    checks = []
    def check(name, condition, details):
        checks.append({"check": name, "passed": bool(condition), "details": details})
    with closing(sqlite3.connect(settings.db_path)) as conn:
        conn.row_factory = sqlite3.Row
        run = dict(conn.execute("SELECT * FROM dq_run").fetchone())
        check("database_integrity", conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "PRAGMA integrity_check")
        fk = conn.execute("PRAGMA foreign_key_check").fetchall()
        check("foreign_keys", not fk, f"{len(fk)} violations")
        check("counts_reconcile", run["raw_records"] == run["curated_records"] + run["quarantined_records"], run)
        for table in TABLES:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            path = settings.root / "outputs/powerbi" / f"{table}.csv"
            exported = pd.read_csv(path)
            check("export_" + table, len(exported) == count and (count > 0), {"database": count, "csv": len(exported)})
            key = TABLES[table][2]
            check("unique_" + table, exported[key].is_unique, key)
        exception_count = conn.execute("SELECT COUNT(*) FROM dq_exception").fetchone()[0]
        failed = conn.execute("SELECT SUM(records_failed) FROM dq_result").fetchone()[0]
        check("exception_evidence", failed == exception_count == run["exception_count"], {"failed_checks": failed, "exceptions": exception_count})
        row_checks = pd.read_sql_query("SELECT dimension,passed FROM dq_check", conn)
        score = weighted_score(row_checks, json.loads(run["weights_json"]))
        check("score_recalculation", score == run["overall_score"], {"recalculated": score, "stored": run["overall_score"]})
        check("rules_executed", conn.execute("SELECT COUNT(*) FROM dq_result").fetchone()[0] == run["rule_count"], run["rule_count"])
        curated = {table: pd.read_sql_query(f"SELECT * FROM {table}", conn) for table in TABLES}
        reference = references(settings)
        rule_rows = [dict(row) for row in conn.execute("SELECT * FROM dq_rule WHERE active=1 AND reject=1")]
        residual = []
        for rule in rule_rows:
            rule["parameters"] = json.loads(rule["parameters"])
            failed_rows = int(failure_mask(rule, curated[rule["table_name"]], curated, reference, run["as_of"]).sum())
            if failed_rows:
                residual.append({"rule_id": rule["rule_id"], "failures": failed_rows})
        check("curated_blocking_rules", not residual, residual or "Every blocking rule passes on curated records")
        metadata_count = conn.execute("SELECT COUNT(*) FROM metadata_catalog").fetchone()[0]
        check("metadata_contract_coverage", metadata_count == sum(len(v[4]) for v in TABLES.values()), metadata_count)
        glossary_count = conn.execute("SELECT COUNT(*) FROM business_glossary").fetchone()[0]
        check("business_glossary", glossary_count >= 15, glossary_count)
        months = conn.execute("SELECT COUNT(*) FROM kpi_monthly").fetchone()[0]
        check("transaction_period", months >= 12, {"months": months})
        summary = dict(conn.execute("SELECT * FROM executive_kpis").fetchone())
        sales_value = conn.execute("SELECT SUM(quantity*unit_price) FROM fact_sales_order").fetchone()[0]
        inventory = conn.execute("SELECT SUM(quantity) FROM (SELECT quantity, ROW_NUMBER() OVER (PARTITION BY facility_id,product_id,warehouse_id ORDER BY stock_date DESC,inventory_id DESC) n FROM fact_inventory) WHERE n=1").fetchone()[0]
        check("sales_reconciliation", summary["sales_value"] == sales_value, sales_value)
        check("inventory_snapshot_reconciliation", summary["inventory_quantity"] == inventory, inventory)
        check("kpi_ranges", 0 <= summary["on_time_delivery_rate"] <= 1 and 0 <= summary["order_fulfillment_rate"] <= 1, summary)
        check("meaningful_kpis", summary["total_orders"] > 0 and summary["production_quantity"] > 0 and summary["shipments"] > 0, summary)
        check("no_fake_pbix", not list(settings.root.rglob("*.pbix")), "CSV-based Power BI implementation")
    evidence = {"passed": sum(c["passed"] for c in checks), "failed": sum(not c["passed"] for c in checks), "checks": checks}
    (settings.root / "outputs/reports/verification.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    if evidence["failed"]:
        raise ValueError("Acceptance checks failed; inspect outputs/reports/verification.json")
    return evidence
