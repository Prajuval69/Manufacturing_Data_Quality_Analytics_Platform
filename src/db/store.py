"""Constrained SQLite snapshot built transactionally, then atomically published."""
import json
import os
import sqlite3
from contextlib import closing
import pandas as pd
from src.config import TABLES, FOREIGN_KEYS, LOAD_ORDER

def schema_sql():
    ddl = ["PRAGMA foreign_keys=ON;"]
    for table in LOAD_ORDER:
        _, _, key, _, columns = TABLES[table]
        fields = []
        for col in columns:
            typ = "REAL" if col in ["quantity", "unit_price"] else "TEXT"
            part = f'"{col}" {typ} NOT NULL'
            if col == key:
                part += " PRIMARY KEY"
            if col in ["quantity", "unit_price"]:
                part += f' CHECK ("{col}" >= 0)'
            if col == "uom":
                part += " CHECK (uom IN ('EA','KG','L'))"
            if col.endswith("_date"):
                part += f' CHECK (length("{col}")=10 AND date("{col}") IS NOT NULL)'
            if col in FOREIGN_KEYS.get(table, {}):
                target = FOREIGN_KEYS[table][col]
                part += f' REFERENCES {target}({TABLES[target][2]})'
            fields.append(part)
        ddl.append(f"CREATE TABLE {table} ({', '.join(fields)});")
        for col in FOREIGN_KEYS.get(table, {}):
            ddl.append(f"CREATE INDEX ix_{table}_{col} ON {table}({col});")
        date = TABLES[table][3]
        if date:
            ddl.append(f"CREATE INDEX ix_{table}_date ON {table}({date});")
    ddl.extend([
        "CREATE TABLE ref_uom (uom TEXT PRIMARY KEY, description TEXT NOT NULL);",
        "CREATE TABLE ref_product_category (category TEXT PRIMARY KEY);",
        "CREATE TABLE dq_run (run_id TEXT PRIMARY KEY, started_at TEXT NOT NULL, completed_at TEXT NOT NULL, as_of TEXT NOT NULL, overall_score REAL CHECK(overall_score BETWEEN 0 AND 100), raw_records INTEGER, curated_records INTEGER, quarantined_records INTEGER, rule_count INTEGER, exception_count INTEGER, weights_json TEXT NOT NULL, input_hash TEXT NOT NULL);",
        "CREATE TABLE dq_rule (rule_id TEXT PRIMARY KEY, rule_name TEXT, description TEXT, dimension TEXT, severity TEXT, source_system TEXT, table_name TEXT, column_name TEXT, validation_logic TEXT, phase TEXT, reject INTEGER, active INTEGER, parameters TEXT);",
        "CREATE TABLE dq_result (run_id TEXT REFERENCES dq_run(run_id), rule_id TEXT REFERENCES dq_rule(rule_id), records_checked INTEGER, records_passed INTEGER, records_failed INTEGER, pass_rate REAL, failure_rate REAL, severity TEXT, executed_at TEXT, affected_records TEXT, PRIMARY KEY(run_id,rule_id), CHECK(records_passed+records_failed=records_checked));",
        "CREATE TABLE dq_exception (exception_id TEXT PRIMARY KEY, run_id TEXT REFERENCES dq_run(run_id), rule_id TEXT REFERENCES dq_rule(rule_id), source_system TEXT, table_name TEXT, record_key TEXT, source_row INTEGER, column_name TEXT, current_value TEXT, expected_condition TEXT, severity TEXT CHECK(severity IN ('Critical','High','Medium','Low')), status TEXT CHECK(status IN ('Open','In Review','Resolved','Accepted')), detected_at TEXT, assigned_to TEXT, resolution_note TEXT, resolved_at TEXT, facility_id TEXT, month TEXT);",
        "CREATE INDEX ix_exception_status ON dq_exception(status,severity);",
        "CREATE INDEX ix_exception_facility ON dq_exception(facility_id);",
        "CREATE TABLE dq_check (run_id TEXT REFERENCES dq_run(run_id), rule_id TEXT REFERENCES dq_rule(rule_id), table_name TEXT, source_row INTEGER, source_system TEXT, dimension TEXT, facility_id TEXT, month TEXT, passed INTEGER CHECK(passed IN (0,1)), PRIMARY KEY(run_id,rule_id,source_row));",
        "CREATE INDEX ix_check_scope ON dq_check(source_system,facility_id,month);",
        "CREATE TABLE dq_score (scope TEXT, group_name TEXT, score REAL, checks INTEGER, failed_checks INTEGER, PRIMARY KEY(scope,group_name));",
        "CREATE TABLE metadata_catalog (table_name TEXT, field_name TEXT, business_name TEXT, description TEXT, data_type TEXT, source_system TEXT, sensitivity TEXT, owner TEXT, refresh_frequency TEXT, critical_data_element INTEGER, PRIMARY KEY(table_name,field_name));",
        "CREATE TABLE business_glossary (term TEXT PRIMARY KEY, definition TEXT, business_owner TEXT, related_field TEXT, calculation TEXT);",
        "CREATE TABLE data_lineage (lineage_id TEXT PRIMARY KEY, source TEXT, transformation TEXT, target TEXT, description TEXT);",
        "CREATE TABLE data_owner (table_name TEXT PRIMARY KEY, owner TEXT, steward TEXT, responsibility TEXT);",
        "CREATE TABLE profiling_result (table_name TEXT, stage TEXT, column_name TEXT, row_count INTEGER, column_count INTEGER, data_type TEXT, null_count INTEGER, null_percentage REAL, unique_count INTEGER, duplicate_count INTEGER, row_duplicate_count INTEGER, min_value TEXT, max_value TEXT, mean_value REAL, median_value REAL, sample_values TEXT, PRIMARY KEY(table_name,stage,column_name));",
        "CREATE TABLE executive_kpis (total_orders INTEGER, order_quantity REAL, average_order_quantity REAL, sales_value REAL, production_quantity REAL, inventory_quantity REAL, inventory_snapshot_date TEXT, shipments INTEGER, delivered_shipments INTEGER, on_time_delivery_rate REAL, average_delivery_delay REAL, late_shipments INTEGER, order_fulfillment_rate REAL, dq_score REAL, failed_rules INTEGER, open_exceptions INTEGER, critical_exceptions INTEGER);",
    ])
    metric_cols = "total_orders INTEGER, order_quantity REAL, production_quantity REAL, inventory_quantity REAL, shipments INTEGER, late_shipments INTEGER, on_time_delivery_rate REAL"
    ddl.extend([
        f"CREATE TABLE kpi_daily (date TEXT PRIMARY KEY, {metric_cols});",
        f"CREATE TABLE kpi_monthly (month TEXT PRIMARY KEY, {metric_cols});",
        f"CREATE TABLE facility_performance (facility_id TEXT PRIMARY KEY REFERENCES dim_facility(facility_id), facility_name TEXT, {metric_cols});",
        f"CREATE TABLE product_performance (product_id TEXT PRIMARY KEY REFERENCES dim_product(product_id), category TEXT, {metric_cols});",
        f"CREATE TABLE category_performance (category TEXT PRIMARY KEY, {metric_cols});",
        "CREATE TABLE inventory_trend (month TEXT, facility_id TEXT, product_id TEXT, quantity REAL, snapshot_date TEXT, PRIMARY KEY(month,facility_id,product_id));",
        "CREATE TABLE governance_coverage (table_name TEXT PRIMARY KEY, fields INTEGER, documented_fields INTEGER, owned_fields INTEGER, critical_fields INTEGER, documented_critical_fields INTEGER, lineage_edges INTEGER, glossary_terms INTEGER, metadata_coverage REAL, ownership_coverage REAL, critical_coverage REAL);",
    ])
    return "\n".join(ddl) + "\n"

