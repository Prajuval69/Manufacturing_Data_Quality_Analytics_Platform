# MASTER PROMPT — Manufacturing Data Quality & Analytics Governance Platform

## Role

Act as a senior data engineer, analytics engineer, data quality engineer, BI developer, and pragmatic software architect. Build this project completely from start to finish in the current workspace.

Project name:

**Manufacturing Data Quality & Analytics Governance Platform**

The project is a portfolio-grade simulation of a manufacturing/packaging company's data platform. It must demonstrate the capabilities expected from a Data Analytics Intern working across data engineering, analytics, master data governance, data quality, metadata/lineage, AI/GenAI, and process automation.

Do not merely create a prototype with placeholder files. Implement the working system, generate realistic synthetic data, run the pipeline, execute tests, verify outputs, fix failures, and leave the repository clean and documented.

---

# 1. Core objective

Build an end-to-end platform that:

1. Generates realistic synthetic manufacturing/packaging business data.
2. Ingests data from multiple simulated source systems.
3. Profiles incoming datasets.
4. Cleans and standardizes data.
5. Runs deterministic data-quality validation.
6. Creates an exception-management queue.
7. Maintains master/reference data.
8. Produces metadata, a business glossary, and source-to-output lineage.
9. Loads analytics-ready tables into a relational database.
10. Exposes useful APIs for data-quality and analytics information.
11. Produces reporting-ready outputs for Power BI.
12. Provides a GenAI-style Data Quality Assistant with a safe deterministic fallback.
13. Runs automated tests.
14. Generates documentation and sample reports.
15. Provides reproducible commands for rebuilding everything.

The implementation must work locally without requiring paid cloud infrastructure.

---

# 2. Important constraints

- Use synthetic data only.
- Do not claim the synthetic data represents actual Greif data.
- Do not scrape Greif or use confidential/company data.
- Do not hardcode fake business results as if they were real.
- Prefer Python, Pandas, SQL, SQLite/PostgreSQL-compatible SQL, FastAPI, and Power BI-compatible CSV/Excel outputs.
- The project must run without mandatory cloud credentials.
- GenAI integration must be optional. The core application must still work when no LLM/API key is configured.
- Never expose API keys or secrets in source control.
- Use `.env.example`.
- Keep the architecture understandable enough for a fresher to explain in an interview.
- Avoid unnecessary enterprise technologies merely for keywords.
- Do not create fake screenshots or pretend a `.pbix` file was generated if Power BI Desktop is unavailable.
- Generate clean CSV/Excel outputs and a Power BI implementation guide instead.

---

# 3. Business scenario

Create a fictional global packaging manufacturer called:

**PackRight Manufacturing**

This is a fictional company used only for the portfolio project.

The company has:

- Manufacturing plants
- Customers
- Products
- Suppliers
- Sales orders
- Production orders
- Inventory
- Shipments
- Materials

Suggested facilities:

- Chennai Plant
- Hyderabad Plant
- Pune Plant
- Mumbai Plant
- Bengaluru Plant

Suggested product families:

- Fiber Packaging
- Metal Containers
- Polymer Packaging
- Industrial Drums
- Intermediate Bulk Containers

Create realistic relationships between these entities.

---

# 4. Source systems

Simulate multiple source systems.

At minimum:

## ERP
Contains:
- sales orders
- customers
- products
- order lines

## MES
Contains:
- production orders
- production quantities
- production dates
- facility IDs
- product IDs

## WMS
Contains:
- inventory
- warehouse
- product
- quantity
- stock date

## Logistics
Contains:
- shipments
- carrier
- shipment date
- promised date
- delivery date
- order ID

## Master Data
Contains:
- customer master
- product master
- facility master
- supplier master

Store raw data under:

`data/raw/<source_system>/`

---

# 5. Data generation

Create a reproducible synthetic data generator.

Use a fixed random seed.

Generate enough data to make analytics meaningful.

Suggested scale:

- Customers: 500+
- Products: 150+
- Facilities: 5
- Suppliers: 100+
- Sales orders: 5,000+
- Production records: 8,000+
- Inventory records: 5,000+
- Shipments: 5,000+

The exact scale may be adjusted for local performance.

Include at least 12 months of transaction dates.

Generate both valid records and intentionally corrupted records.

---

# 6. Inject realistic data-quality problems

The synthetic generator must deliberately inject controlled defects.

