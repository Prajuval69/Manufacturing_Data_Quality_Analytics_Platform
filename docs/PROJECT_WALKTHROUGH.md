# Interview-friendly walkthrough

I built a local data platform for a fictional packaging manufacturer. Manufacturing data usually comes from different systems: ERP describes orders and customers, MES describes production, WMS describes stock, and logistics describes deliveries. I generated those sources with one seed so I could demonstrate realistic joins and reproducible defects without using confidential data.

The pipeline reads CSVs into staging, profiles fields, standardizes known aliases and master labels, evaluates rules, and separates accepted rows from quarantine. I chose Pandas because its transformations are visible and familiar, and SQLite because it runs locally while still enforcing keys and constraints. FastAPI makes the same stored results usable through an API. I avoided services that would add operational complexity without improving this portfolio demonstration.

A rule is a catalog entry with table, field, dimension, severity, logic and parameters. The engine produces a boolean failure mask. It summarizes checked/passed/failed counts, creates an exception for every failed occurrence, and stores row-level evidence. Duplicate source keys still have separate source-row identifiers. Accepted parent keys are checked before loading children, so broken master data cannot silently create orphans.

I repair only changes I can justify deterministically: trimming spaces, mapping units and looking up a canonical description from a known ID. I quarantine missing IDs, impossible dates, negative quantities and broken references. Large quantities are warnings that remain visible for a steward to investigate, because an unusually large order could be legitimate. Power BI can filter those rows using exported anomaly flags.

The DQ score is a weighted check pass rate. Completeness has 30%, validity 25%, consistency 20%, uniqueness 10%, referential integrity 10%, and combined timeliness/anomaly 5%. These are my project weights, not an industry standard. I show quarantined counts alongside the score so people do not confuse a high check score with the fraction of accepted records.

Metadata tells users what fields mean and who maintains them. The glossary defines terms such as on-time delivery and fulfillment with formulas. Lineage explains where a field or result came from: ERP to staging to cleaning to curated tables to reporting. Owner roles and sensitivity labels make the governance model understandable, while remaining fictional.

Analytics uses only accepted rows. Orders and production are additive events. Inventory is different: I select the latest observation per facility/product/warehouse, rather than adding balances from many days. I provide daily/monthly trends, facility and product/category comparisons, shipment delays, fulfillment and DQ breakdowns. I export clean CSVs, dimensions and a detailed Power BI model/measure guide because a real PBIX requires Power BI Desktop work.

The assistant first retrieves structured evidence through fixed tools. Without credentials it uses templates to explain failed rules, facility rankings, definitions and exceptions. An optional provider can phrase the same evidence, with a deterministic fallback if it fails. It cannot execute SQL from the question or change records. This demonstrates practical automation while keeping validation deterministic.

I tested generation, rules, transformations, scores, constraints, KPIs, API error handling, workflow updates and assistant behavior. I ran the full-scale pipeline and checked raw/accepted/quarantine reconciliation, join integrity, exception totals and CSVs. I regenerated the full dataset and compared database content fingerprints to prove there were no unintended duplicate records. I also fixed a Windows SQLite-connection cleanup problem discovered by the rerun test.

Limitations: one current batch snapshot, synthetic single-product orders, no live ingestion, no authentication, no full workflow audit history, no installed Power BI Desktop verification and no paid LLM invocation. Future improvements would add incremental ingestion and historical run comparisons, source corrections with audit trails, role-based access, real business contracts and a real Power BI dashboard. Each extension should solve a demonstrated need before adding infrastructure.

Use docs/BUILD_VERIFICATION.md and outputs/reports/BATCH_READOUT.md to discuss the actual counts and results instead of memorizing fabricated business claims.