def append_frame(conn, table, frame):
    if not frame.empty:
        frame.to_sql(table, conn, if_exists="append", index=False, chunksize=2000)

def previous_states(path):
    if not path.exists():
        return {}, None
    with closing(sqlite3.connect(path)) as conn:
        if not conn.execute("SELECT name FROM sqlite_master WHERE name='dq_exception'").fetchone():
            return {}, None
        states = {r[0]: r[1:] for r in conn.execute("SELECT exception_id,status,assigned_to,resolution_note,resolved_at,detected_at FROM dq_exception")}
        run = conn.execute("SELECT run_id,started_at FROM dq_run").fetchone()
        return states, run

def publish(settings, curated, reference, run, rules, results, exceptions, checks, scores, profiles, governance, analytics):
    build_path = settings.db_path.with_suffix(".building")
    if build_path.exists():
        build_path.unlink()
    schema = schema_sql()
    (settings.root / "database/schema.sql").write_text(schema, encoding="utf-8")
    (settings.root / "database/seed.sql").write_text("-- Synthetic reference examples; the pipeline loads all CSV references.\nINSERT INTO ref_uom VALUES ('EA','Each'),('KG','Kilogram'),('L','Litre');\n", encoding="utf-8")
    conn = sqlite3.connect(build_path)
    try:
        conn.executescript(schema)
        for table in LOAD_ORDER:
            append_frame(conn, table, curated[table][TABLES[table][4]])
        append_frame(conn, "ref_uom", pd.read_csv(settings.root / "data/reference/uom.csv"))
        append_frame(conn, "ref_product_category", pd.read_csv(settings.root / "data/reference/product_categories.csv"))
        append_frame(conn, "dq_run", pd.DataFrame([run]))
        catalog = pd.DataFrame(rules)
        catalog["parameters"] = catalog.parameters.map(lambda p: json.dumps(p, sort_keys=True))
        append_frame(conn, "dq_rule", catalog)
        append_frame(conn, "dq_result", pd.DataFrame(results))
        append_frame(conn, "dq_exception", exceptions)
        append_frame(conn, "dq_check", checks)
        append_frame(conn, "dq_score", scores)
        append_frame(conn, "profiling_result", profiles)
        for table, frame in {**governance, **analytics}.items():
            append_frame(conn, table, frame)
        failures = conn.execute("PRAGMA foreign_key_check").fetchall()
        if failures:
            raise ValueError(f"Foreign key violations: {failures[:5]}")
        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("SQLite integrity check failed")
        conn.commit()
    finally:
        conn.close()
    os.replace(build_path, settings.db_path)
