# Manufacturing Data Quality & Analytics Governance Platform

Working local portfolio platform for **PackRight Manufacturing**, a fictional packaging company. Every business record is generated synthetically. No confidential Greif data is used or represented.

Python/Pandas batches ingest ERP, MES, WMS, logistics and master data; profile, standardize and validate records; quarantine blocking failures; publish constrained SQLite tables; calculate KPIs; and export governance and Power BI datasets. FastAPI exposes the results and exception workflow. A structured-data assistant works without external credentials.

## Public project

- Repository: https://github.com/Prajuval69/Manufacturing_Data_Quality_Analytics_Platform
- Results site: https://prajuval69.github.io/Manufacturing_Data_Quality_Analytics_Platform/

GitHub Pages publishes the static synthetic-batch results page from docs/index.html on main. The Python pipeline, FastAPI endpoints and exception updates run locally using the commands below. No paid hosting or external credentials are required.

## Run on Windows PowerShell

Run from this repository directory. Python 3.11+ is required; the verified environment uses Python 3.12.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m src.cli all
.\.venv\Scripts\python.exe -m src.cli verify
.\.venv\Scripts\python.exe scripts/check_rerun.py
.\.venv\Scripts\python.exe -m pytest -q --junitxml=outputs/reports/pytest.xml
.\.venv\Scripts\python.exe -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000
```

In a second PowerShell terminal, run:

```powershell
.\.venv\Scripts\python.exe scripts/smoke_api.py
```

Open http://127.0.0.1:8000/docs for interactive API documentation. Stop the server with Ctrl+C before rebuilding the database on Windows. Database publication uses an atomic file replacement, which Windows blocks when another process has the file open.

On macOS/Linux, use `.venv/bin/python` instead of `.\.venv\Scripts\python.exe`. `requirements.txt` provides supported version ranges; `requirements-lock.txt` records the exact tested packages. No Docker, cloud, SQL server, Power BI Desktop, or LLM key is required.

## Actual results

See [docs/BUILD_VERIFICATION.md](docs/BUILD_VERIFICATION.md) for measured counts, scores, HTTP results, test results and full-scale rerun evidence. JSON/CSV/XML evidence is in `outputs/reports/`.

Verified default build: **28,996 raw records**, **26,148 curated**, **2,848 quarantined**, **159 rules**, **3,927 exceptions**, and **99.3191/100 DQ score**. **84 tests**, **37 acceptance checks** and **20 live HTTP checks** passed with zero failures. Full-scale regeneration and database fingerprints matched exactly. There are **28 populated Power BI CSVs**, **58 metadata fields**, **23 glossary terms** and **88 lineage edges**. These are measured synthetic-batch results, not real company performance.

The default seed is 42; corruption rate is 0.03; business dates span January 2025–June 2026 with some shipment completion dates in July. Validation uses the fixed as-of date **2026-07-31**, making future-date checks reproducible. Intentional corrupt dates can fall outside this period. The corruption rate is a per-operation budget: approximately rate/5 of rows for each applicable defect operation, with possible overlap. It is not the final defective-row percentage.

## Commands and configuration

```powershell
.\.venv\Scripts\python.exe -m src.cli generate --seed 42 --corruption-rate 0.03 --scale 1
.\.venv\Scripts\python.exe -m src.cli pipeline
.\.venv\Scripts\python.exe -m src.cli profile
.\.venv\Scripts\python.exe -m src.cli governance
.\.venv\Scripts\python.exe -m src.cli report
```

`all` regenerates synthetic inputs and runs every pipeline stage. `pipeline` processes current input CSVs. `profile` independently profiles current raw files and re-exports stored profiles; `governance` and `report` export the current database snapshot. Rebuild with `pipeline` after changing source files, rule definitions or governance code. `--root` supports isolated output folders; use `--scale 0.08` for a fast demonstration. Seed, scale and corruption settings affect `generate`/`all`. `--as-of` affects validation.

Copy `.env.example` to `.env` only when customizing settings. Relative database paths resolve under `PACKRIGHT_ROOT`; the default root is derived from source location. `config/dq_rules.json` is the editable, machine-readable rule catalog, initially generated from `src/quality/rules.py`. Existing catalogs are respected on reruns. Weights must have all six documented buckets, be nonnegative, and sum to one.

## Outputs

|Location|Contents|
|---|---|
|`data/raw/<source>/`|Unmodified synthetic sources, MDM snapshots and generation manifest|
|`data/reference/`|Trusted master keys, labels, units and packaging categories|
|`data/staging/`|Contract-checked ingestion with source-row occurrence IDs|
|`data/processed/cleaned/`|Standardized rows, including defects awaiting validation|
|`data/processed/curated/`|Accepted masters and facts|
|`data/processed/quarantine_*.csv`|Rejected rows and failed rule IDs|
|`data/processed/packright.db`|Masters, facts, DQ evidence, governance, profiling and analytics|
|`outputs/powerbi/`|Import-ready CSVs, dates, monthly keys, snapshots and anomaly flags|
|`outputs/governance/`|Metadata, glossary, lineage and ownership CSVs|
|`outputs/profiling/`|Raw/cleaned/curated column profiles|
|`outputs/reports/`|Pipeline results, readout, verification evidence, tests and HTTP smoke results|
|`logs/pipeline.log`|Stage-level execution logs|

## How to interpret results

DQ score is a weighted pass rate over rule checks. A high check score can coexist with a lower accepted-record rate because one blocking failure excludes an entire row and failures can cascade through references. Raw canonical/duplicate checks and cleaned domain/reference checks measure incoming batch assurance together. Resolved exception status does not rewrite source data or improve the measured score.

Blocking violations are quarantined, never replaced with invented quantities or identifiers. Canonical names and unit aliases are repaired from trusted synthetic references. Duplicate extra occurrences are excluded and marked resolved. Anomalies remain in curated data for review; they can inflate volume KPIs. `data_quality_flags.csv` exposes them for reporting filters. Inventory is the latest observed balance per facility/product/warehouse, not a sum across dates.

The database contains the latest complete snapshot, not a historical warehouse of executions. Reruns with the same inputs, code, rules, weights and as-of date have the same run identity and preserve exception statuses/notes. Changing any of these creates a new snapshot and resets source-specific workflow decisions. Do not run simultaneous pipeline writers. The unauthenticated API is intended for local portfolio use.

## Documentation

[Architecture](docs/ARCHITECTURE.md), [data model](docs/DATA_MODEL.md), [dictionary](docs/DATA_DICTIONARY.md), [rule catalog](docs/DATA_QUALITY_RULES.md), [scoring](docs/DQ_SCORING.md), [governance](docs/GOVERNANCE.md), [lineage](docs/LINEAGE.md), [Power BI guide](docs/POWER_BI_GUIDE.md), [API guide](docs/API_GUIDE.md), [assistant](docs/AI_ASSISTANT.md), [testing](docs/TESTING.md), [interview walkthrough](docs/PROJECT_WALKTHROUGH.md).

The original specification files remain at the repository root. Actual implementation documentation is in `docs/`. There is no fabricated `.pbix`, dashboard screenshot or live external LLM result.
