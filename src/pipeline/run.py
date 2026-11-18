"""One local batch with observable stages and deterministic identities."""
import hashlib
import json
import logging
from datetime import datetime, timezone
import pandas as pd
from src.config import Settings, TABLES, LOAD_ORDER
from src.pipeline.ingestion import ingest, references
from src.pipeline.standardization import standardize
from src.profiling.engine import profile
from src.quality.rules import build_rules
from src.quality.engine import validate, CHECK_COLUMNS, score_breakdowns
from src.db.store import publish, previous_states
from src.governance.catalog import build
from src.analytics.kpis import compute
from src.reporting.export import export

def input_hash(settings, rules):
    h = hashlib.sha256()
    for folder in ["data/raw", "data/reference"]:
        for path in sorted((settings.root / folder).rglob("*.csv")):
            h.update(str(path.relative_to(settings.root)).encode())
            h.update(path.read_bytes())
    h.update(json.dumps({"rules": rules, "weights": settings.weights, "as_of": settings.as_of}, sort_keys=True).encode())
    # Changes in transformation/analytics code invalidate the snapshot identity.
    for path in sorted((__import__('pathlib').Path(__file__).resolve().parents[1]).rglob("*.py")):
        h.update(path.read_bytes())
    return h.hexdigest()

def run(settings: Settings | None = None):
    settings = settings or Settings()
    settings.prepare()
    logger = logging.getLogger("packright")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
    file_handler = logging.FileHandler(settings.root / "logs/pipeline.log", encoding="utf-8")
    logger.addHandler(file_handler)
    try:
        started = datetime.now(timezone.utc).isoformat()
        catalog_path = settings.root / "config/dq_rules.json"
        rules = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.exists() else build_rules()
        if len({r["rule_id"] for r in rules}) != len(rules):
            raise ValueError("Duplicate rule IDs")
        catalog_path.write_text(json.dumps(rules, indent=2), encoding="utf-8")
        digest = input_hash(settings, rules)
        run_id = digest[:20]
        states, prior = previous_states(settings.db_path)
        same_input = prior is not None and prior[0] == run_id
        logger.info("Ingestion: checking 11 source contracts")
        raw = ingest(settings)
        reference = references(settings)
        curated, profiles, all_results, all_exceptions, all_checks, counts = {}, [], [], [], [], {}
        logger.info("Profiling, canonical standardization, validation and quarantine")
        for table in LOAD_ORDER:
            frame = raw[table]
            clean = standardize(table, frame, reference)
            profiles.extend([profile(table, frame, "raw"), profile(table, clean, "cleaned")])
            results, exceptions, checks, rejected = validate(table, frame, clean, rules, curated, reference, settings, run_id)
            accepted = clean.loc[~rejected].copy()
            curated[table] = accepted
            clean.to_csv(settings.root / "data/processed/cleaned" / f"{table}.csv", index=False)
            accepted[TABLES[table][4]].to_csv(settings.root / "data/processed/curated" / f"{table}.csv", index=False)
            quarantine = clean.loc[rejected].copy()
            quarantine["failed_rule_ids"] = quarantine.source_row.map(lambda row: ";".join(e["rule_id"] for e in exceptions if e["source_row"] == row))
            quarantine.to_csv(settings.root / "data/processed" / f"quarantine_{table}.csv", index=False)
            profiles.append(profile(table, accepted, "curated"))
            all_results.extend(results)
            all_exceptions.extend(exceptions)
            all_checks.extend(checks)
            counts[table] = {"raw": len(frame), "curated": len(accepted), "quarantined": int(rejected.sum())}
            logger.info("%s raw=%d accepted=%d quarantined=%d", table, len(frame), len(accepted), rejected.sum())
        exception_columns = ["exception_id", "run_id", "rule_id", "source_system", "table_name", "record_key", "source_row", "column_name", "current_value", "expected_condition", "severity", "status", "detected_at", "assigned_to", "resolution_note", "resolved_at", "facility_id", "month"]
        exceptions = pd.DataFrame(all_exceptions, columns=exception_columns)
        if same_input:
            for i, e in exceptions.iterrows():
                if e.exception_id in states:
                    exceptions.loc[i, ["status", "assigned_to", "resolution_note", "resolved_at", "detected_at"]] = states[e.exception_id]
        checks = pd.DataFrame(all_checks, columns=CHECK_COLUMNS)
        scores = score_breakdowns(checks, settings.weights)
        score = float(scores.iloc[0].score)
        logger.info("Scoring: %.4f; exceptions: %d; checks: %d", score, len(exceptions), len(checks))
        logger.info("Building governance and analytics")
        governance = build(curated)
        analytics = compute(curated, exceptions, all_results, score)
        run_record = {"run_id": run_id, "started_at": prior[1] if same_input else started, "completed_at": datetime.now(timezone.utc).isoformat(),
                      "as_of": settings.as_of, "overall_score": score, "raw_records": sum(c["raw"] for c in counts.values()),
                      "curated_records": sum(c["curated"] for c in counts.values()), "quarantined_records": sum(c["quarantined"] for c in counts.values()),
                      "rule_count": sum(r["active"] for r in rules), "exception_count": len(exceptions), "weights_json": json.dumps(settings.weights), "input_hash": digest}
        logger.info("Publishing constrained database snapshot")
        publish(settings, curated, reference, run_record, rules, all_results, exceptions, checks, scores, pd.concat(profiles, ignore_index=True), governance, analytics)
        logger.info("Exporting Power BI, profiles, governance and reports")
        files = export(settings)
        summary = {**run_record, "counts": counts, "reporting_files": files, "exception_statuses": exceptions.status.value_counts().to_dict(), "dimension_scores": scores.loc[scores.scope.eq("dimension")].to_dict("records")}
        (settings.root / "outputs/reports/pipeline_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        logger.info("Pipeline complete")
        return summary
    finally:
        logger.removeHandler(file_handler)
        file_handler.close()

if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
