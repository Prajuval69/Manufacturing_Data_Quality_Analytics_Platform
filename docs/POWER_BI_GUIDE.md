# Power BI implementation guide

This build supplies actual CSV datasets in `outputs/powerbi/`. Power BI Desktop was not found in the environment. No PBIX or dashboard rendering is claimed. This guide describes how to build the four requested report pages with the generated tables.

## Import and type setup

In Desktop, choose Get Data → Text/CSV, select each file and Transform Data. Use UTF-8 and comma delimiters. Set IDs and categorical fields to Text; event dates to Date; quantity/price/score to Decimal Number; counts/flags to Whole Number; rates to Decimal Number formatted as Percentage. `month` is Text in YYYY-MM form. Scores are already on 0–100 and should not be formatted as fractional percentages.

Recommended core imports:

- Dimensions: `dim_customer`, `dim_product`, `dim_facility`, `dim_supplier`, `dim_material`, `dim_warehouse`, `dim_date`, `dim_month`.
- Facts: `fact_sales_order`, `fact_sales_order_line`, `fact_production`, `fact_inventory`, `fact_shipment`.
- Reporting: `executive_kpis`, `facility_performance`, `product_performance`, `category_performance`, `kpi_daily`, `kpi_monthly`, `inventory_snapshot`, `inventory_trend`.
- DQ/governance: `dq_summary`, `dq_trend`, `dq_rule`, `dq_result`, `dq_exceptions`, `data_quality_flags`, `governance_coverage`. Metadata/glossary/lineage/owner CSVs can also be imported from `outputs/governance/`.

Keep preaggregated performance/KPI tables separate from fact-based measures. Do not add event fact totals to preaggregated totals. `executive_kpis` is a one-row all-batch receipt; its values do not respond to slicers unless replaced with fact-based measures. There is one sales line per order in this simulation; use headers for sales measures so values are not counted twice.

## Relationships

Use single-direction one-to-many filtering from dimensions to facts. Confirm unique dimension keys before enabling relationships.

|One side|Many side|Usage|
|---|---|---|
|dim_customer.customer_id|fact_sales_order.customer_id|Customer slice|
|dim_product.product_id|fact_sales_order / fact_sales_order_line / fact_production / fact_inventory / inventory_snapshot / inventory_trend .product_id|Product/category slice|
|dim_facility.facility_id|fact_sales_order / fact_production / fact_inventory / fact_shipment / inventory_snapshot / inventory_trend .facility_id|Plant slice|
|dim_supplier.supplier_id|dim_product.supplier_id|Supplier → SKU → facts|
|dim_material.material_id|fact_production.material_id|Material slice|
|dim_warehouse.warehouse_id|fact_inventory.warehouse_id and inventory_snapshot.warehouse_id|Warehouse slice|
|dim_date.date|fact_sales_order.order_date, fact_production.production_date, fact_inventory.stock_date, fact_shipment.ship_date|Active event-date relationships|
|dim_month.month|kpi_monthly.month and inventory_trend.month|Monthly aggregates|
|dq_rule.rule_id|dq_result.rule_id and dq_exceptions.rule_id|Rule dimension/severity context|

Avoid connecting dim_facility to dim_warehouse when both already filter fact_inventory, or dim_supplier to dim_material when it creates a second filter path into production. Likewise avoid an active order→shipment relationship if customer/product/facility dimension paths create ambiguity. Shipments can be enriched in Power Query by merging curated orders on the unique order_id to add product_id/customer_id; then use direct dimension relationships. The database/API already derive shipment products from accepted orders.

Mark dim_date as a date table. Delivery/promise date relationships to shipments can be inactive and activated with USERELATIONSHIP in dedicated measures, or implemented using separate role-playing date tables. For monthly-only charts, use dim_month; linking a repeated month column from dim_date as the one side is incorrect. Keep day and month slicers explicit about the tables they filter.

`dq_summary` mixes six scopes. Create separate Power Query references filtered to `scope=facility_id`, `source_system`, `table_name`, `dimension` or `month`, and rename group_name appropriately. The facility reference can relate to dim_facility, and the month reference to dim_month. Do not join the unfiltered mixed-scope table to every dimension. Leave UNKNOWN and UNASSIGNED buckets visible in separate DQ visuals.

`dq_exceptions` has one failed rule per source occurrence, so record_key is not unique. Use exception_id for exception counts. Facility/source/severity/status fields support queue visuals; do not create many-to-many fact joins on record_key. To add anomaly filtering to a fact, filter `data_quality_flags` to that fact's table_name in Power Query, merge on record_key → fact primary key, and fill missing has_anomaly/has_open_exception with 0. The flags are unique by table_name/record_key. Some repaired duplicate failures still share an accepted record key; has_anomaly specifically tracks outlier checks.

## DAX measures

