"""Compose BUILD_VERIFICATION.md from actual generated evidence, never constants."""
import json
from pathlib import Path
import sqlite3
from contextlib import closing
from datetime import datetime
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import Settings

def receipt():
    settings = Settings()
    root = settings.root
    def read(name):
        return json.loads((root / "outputs/reports" / name).read_text(encoding="utf-8"))
    pipeline = read("pipeline_summary.json")
    manifest = json.loads((root / "data/raw/manifest.json").read_text(encoding="utf-8"))
    verification = read("verification.json")
    rerun = read("rerun_verification.json")
    smoke = read("api_smoke.json")
    audit = read("hygiene_audit.json")
    xml = ET.parse(root / "outputs/reports/pytest.xml").getroot()
    suites = xml.findall("testsuite") if xml.tag == "testsuites" else [xml]
    tests = sum(int(s.get("tests", 0)) for s in suites)
    failures = sum(int(s.get("failures", 0)) for s in suites)
    errors = sum(int(s.get("errors", 0)) for s in suites)
    skipped = sum(int(s.get("skipped", 0)) for s in suites)
    passed = tests - failures - errors - skipped
    assert failures == errors == skipped == verification["failed"] == smoke["failed"] == 0
    assert audit["passed"] and rerun["same_raw_sources"] and rerun["same_database_fingerprints"]
    with closing(sqlite3.connect(settings.db_path)) as conn:
        current_run = conn.execute("SELECT run_id FROM dq_run").fetchone()[0]
        verified_run = next(c["details"]["run_id"] for c in verification["checks"] if c["check"] == "counts_reconcile")
        assert current_run == pipeline["run_id"] == rerun["run_id"] == smoke["run_id"] == verified_run
        counts = {table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in ["metadata_catalog", "business_glossary", "data_lineage", "data_owner", "dq_check", "kpi_daily", "kpi_monthly", "facility_performance", "product_performance"]}
        status = dict(conn.execute("SELECT status,COUNT(*) FROM dq_exception GROUP BY status").fetchall())
        severity = dict(conn.execute("SELECT severity,COUNT(*) FROM dq_exception GROUP BY severity").fetchall())
    now = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S IST")
    text = f"# Build verification — actual execution receipt\n\nVerified {now}. All data is synthetic PackRight Manufacturing; no confidential Greif data.\n\n"
    text += f"Snapshot `{current_run}`; seed {manifest['seed']}; corruption budget {manifest['corruption_rate']}; fixed validation as-of {pipeline['as_of']}. Generated business period: {manifest['period'][0]}–{manifest['period'][1]}; shipment completions can extend beyond order dates.\n\n"
    text += f"- Raw business-source occurrences: **{pipeline['raw_records']:,}** (includes controlled duplicate rows and order lines; excludes separate canonical reference copies).\n- Curated records: **{pipeline['curated_records']:,}**.\n- Quarantined records: **{pipeline['quarantined_records']:,}**.\n- Active/executed rules: **{pipeline['rule_count']}** across seven dimensions.\n- Row-level rule checks: **{counts['dq_check']:,}**.\n- Exceptions / failed checks: **{pipeline['exception_count']:,}**.\n- Overall incoming DQ score: **{pipeline['overall_score']:.4f}/100**.\n- Tests: **{passed} passed, {failures} failed, {errors} errors, {skipped} skipped**.\n- Full-scale acceptance checks: **{verification['passed']} passed, {verification['failed']} failed**.\n- Live loopback HTTP checks: **{smoke['passed']} passed, {smoke['failed']} failed**, at `{smoke['base_url']}`.\n- Assistant smoke mode: **{smoke['assistant_mode']}**.\n\n"
    text += "## Record counts\n\n|Table|Raw|Curated|Quarantined|\n|---|---:|---:|---:|\n"
    text += "\n".join(f"|{t}|{c['raw']:,}|{c['curated']:,}|{c['quarantined']:,}|" for t,c in pipeline["counts"].items()) + "\n\n"
    text += "## DQ evidence\n\nScores are weighted check pass rates; accepted-record percentages have a different denominator. All blocking rules were rerun against curated rows and passed. Anomaly flags remain for review.\n\n|Dimension|Score|Checks|Failures|\n|---|---:|---:|---:|\n"
    text += "\n".join(f"|{d['group_name']}|{d['score']:.4f}|{d['checks']:,}|{d['failed_checks']:,}|" for d in pipeline["dimension_scores"]) + "\n\n"
    text += f"Exception statuses: `{json.dumps(status, sort_keys=True)}`. Severity counts: `{json.dumps(severity, sort_keys=True)}`. One failed rule on one occurrence creates one exception; exceptions can exceed defective-row counts.\n\n"
    text += "## Governance and analytics\n\n" + "\n".join(f"- `{t}`: {c:,} rows." for t,c in counts.items() if t != "dq_check") + "\n\n"
    files = sorted((root / "outputs/powerbi").glob("*.csv"))
    text += f"Power BI outputs: **{len(files)} actual CSV files**, including executive KPIs, facility/product/category performance, inventory snapshots/trends, DQ scores/trends/exceptions/rules/results, anomaly flags, calendar/month dimensions, core facts/masters and governance coverage. Profiling and governance CSVs are separately populated. Read `outputs/reports/BATCH_READOUT.md` for measured business totals and caveats.\n\n"
    text += "## API smoke results\n\n|Method|Endpoint|HTTP|Pass|\n|---|---|---:|---|\n"
    text += "\n".join(f"|{r['method']}|{r['path']}|{r['status']}|{r['passed']}|" for r in smoke["results"]) + "\n\n"
    text += "## Reproducibility and hygiene\n\nThe full default dataset was regenerated and the pipeline rerun. Raw CSV hashes and measured database-table hashes matched exactly; row counts, keys, exceptions, scores and KPIs did not duplicate or drift. The integration test also verifies preserving an Accepted status and resolution note across reruns. Execution timestamps are intentionally excluded from content fingerprints.\n\n"
    text += f"Parsed {audit['python_files_parsed']} Python files; no hardcoded host paths or recognized embedded token patterns were found in source/generated outputs. `.env` is ignored and the example key is empty. No fake PBIX, temporary database-build files or missing required documentation. SQLite integrity and foreign-key checks passed; exports reconcile to database counts. `pip check` and source compilation were also run. There is no Git repository initialized in this workspace, so the receipt covers local source/output hygiene rather than a commit-history secret audit.\n\n"
    text += "## Limitations\n\nPower BI Desktop was not found; CSVs and a detailed implementation guide replace PBIX delivery. No external LLM credential was configured; deterministic behavior is tested and the optional provider interface is mock-tested, but no real paid provider request is claimed. This is a local single-writer batch snapshot with no authentication, historical-run warehouse, full workflow audit history or live freshness SLA. Stop the API before database rebuilds on Windows. Retained anomalies can inflate quantities, and inventory trends report observed balances rather than a full month-end stock ledger.\n\n"
    text += "## Reproduce\n\n```powershell\npython -m venv .venv\n.\\.venv\\Scripts\\python.exe -m pip install -r requirements-lock.txt\n.\\.venv\\Scripts\\python.exe -m src.cli all\n.\\.venv\\Scripts\\python.exe -m src.cli verify\n.\\.venv\\Scripts\\python.exe scripts/check_rerun.py\n.\\.venv\\Scripts\\python.exe -m pytest -q --junitxml=outputs/reports/pytest.xml\n.\\.venv\\Scripts\\python.exe -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000\n# In a second terminal:\n.\\.venv\\Scripts\\python.exe scripts/smoke_api.py\n.\\.venv\\Scripts\\python.exe scripts/audit_project.py\n.\\.venv\\Scripts\\python.exe scripts/build_receipt.py\n```\n\nEvidence: pipeline_summary.json, verification.json, rerun_verification.json, api_smoke.json, hygiene_audit.json and pytest.xml in `outputs/reports/`.\n"
    (root / "docs/BUILD_VERIFICATION.md").write_text(text, encoding="utf-8")
    return {"tests_passed": passed, "api_checks_passed": smoke["passed"], "verification_checks_passed": verification["passed"], "powerbi_csvs": len(files)}

if __name__ == "__main__":
    print(json.dumps(receipt(), indent=2))