At minimum:

## Completeness
- missing customer IDs
- missing product classifications
- missing facility IDs
- missing dates
- missing supplier IDs

## Validity
- invalid product codes
- invalid facility codes
- invalid units of measure
- impossible dates
- negative quantities where not permitted

## Consistency
- inconsistent customer names
- inconsistent product descriptions
- inconsistent facility names
- inconsistent units

## Uniqueness
- duplicate customers
- duplicate products
- duplicate transactions

## Referential integrity
- transactions referencing nonexistent customers
- transactions referencing nonexistent products
- transactions referencing nonexistent facilities

## Range/anomaly checks
- unusually high production quantity
- unusually high inventory
- impossible delivery duration
- abnormal order quantity

The corruption rate must be configurable.

---

# 7. Data pipeline

Implement a clear pipeline:

raw → staging → cleaned → curated → analytics

Suggested modules:

1. ingestion
2. profiling
3. standardization
4. validation
5. exception creation
6. curated loading
7. KPI calculation
8. reporting export

Each stage must have logging.

The pipeline should be idempotent where practical.

Running it twice should not randomly duplicate records.

---

# 8. Database

Use SQLite by default.

Structure the database into logical tables.

Minimum tables:

## Master
- dim_customer
- dim_product
- dim_facility
- dim_supplier

## Transactions
- fact_sales_order
- fact_production
- fact_inventory
- fact_shipment

## Data Quality
- dq_rule
- dq_result
- dq_exception
- dq_run

## Governance
- metadata_catalog
- business_glossary
- data_lineage
- data_owner

## Analytics
- kpi_daily
- kpi_monthly
- facility_performance
- product_performance

Use primary keys, foreign keys where appropriate, indexes, and sensible constraints.

---

# 9. Data-quality framework

Build a reusable validation engine.

Each rule should have:

- rule_id
- rule_name
- description
- dimension
- severity
- source/table
- column
- validation logic
- active flag

Dimensions:

- completeness
- validity
- consistency
- uniqueness
- referential_integrity
- timeliness
- anomaly

Severity:

- Critical
- High
- Medium
- Low

The engine should output:

- records checked
- records passed
- records failed
- pass rate
- failure rate
- affected records
- severity
- execution timestamp

---

# 10. Data-quality score

Create a transparent portfolio scoring model.

Use:

- Completeness: 30%
- Validity: 25%
- Consistency: 20%
- Uniqueness: 10%
- Referential integrity: 10%
- Timeliness/anomaly: 5%

Clearly document that these weights are a project-specific scoring model, not an industry standard.

Calculate:

- overall data-quality score
- score by source
- score by table
- score by facility
- score by month
- score by dimension

Do not hide the calculation.

---

# 11. Exception management

Every failed validation should be traceable.

Create an exception table containing:

- exception_id
- run_id
- rule_id
- source_system
- table_name
- record_key
- column_name
- current_value
- expected_condition
- severity
- status
- detected_at
- assigned_to
- resolution_note
- resolved_at

Statuses:

- Open
- In Review
- Resolved
- Accepted

Implement APIs to:

- list exceptions
- filter exceptions
- get an exception
- update exception status
- add resolution notes

Do not implement authentication unless necessary; this is a portfolio project.

---

# 12. Master data management

Create reference/master data for:

- customers
- products
- facilities
- suppliers
- units of measure
- product categories

Implement standardization logic.

Examples:

`Chennai Plant`, `CHN Plant`, `Chennai plant` → `CHENNAI`

Normalize:

- casing
- whitespace
- known aliases
- units
- categorical values

Create master-data validation checks.

---

# 13. Profiling

Create a generic profiler capable of reporting:

- row count
- column count
- data type
- null count
- null percentage
- unique count
- duplicate count
- min
- max
- mean
- median where applicable
- sample values

Export profiling results to CSV/Excel.

---

# 14. Metadata catalog

Create metadata for important fields.

For every important field capture:

- field name
- table
- business name
- description
- data type
- source system
- sensitivity classification
- owner
- refresh frequency
- critical data element flag

Example:

`customer_id`

Business name:
Customer Identifier

Description:
Unique identifier assigned to a customer in the master-data system.

Critical data element:
Yes

---

# 15. Business glossary

Create at least 15 glossary terms.

Examples:

