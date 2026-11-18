"""Exports reflect the persisted snapshot, including steward status updates."""
import json
import sqlite3
from contextlib import closing
import pandas as pd
from src.config import TABLES

def export(settings):
    settings.prepare()
    with closing(sqlite3.connect(settings.db_path)) as conn:
        mapping = {**{name: name for name in TABLES}, **{name: name for name in ["executive_kpis", "kpi_daily", "kpi_monthly", "facility_performance", "product_performance", "category_performance", "inventory_trend", "governance_coverage", "dq_exception", "dq_rule", "dq_result"]}}
        mapping.update({"dq_summary": "dq_score", "dq_exceptions": "dq_exception"})
        mapping.pop("dq_exception")
        for filename, table in mapping.items():
            pd.read_sql_query(f'SELECT * FROM "{table}"', conn).to_csv(settings.root / "outputs/powerbi" / f"{filename}.csv", index=False)
        scores = pd.read_sql_query("SELECT * FROM dq_score WHERE scope='month' ORDER BY group_name", conn)
        scores.to_csv(settings.root / "outputs/powerbi/dq_trend.csv", index=False)
        calendar = pd.DataFrame({"date": pd.date_range("2025-01-01", "2026-07-31").strftime("%Y-%m-%d")})
        calendar["month"] = calendar.date.str[:7]
        calendar["year"] = calendar.date.str[:4].astype(int)
        calendar.to_csv(settings.root / "outputs/powerbi/dim_date.csv", index=False)
        pd.DataFrame({"month": calendar.month.drop_duplicates().tolist()}).to_csv(settings.root / "outputs/powerbi/dim_month.csv", index=False)
        inventory_snapshot = pd.read_sql_query("SELECT inventory_id,product_id,facility_id,warehouse_id,stock_date,quantity,uom FROM (SELECT *,ROW_NUMBER() OVER(PARTITION BY facility_id,product_id,warehouse_id ORDER BY stock_date DESC,inventory_id DESC) AS occurrence FROM fact_inventory) WHERE occurrence=1", conn)
        inventory_snapshot.to_csv(settings.root / "outputs/powerbi/inventory_snapshot.csv", index=False)
        for table in ["metadata_catalog", "business_glossary", "data_lineage", "data_owner"]:
            pd.read_sql_query(f"SELECT * FROM {table}", conn).to_csv(settings.root / "outputs/governance" / f"{table}.csv", index=False)
        profile = pd.read_sql_query("SELECT * FROM profiling_result", conn)
        profile.to_csv(settings.root / "outputs/profiling/profile.csv", index=False)
        summary = pd.read_sql_query("SELECT * FROM executive_kpis", conn).iloc[0].to_dict()
        (settings.root / "outputs/reports/kpi_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        top = pd.read_sql_query("SELECT rule_id,records_checked,records_failed,failure_rate,severity FROM dq_result WHERE records_failed>0 ORDER BY records_failed DESC LIMIT 15", conn)
        top.to_csv(settings.root / "outputs/reports/top_failed_rules.csv", index=False)
        flags = []
        for table, (_, _, key, _, _) in TABLES.items():
            frame = pd.read_sql_query(f"SELECT '{table}' AS table_name,t.{key} AS record_key,COUNT(e.exception_id) AS exception_count,MAX(CASE WHEN r.dimension='anomaly' THEN 1 ELSE 0 END) AS has_anomaly,MAX(CASE WHEN e.status IN ('Open','In Review') THEN 1 ELSE 0 END) AS has_open_exception FROM {table} t JOIN dq_exception e ON e.table_name=? AND e.record_key=t.{key} JOIN dq_rule r ON r.rule_id=e.rule_id GROUP BY t.{key}", conn, params=(table,))
            flags.append(frame)
        pd.concat(flags, ignore_index=True).to_csv(settings.root / "outputs/powerbi/data_quality_flags.csv", index=False)
        report = f"# PackRight synthetic batch readout\n\nOrders: {summary['total_orders']:,.0f}; production: {summary['production_quantity']:,.0f} EA; latest observed inventory: {summary['inventory_quantity']:,.0f} EA.\n\nOn-time delivery: {summary['on_time_delivery_rate']:.2%}; open/in-review exceptions: {summary['open_exceptions']:,.0f}; incoming DQ score: {summary['dq_score']:.4f}/100.\n\nBlocking checks quarantine invalid rows. Anomalies remain visible and can inflate quantities; join data_quality_flags.csv by table and record key to inspect or exclude them in reporting. The DQ score is a weighted check pass rate, not the percentage of trusted records.\n\nMost frequent failed rules:\n\n"
        report += "\n".join(f"- {r.rule_id}: {r.records_failed} of {r.records_checked} checks ({r.failure_rate:.2%}); {r.severity}." for r in top.itertuples())
        (settings.root / "outputs/reports/BATCH_READOUT.md").write_text(report + "\n", encoding="utf-8")
        edges = pd.read_sql_query("SELECT * FROM data_lineage", conn)
        lineage = "# Actual source-to-output lineage\n\nEvery input is synthetic PackRight data.\n\n" + "\n".join(f"- `{r.source}` → `{r.target}`: {r.transformation}." for r in edges.itertuples())
        (settings.root / "docs/LINEAGE.md").write_text(lineage + "\n", encoding="utf-8")
        dictionary = pd.read_sql_query("SELECT * FROM metadata_catalog", conn)
        doc = "# Data dictionary\n\nGenerated from the actual field contracts. See DATA_MODEL.md for table grains.\n\n|Table|Field|Type|Meaning|Critical|Owner|\n|---|---|---|---|---|---|\n"
        doc += "\n".join(f"|{r.table_name}|{r.field_name}|{r.data_type}|{r.description}|{bool(r.critical_data_element)}|{r.owner}|" for r in dictionary.itertuples())
        (settings.root / "docs/DATA_DICTIONARY.md").write_text(doc + "\n", encoding="utf-8")
        rules = pd.read_sql_query("SELECT * FROM dq_rule", conn)
        doc = "# Executed rule catalog\n\nDefinitions are in config/dq_rules.json. Raw-phase checks measure incoming uniqueness and canonical formatting. Other checks run on standardized rows, against accepted parents.\n\n|Rule ID|Dimension|Severity|Phase|Blocking|Logic parameters|\n|---|---|---|---|---|---|\n"
        doc += "\n".join(f"|{r.rule_id}|{r.dimension}|{r.severity}|{r.phase}|{bool(r.reject)}|{r.parameters}|" for r in rules.itertuples())
        (settings.root / "docs/DATA_QUALITY_RULES.md").write_text(doc + "\n", encoding="utf-8")
    return len(mapping) + 5
