# Testing and verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q --junitxml=outputs/reports/pytest.xml
.\.venv\Scripts\python.exe -m src.cli verify
.\.venv\Scripts\python.exe scripts/check_rerun.py
```

Tests create isolated temporary roots and small generated datasets, never replacing the workspace database. The suite covers reproducible generation, changed seeds, source contracts, injected defect types, date span, corruption/scale validation, canonical repairs, every quality dimension, scores and pooling, profiles, SQLite constraints, exception reconciliation, KPI calculations, inventory snapshots, metadata/glossary/lineage coverage, Power BI exports, schema drift, pristine-data behavior, API reads/filters/mutations/errors, missing database handling, assistant responses, provider fallback and preservation of workflow state across reruns.

The `verify` command inspects the full-scale workspace snapshot. It independently recalculates scores from persisted checks, matches failed checks to exceptions, verifies count reconciliation, tests SQLite integrity/foreign keys, checks all blocking rules on curated records, reconciles sales and latest-stock KPIs, confirms metadata coverage/date span and inspects export row counts and keys. Detailed evidence is `outputs/reports/verification.json`.

`scripts/check_rerun.py` fingerprints source CSVs and database tables, regenerates with the saved seed/settings, runs the pipeline, and verifies both fingerprints are unchanged. It compares content and identities rather than nondeterministic execution timestamps. It writes `rerun_verification.json`. Stop the API before running it on Windows.

Start uvicorn, then run `scripts/smoke_api.py` in another terminal for real HTTP coverage. TestClient integration tests complement this live-server verification. HTTP evidence is saved in `api_smoke.json`; test evidence is JUnit XML. `scripts/build_receipt.py` consolidates actual evidence into `docs/BUILD_VERIFICATION.md`.

The actual passing count and verification date are recorded in BUILD_VERIFICATION.md. No test is a placeholder assertion. External LLM calls and actual Power BI Desktop rendering are outside the automated tests because no credentials/Desktop instance are required for this project.