- Production Quantity
- On-Time Delivery Rate
- Inventory Quantity
- Data Quality Score
- Customer
- Product
- Facility
- Sales Order
- Shipment
- Exception
- Completeness
- Validity
- Data Lineage
- Critical Data Element
- Order Fulfillment Rate

Each term should have:

- term
- definition
- business owner
- related table/field
- calculation where applicable

---

# 16. Data lineage

Create a simple lineage model.

Example:

`ERP.sales_orders`
→ `stg_sales_order`
→ `clean_sales_order`
→ `fact_sales_order`
→ `kpi_monthly`
→ `Power BI`

Represent lineage as structured records.

Include:

- source
- transformation
- target
- transformation description

Create a human-readable lineage document.

---

# 17. Analytics

Calculate useful business KPIs.

At minimum:

## Sales
- total orders
- order quantity
- average order quantity
- orders by facility
- orders by product category

## Production
- production quantity
- production trend
- production by facility
- production by product

## Inventory
- total inventory
- inventory by facility
- inventory by product category
- inventory trend

## Logistics
- shipments
- on-time delivery rate
- average delivery delay
- late shipments

## Data quality
- overall DQ score
- failed rules
- open exceptions
- critical exceptions
- score by source
- score by facility

---

# 18. Power BI preparation

Do not attempt to manufacture a fake `.pbix` file.

Generate:

`outputs/powerbi/`

with clean reporting tables such as:

- executive_kpis.csv
- facility_performance.csv
- product_performance.csv
- dq_summary.csv
- dq_exceptions.csv
- dq_trend.csv
- governance_coverage.csv

Create:

`docs/POWER_BI_GUIDE.md`

The guide must specify:

- which tables to import
- relationships
- recommended measures
- recommended visuals
- filters/slicers
- page layout
- business questions answered

Dashboard pages:

1. Executive Overview
2. Operations Analytics
3. Data Quality
4. Governance

---

# 19. FastAPI

Build a REST API.

Minimum endpoints:

GET `/health`

GET `/api/kpis/summary`

GET `/api/kpis/facilities`

GET `/api/kpis/products`

GET `/api/data-quality/summary`

GET `/api/data-quality/rules`

GET `/api/exceptions`

GET `/api/exceptions/{exception_id}`

PATCH `/api/exceptions/{exception_id}`

GET `/api/governance/metadata`

GET `/api/governance/glossary`

GET `/api/governance/lineage`

GET `/api/profiling/{table_name}`

Use Pydantic models.

Add useful validation and error responses.

---

# 20. GenAI Data Quality Assistant

Create a module that can answer questions from structured project data.

Example questions:

- Why did data quality decrease this month?
- What are the most common data-quality issues?
- Which facility has the most exceptions?
- Which rules are failing most often?
- What should the data team investigate first?
- Explain this exception.
- What does this KPI mean?

Architecture:

User question
→ retrieve relevant structured data
→ generate context
→ optional LLM
→ answer

The assistant must have a deterministic fallback when no API key exists.

For the fallback, use rule-based/template responses.

If an LLM provider is implemented, isolate it behind a service interface.

Never require an API key for the main project to run.

---

# 21. Optional AI agent behavior

If practical, implement a simple tool-based agent that can call:

- get_dq_summary()
- get_top_failed_rules()
- get_facility_exceptions()
- get_kpi_summary()
- explain_rule()

Do not build an unnecessarily complicated autonomous agent.

The point is to demonstrate safe business-process automation.

---

# 22. Testing

Create a proper test suite.

Test:

- data generation
- transformation
- standardization
- each validation category
- DQ scoring
- exception creation
- KPI calculations
- API endpoints
- database loading
- GenAI fallback
- idempotent pipeline behavior

Include unit and integration tests.

Target at least 25 meaningful tests.

Do not create fake tests that only assert `True`.

---

# 23. CLI

Create a simple CLI or Python entry points.

Suggested commands:

`python -m src.pipeline.run`

`python -m src.data.generate`

`python -m src.profiling.run`

`python -m src.reporting.export`

`python -m src.governance.build_catalog`

If a unified CLI is cleaner, support:

`python -m src.cli generate`

`python -m src.cli pipeline`

`python -m src.cli profile`

`python -m src.cli report`

`python -m src.cli all`

---

# 24. Configuration

Use:

`.env.example`

Possible variables:

DATABASE_URL=sqlite:///data/processed/packright.db

LLM_PROVIDER=

