# Table grains and SQL model

|Table|Grain / primary key|Parent relationships|
|---|---|---|
|dim_customer|One fictional buyer / customer_id|Trusted MDM reference membership|
|dim_supplier|One fictional supplier / supplier_id|Trusted master membership|
|dim_facility|One plant / facility_id|Five trusted facilities|
|dim_product|One packaging SKU / product_id|supplier_id → dim_supplier|
|dim_material|One material / material_id|supplier_id → dim_supplier|
|dim_warehouse|One warehouse / warehouse_id|facility_id → dim_facility|
|fact_sales_order|One single-product order / order_id|customer, product, facility|
|fact_sales_order_line|One line / line_id, one line per order in this simulation|order and product; values must agree with header|
|fact_production|One completed production event / production_id|product, facility, material|
|fact_inventory|One inventory observation / inventory_id|product, facility, warehouse; warehouse must belong to facility|
|fact_shipment|One delivered shipment / shipment_id, one attempted source shipment per order|order and facility; shipping date/facility must agree with order|
|dq_run|One current snapshot / run_id|Input fingerprint and project weights|
|dq_rule|One validation definition / rule_id|Source, field, dimension, severity, phase, blocking behavior, parameters|
|dq_result|One summary per run/rule|Composite key (run_id, rule_id)|
|dq_check|One rule check per source occurrence|Composite key (run_id, rule_id, source_row)|
|dq_exception|One failed rule per occurrence / exception_id|run_id and rule_id; source_row disambiguates duplicated business keys|
|dq_score|One scope/group score|(scope, group_name); overall/source/table/facility/month/dimension|
|metadata_catalog|One core table field|(table_name, field_name)|
|business_glossary|One business term / term|Related field and formula|
|data_lineage|One transformation edge / lineage_id|Source, transformation, target, description|
|data_owner|One core table owner/steward / table_name|Synthetic business role, no real employee identity|
|profiling_result|One stage/table/column profile|Raw, cleaned, curated|
|kpi_daily, kpi_monthly|One event day/month|Inventory is an observation-period snapshot and is non-additive over time|
|facility_performance|One accepted facility|All-period event measures and latest known inventory|
|product_performance, category_performance|One accepted SKU/category|All-period event measures and latest known inventory|
|inventory_trend|One month/facility/product|Latest observation within month, summed across warehouses|
|executive_kpis|One current batch summary|All curated event data and last observed inventory|
|governance_coverage|One core input table|Contract-field documentation/ownership coverage|
|ref_uom, ref_product_category|One allowed reference value|EA/KG/L and five packaging families|

`database/schema.sql` is the actual executable SQLite schema, produced from these contracts. `database/seed.sql` contains unit reference examples; the pipeline loads the complete generated reference files. Foreign-key enforcement is enabled on builds and writes. SQL and database publication are implemented/tested with SQLite; no PostgreSQL deployment is claimed.

Headers carry quantity and unit price because this deliberately models single-product orders. Never sum header and line quantities together. Missing accepted lines are visible in quarantines; the header remains usable because its required measures are independently validated. Shipments inherit ordered products for analytics. Synthetic prices are INR; all transaction quantities are EA. Materials can use KG.

Daily and monthly event measures group by each domain's own event date. Delivery timeliness groups shipments by ship date. Global inventory uses latest available observation per facility/product/warehouse; observations can have different last dates. Monthly inventory uses latest observation **within** each month, with no carry-forward for combinations absent in that month. Treat it as reporting of observed stock, not a complete month-end ledger.