```dax
Total Orders = COUNTROWS(fact_sales_order)
Order Quantity = SUM(fact_sales_order[quantity])
Average Order Quantity = DIVIDE([Order Quantity], [Total Orders])
Sales Value INR = SUMX(fact_sales_order,
    fact_sales_order[quantity] * fact_sales_order[unit_price])
Production Quantity = SUM(fact_production[quantity])
Current Observed Inventory = SUM(inventory_snapshot[quantity])
Shipments = COUNTROWS(fact_shipment)
Late Shipments = COUNTROWS(FILTER(fact_shipment,
    fact_shipment[delivery_date] > fact_shipment[promised_date]))
On Time Delivery Rate = DIVIDE([Shipments] - [Late Shipments], [Shipments])
Average Delivery Delay Days = AVERAGEX(fact_shipment,
    MAX(0, DATEDIFF(fact_shipment[promised_date],
        fact_shipment[delivery_date], DAY)))
Order Fulfillment Rate = DIVIDE(DISTINCTCOUNT(fact_shipment[order_id]),
    [Total Orders])
Overall DQ Score = CALCULATE(MAX(dq_summary[score]),
    dq_summary[scope] = "overall")
Failed Rules = COUNTROWS(FILTER(dq_result, dq_result[records_failed] > 0))
Open Exceptions = CALCULATE(COUNTROWS(dq_exceptions),
    dq_exceptions[status] IN {"Open", "In Review"})
Critical Open Exceptions = CALCULATE([Open Exceptions],
    dq_exceptions[severity] = "Critical")
Metadata Coverage = DIVIDE(SUM(governance_coverage[documented_fields]),
    SUM(governance_coverage[fields]))
Ownership Coverage = DIVIDE(SUM(governance_coverage[owned_fields]),
    SUM(governance_coverage[fields]))
Critical Field Coverage = DIVIDE(
    SUM(governance_coverage[documented_critical_fields]),
    SUM(governance_coverage[critical_fields]))
```

Fulfillment at full-batch scope matches the supplied KPI. For dated cohorts, filter both orders and shipments by the **order** cohort, rather than comparing ship-date rows to order-date rows. For a dynamic cohort measure, collect order_ids from filtered fact_sales_order with VALUES, use TREATAS on shipments.order_id and REMOVEFILTERS(dim_date) on shipment events; this counts shipments for the selected orders across their delivery dates. Customer/product shipment slicers require the enrichment described above.

Do not sum inventory observations over time. Use inventory_snapshot for the current last-known view, and inventory_trend with a **single selected month** for monthly observed balance. Monthly inventory does not carry forward missing combinations. Production/order/shipment quantities are additive; monthly on-time rates need shipment-count weighting. Never average facility rates or monthly DQ scores to manufacture an overall score: use the supplied overall score/check evidence. Retained anomaly rows can dominate quantity totals; show a warning and add an anomaly slicer after merging flags.

## Four report pages

|Page|Layout and visuals|Business question|
|---|---|---|
|Executive Overview|Top row: order count, sales INR, production, observed inventory, OTD, overall DQ. Middle: monthly sales/production trend and facility comparison. Bottom: category split, quarantine receipt, critical/open queue cards.|What is operating performance, and how much should users trust it?|
|Operations Analytics|Facility/category/date filters, production line chart, production by plant bar chart, inventory observed trend with month selection, sales by category, facility performance matrix, late-shipment table.|Where are volumes and delays concentrated?|
|Data Quality|Score by source/table/facility/dimension, event-month DQ trend, top failed-rule bars, severity/status breakdown, exception detail table with observed value, expected condition and assignee.|Which defects need attention, and which cohorts are affected?|
|Governance|Documentation/ownership/CDE coverage cards, coverage by table matrix, glossary definition table and lineage source/transformation/target table.|Are important fields understood, owned and traceable?|

Slicers: event date, observed month, facility, category, source system, severity, status and anomaly flag. Scope each slicer to relevant visuals with Edit Interactions. DQ results use incoming cohorts; operations use curated records. Explain these populations in a report note. Label all pages **Synthetic PackRight Manufacturing — portfolio demonstration**.

## Reconciliation and refresh

Match unsliced cards to `outputs/reports/kpi_summary.json`. Match imported fact/dimension row counts to BUILD_VERIFICATION.md and exception totals to dq_result failure totals. Inventory must match inventory_snapshot. See `BATCH_READOUT.md` for retained-anomaly caveats. Coverage percentages reflect generated core contracts, not independent compliance certification.

After source corrections, run the pipeline; after only exception workflow updates, run `python -m src.cli report`. Refresh Desktop imports from the same output folder. Relocating the repository requires updating the Power Query folder parameter. Save a real PBIX only after constructing and verifying the report in Desktop; CSV generation does not create one.