LLM_API_KEY=

LLM_MODEL=

DQ_COMPLETENESS_WEIGHT=0.30

DQ_VALIDITY_WEIGHT=0.25

DQ_CONSISTENCY_WEIGHT=0.20

DQ_UNIQUENESS_WEIGHT=0.10

DQ_REFERENTIAL_WEIGHT=0.10

DQ_ANOMALY_WEIGHT=0.05

Do not commit `.env`.

---

# 25. Project structure

Create a clean structure similar to:

project/
├── README.md
├── MASTER_PROMPT.md
├── requirements.txt
├── pyproject.toml
├── .env.example
├── .gitignore
├── Makefile
├── config/
├── data/
│   ├── raw/
│   ├── staging/
│   ├── processed/
│   └── reference/
├── database/
│   ├── schema.sql
│   └── seed.sql
├── src/
│   ├── api/
│   ├── data/
│   ├── pipeline/
│   ├── quality/
│   ├── governance/
│   ├── analytics/
│   ├── ai/
│   ├── profiling/
│   ├── reporting/
│   ├── db/
│   └── utils/
├── tests/
├── outputs/
│   ├── reports/
│   ├── powerbi/
│   └── profiling/
├── docs/
└── logs/

Adjust the structure if there is a materially better design, but preserve separation of concerns.

---

# 26. Documentation

Create:

README.md
ARCHITECTURE.md
DATA_DICTIONARY.md
DATA_QUALITY_RULES.md
GOVERNANCE.md
LINEAGE.md
POWER_BI_GUIDE.md
API_GUIDE.md
AI_ASSISTANT.md
TESTING.md
PROJECT_WALKTHROUGH.md

The PROJECT_WALKTHROUGH must explain the project in interview-friendly language.

Include:

- problem
- business scenario
- architecture
- pipeline
- data-quality engine
- governance
- analytics
- GenAI
- testing
- limitations
- future improvements

---

# 27. Interview realism

The final implementation must be explainable by a fresher.

Avoid unnecessary complexity.

The developer should be able to explain:

1. Why multiple source systems were simulated.
2. Why data quality was important.
3. How validation rules work.
4. How exceptions are generated.
5. How DQ scores are calculated.
6. What metadata means.
7. What lineage means.
8. How Power BI consumes the output.
9. Why GenAI is optional.
10. How the pipeline can be automated.

---

# 28. Execution requirements

After implementation:

1. Install dependencies if possible.
2. Generate synthetic data.
3. Run the full pipeline.
4. Build the database.
5. Run profiling.
6. Run data-quality validation.
7. Generate exceptions.
8. Build governance outputs.
9. Generate analytics outputs.
10. Generate Power BI-ready outputs.
11. Run all tests.
12. Start the API and smoke-test endpoints if feasible.
13. Fix all failures.
14. Verify generated files.
15. Remove unnecessary temporary artifacts.
16. Update README with exact commands.
17. Record final test count and pipeline results in `docs/BUILD_VERIFICATION.md`.

Do not stop after writing code. The final repository must contain actual generated outputs.

---

# 29. Acceptance criteria

The project is complete only if:

- [ ] Synthetic data is generated reproducibly.
- [ ] Multiple source systems exist.
- [ ] ETL pipeline executes successfully.
- [ ] Data-quality rules execute successfully.
- [ ] Defects are detected.
- [ ] Exceptions are persisted.
- [ ] DQ scores are calculated.
- [ ] Master/reference data is implemented.
- [ ] Metadata catalog exists.
- [ ] Business glossary exists.
- [ ] Lineage exists.
- [ ] KPI tables exist.
- [ ] Power BI-ready files exist.
- [ ] FastAPI runs.
- [ ] API endpoints return meaningful data.
- [ ] GenAI fallback works without credentials.
- [ ] At least 25 meaningful tests pass.
- [ ] Documentation is complete.
- [ ] No secrets are committed.
- [ ] No fake claims about real company data are made.
- [ ] Full pipeline can be reproduced from documented commands.

---

# 30. Final response to the user

After completing the project, provide a concise final report containing:

- What was built
- Architecture
- Main technologies
- Number of generated records
- Number of validation rules
- Number of exceptions
- Overall DQ score
- Number of tests passed
- API status
- Generated output locations
- Known limitations
- Exact commands to run it again

Do not claim success unless you actually ran and verified it.
