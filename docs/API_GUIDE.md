# API guide

Start with `python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000` after a completed pipeline. Interactive OpenAPI documentation: http://127.0.0.1:8000/docs. This portfolio API has no authentication and should run locally. All business data is synthetic.

|Method|Path|Behavior|
|---|---|---|
|GET|/health|Verified snapshot identity, company and synthetic-only flag; 503 if unavailable|
|GET|/api/kpis/summary|Current business KPIs and actionable exception counts|
|GET|/api/kpis/facilities|Five accepted facility performance rows|
|GET|/api/kpis/products|Product metrics; limit 1–1000, offset ≥0|
|GET|/api/data-quality/summary|Run, grouped scores and exception status counts|
|GET|/api/data-quality/rules|Rule catalog; optional dimension filter|
|GET|/api/exceptions|Paginated queue, total and items|
|GET|/api/exceptions/{exception_id}|One exception; 404 if absent|
|PATCH|/api/exceptions/{exception_id}|Update status, assignee and/or note|
|GET|/api/governance/metadata|Field catalog, optional table_name filter|
|GET|/api/governance/glossary|Business terms and formulas|
|GET|/api/governance/lineage|Structured transformation edges|
|GET|/api/profiling/{table_name}|Column profiles, stage=raw/cleaned/curated; unknown table →404|
|POST|/api/assistant/ask|Structured evidence and deterministic/optional LLM answer|

Exception filters: `status`, `severity`, `source_system`, `table_name`, `facility_id`, `limit` (default 100, maximum 1000) and `offset`. Sources use uppercase ERP/MES/WMS/LOGISTICS/MASTER_DATA. Filters use exact values. Status/severity enums and pagination bounds have HTTP 422 validation errors.

Example PATCH body:

```json
{"status":"Resolved","assigned_to":"ERP Data Steward","resolution_note":"Corrected the synthetic source customer identifier and reviewed it"}
```

Statuses: Open, In Review, Resolved, Accepted. Resolved/Accepted requires a resolution_note in the same request. Empty, null or unexpected update fields are rejected. Updating status recalculates actionable KPI counts. Re-export CSVs with `python -m src.cli report` after workflow updates; exports are snapshots and do not update automatically.

Example assistant body:

```json
{"question":"Which rules are failing most often?","use_llm":false}
```

The response identifies mode, fallback_reason, answer, structured evidence and synthetic_only. Questions are bounded to 3–2000 characters. LLM use requires explicit `use_llm=true` and configured credentials; otherwise deterministic mode is returned. Pydantic models validate requests and the health response. FastAPI generates OpenAPI schemas for the complete API.

`scripts/smoke_api.py` tests real loopback HTTP, meaningful responses, filtering, GET/PATCH, invalid updates, 404/422 errors and the assistant. It temporarily changes one Open exception to In Review, then restores its original status. The actual verification receipt is in `outputs/reports/api_smoke.json`.
