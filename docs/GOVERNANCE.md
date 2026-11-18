# Governance implementation

Trusted synthetic references include customers, products, facilities, suppliers, materials, warehouses, units and packaging categories. ERP customer/product snapshots are independent feeds; canonical name disagreements are detected before repair. Known UOM and facility-name aliases are normalized. Missing/unrecognized identifiers are quarantined, not guessed.

The metadata catalog documents every contracted core input field: table, field, business name, description, type, source, sensitivity, owner, refresh frequency and critical-element flag. All fields are classified `Synthetic - Public Demonstration`. Coverage denominators are core source contract fields, **not every technical database column**. Owner/steward assignments are fictional business roles; they are a governance demonstration rather than verified organizational approvals.

The business glossary has definitions and formulas for operations, DQ dimensions, exceptions, lineage, critical elements and fulfillment. KPI definitions specify population and grain. Structured lineage records trace raw → staging → cleaned → curated → reporting, plus trusted references, foreign-key dependencies and exception generation. `docs/LINEAGE.md` is generated from the actual lineage records.

The exception queue includes a stable ID, run/rule, source/table, business key, source occurrence, field, observed value, expected condition, severity, status, UTC detection time, assignee, resolution note and resolved time. API filters support status, severity, source, table and facility, with pagination. States are Open, In Review, Resolved and Accepted. Terminal transitions require a nonblank note. Reopening clears resolved_at.

Canonical repairs and duplicate exclusions are automatically marked Resolved with explicit notes. Other failures are Open. Anomalies are retained for review. An exception resolution does not change the data; source fixes followed by a new pipeline run produce fresh evidence. The current workflow state is preserved across same-identity reruns; a different snapshot starts a new queue. Full status-transition audit history is a future extension.

Artifacts: `outputs/governance/{metadata_catalog,business_glossary,data_lineage,data_owner}.csv`, `outputs/powerbi/governance_coverage.csv`, and database governance tables. Rerun `pipeline` to rebuild definitions; `governance` re-exports the stored snapshot.
