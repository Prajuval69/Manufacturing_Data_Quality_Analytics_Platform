# Build verification — actual execution receipt

Verified 2026-10-03 09:17:24 IST. All data is synthetic PackRight Manufacturing; no confidential Greif data.

Snapshot `e1f9eb9be6d0faec09d1`; seed 42; corruption budget 0.03; fixed validation as-of 2026-07-31. Generated business period: 2025-01-01–2026-06-30; shipment completions can extend beyond order dates.

- Raw business-source occurrences: **28,996** (includes controlled duplicate rows and order lines; excludes separate canonical reference copies).
- Curated records: **26,148**.
- Quarantined records: **2,848**.
- Active/executed rules: **159** across seven dimensions.
- Row-level rule checks: **588,018**.
- Exceptions / failed checks: **3,927**.
- Overall incoming DQ score: **99.3191/100**.
- Tests: **84 passed, 0 failed, 0 errors, 0 skipped**.
- Full-scale acceptance checks: **37 passed, 0 failed**.
- Live loopback HTTP checks: **20 passed, 0 failed**, at `http://127.0.0.1:8000`.
- Assistant smoke mode: **deterministic**.

## Record counts

|Table|Raw|Curated|Quarantined|
|---|---:|---:|---:|
|dim_supplier|101|100|1|
|dim_customer|503|500|3|
|dim_facility|6|5|1|
|dim_product|151|147|4|
|dim_material|61|58|3|
|dim_warehouse|6|5|1|
|fact_sales_order|5,030|4,599|431|
|fact_sales_order_line|5,030|4,377|653|
|fact_production|8,048|7,253|795|
|fact_inventory|5,030|4,690|340|
|fact_shipment|5,030|4,414|616|

## DQ evidence

Scores are weighted check pass rates; accepted-record percentages have a different denominator. All blocking rules were rerun against curated rows and passed. Anomaly flags remain for review.

|Dimension|Score|Checks|Failures|
|---|---:|---:|---:|
|anomaly|99.4066|33,198|197|
|completeness|99.7601|210,083|504|
|consistency|98.9568|62,406|651|
|referential_integrity|97.5758|75,490|1,830|
|timeliness|99.5553|38,228|170|
|uniqueness|99.3930|28,996|176|
|validity|99.7142|139,617|399|

Exception statuses: `{"Open": 3601, "Resolved": 326}`. Severity counts: `{"Critical": 1830, "High": 1298, "Low": 27, "Medium": 772}`. One failed rule on one occurrence creates one exception; exceptions can exceed defective-row counts.

## Governance and analytics

- `metadata_catalog`: 58 rows.
- `business_glossary`: 23 rows.
- `data_lineage`: 88 rows.
- `data_owner`: 11 rows.
- `kpi_daily`: 549 rows.
- `kpi_monthly`: 19 rows.
- `facility_performance`: 5 rows.
- `product_performance`: 147 rows.

Power BI outputs: **28 actual CSV files**, including executive KPIs, facility/product/category performance, inventory snapshots/trends, DQ scores/trends/exceptions/rules/results, anomaly flags, calendar/month dimensions, core facts/masters and governance coverage. Profiling and governance CSVs are separately populated. Read `outputs/reports/BATCH_READOUT.md` for measured business totals and caveats.

## API smoke results

|Method|Endpoint|HTTP|Pass|
|---|---|---:|---|
|GET|/health|200|True|
|GET|/openapi.json|200|True|
|GET|/api/kpis/summary|200|True|
|GET|/api/kpis/facilities|200|True|
|GET|/api/kpis/products|200|True|
|GET|/api/data-quality/summary|200|True|
|GET|/api/data-quality/rules|200|True|
|GET|/api/governance/metadata|200|True|
|GET|/api/governance/glossary|200|True|
|GET|/api/governance/lineage|200|True|
|GET|/api/profiling/fact_production|200|True|
|GET|/api/exceptions?status=Open&severity=High&limit=2|200|True|
|GET|/api/exceptions/12fd6e9a929328016059b2b1|200|True|
|PATCH|/api/exceptions/12fd6e9a929328016059b2b1|200|True|
|PATCH|/api/exceptions/12fd6e9a929328016059b2b1|200|True|
|GET|/api/exceptions/not-present|404|True|
|GET|/api/profiling/not-present|404|True|
|GET|/api/exceptions?limit=0|422|True|
|PATCH|/api/exceptions/12fd6e9a929328016059b2b1|422|True|
|POST|/api/assistant/ask|200|True|

## Reproducibility and hygiene

The full default dataset was regenerated and the pipeline rerun. Raw CSV hashes and measured database-table hashes matched exactly; row counts, keys, exceptions, scores and KPIs did not duplicate or drift. The integration test also verifies preserving an Accepted status and resolution note across reruns. Execution timestamps are intentionally excluded from content fingerprints.

Parsed 37 Python files; no hardcoded host paths or recognized embedded token patterns were found in source/generated outputs. `.env` is ignored and the example key is empty. No fake PBIX, temporary database-build files or missing required documentation. SQLite integrity and foreign-key checks passed; exports reconcile to database counts. `pip check` and source compilation were also run. There is no Git repository initialized in this workspace, so the receipt covers local source/output hygiene rather than a commit-history secret audit.

## Limitations

Power BI Desktop was not found; CSVs and a detailed implementation guide replace PBIX delivery. No external LLM credential was configured; deterministic behavior is tested and the optional provider interface is mock-tested, but no real paid provider request is claimed. This is a local single-writer batch snapshot with no authentication, historical-run warehouse, full workflow audit history or live freshness SLA. Stop the API before database rebuilds on Windows. Retained anomalies can inflate quantities, and inventory trends report observed balances rather than a full month-end stock ledger.

## Reproduce

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m src.cli all
.\.venv\Scripts\python.exe -m src.cli verify
.\.venv\Scripts\python.exe scripts/check_rerun.py
.\.venv\Scripts\python.exe -m pytest -q --junitxml=outputs/reports/pytest.xml
.\.venv\Scripts\python.exe -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000
# In a second terminal:
.\.venv\Scripts\python.exe scripts/smoke_api.py
.\.venv\Scripts\python.exe scripts/audit_project.py
.\.venv\Scripts\python.exe scripts/build_receipt.py
```

Evidence: pipeline_summary.json, verification.json, rerun_verification.json, api_smoke.json, hygiene_audit.json and pytest.xml in `outputs/reports/`.
