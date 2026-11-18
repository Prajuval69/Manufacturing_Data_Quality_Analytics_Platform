"""Catalog every contracted field, with actual lineage and defined metrics."""
import pandas as pd
from src.config import TABLES, FOREIGN_KEYS

DEFINITIONS = {
    "quantity": "Number of units at this table's documented grain; interpret with uom.",
    "unit_price": "Synthetic INR price per ordered unit; sales value is quantity times unit price.",
    "category": "Packaging family from the controlled product-category reference.",
    "uom": "Standard unit: EA=each, KG=kilogram, L=litre.",
    "order_date": "Calendar day when the fictional order was placed.",
    "stock_date": "Inventory observation day; never sum balances across observation dates.",
    "production_date": "Calendar day of completed synthetic production.",
    "ship_date": "Day goods left the facility.",
    "promised_date": "Promised delivery deadline.",
    "delivery_date": "Actual synthetic delivery day.",
}
GLOSSARY = [
    ("Production Quantity", "Completed packaging units", "fact_production.quantity", "SUM(quantity) by date; EA only"),
    ("On-Time Delivery Rate", "Share of delivered shipments meeting promise", "fact_shipment.delivery_date", "COUNT(delivery_date <= promised_date) / COUNT(delivered shipments)"),
    ("Inventory Quantity", "Latest observed balance per facility/product/warehouse", "fact_inventory.quantity", "SUM(latest quantity per facility/product/warehouse); monthly latest within month"),
    ("Data Quality Score", "Project-specific weighted pass rate across rule checks", "dq_score.score", "100 * SUM(weight * dimension pass rate) / SUM(applicable weights)"),
    ("Customer", "Fictional packaging buyer identified by customer_id", "dim_customer.customer_id", ""),
    ("Product", "Packaging SKU with category, unit and supplier", "dim_product.product_id", ""),
    ("Facility", "PackRight production plant", "dim_facility.facility_id", ""),
    ("Sales Order", "One single-product order header", "fact_sales_order.order_id", "COUNT(order_id)"),
    ("Order Line", "Single product line linked to one order; one line per order in this simulation", "fact_sales_order_line.line_id", "Do not sum headers and lines together"),
    ("Shipment", "Delivery event linked to a curated order", "fact_shipment.shipment_id", "COUNT(shipment_id)"),
    ("Exception", "One failed rule on one source occurrence", "dq_exception.exception_id", "COUNT(exception_id); may exceed defective record count"),
    ("Completeness", "Required fields populated", "dq_rule.dimension", "Passed required-field checks / all required-field checks"),
    ("Validity", "Values meeting formats, domains and ranges", "dq_rule.dimension", "Passed validity checks / validity checks"),
    ("Consistency", "Agreement with canonical master and related fields", "dq_rule.dimension", "Passed consistency checks / consistency checks"),
    ("Uniqueness", "No repeated business key after first occurrence", "dq_rule.dimension", "Extra duplicate occurrences fail"),
    ("Referential Integrity", "Foreign keys resolve to accepted parents", "dq_rule.dimension", "Parent membership checks"),
    ("Data Lineage", "Trace from source through transformations to exports", "data_lineage.target", ""),
    ("Critical Data Element", "Identifier, required date, quantity or category influencing decisions", "metadata_catalog.critical_data_element", ""),
    ("Order Fulfillment Rate", "Curated orders with at least one delivered shipment", "executive_kpis.order_fulfillment_rate", "DISTINCT shipped order_id / COUNT(curated orders)"),
    ("Average Delivery Delay", "Nonnegative days beyond promise, across delivered shipments", "executive_kpis.average_delivery_delay", "AVG(MAX(delivery_date - promised_date, 0))"),
    ("Quarantine", "Source occurrence excluded for blocking rule failures", "dq_run.quarantined_records", "Raw count minus curated count"),
    ("Sales Value", "Ordered value in synthetic INR", "executive_kpis.sales_value", "SUM(quantity * unit_price)"),
    ("Timeliness", "Observation does not fall after fixed as-of date", "dq_rule.dimension", "Historical batch check, not live freshness SLA"),
]

def build(curated):
    metadata, owners, edges = [], [], []
    for table, (source, filename, key, date, columns) in TABLES.items():
        owner = source.upper() + " Business Owner"
        owners.append({"table_name": table, "owner": owner, "steward": source.upper() + " Data Steward", "responsibility": "Maintain definitions, review exceptions, approve source corrections"})
        for col in columns:
            description = DEFINITIONS.get(col, f"Unique identifier for {col.removesuffix('_id').replace('_', ' ')}; resolves to master or transaction parent." if col.endswith("_id") else f"Canonical {col.replace('_', ' ')} in the fictional PackRight dataset.")
            metadata.append({"table_name": table, "field_name": col, "business_name": col.replace("_", " ").title(), "description": description,
                             "data_type": "decimal" if col in ["quantity", "unit_price"] else "date" if col.endswith("_date") else "string",
                             "source_system": source.upper(), "sensitivity": "Synthetic - Public Demonstration", "owner": owner, "refresh_frequency": "On batch execution",
                             "critical_data_element": int(col.endswith("_id") or col.endswith("_date") or col in ["quantity", "category"])})
        path = [f"{source.upper()}.{filename}", f"stg_{table}", f"clean_{table}", table, "kpi_monthly" if table.startswith("fact_") else "facility_performance" if table == "dim_facility" else "metadata_catalog", "Power BI CSV"]
        transformations = ["Contract-checked CSV ingestion", "Normalize text/dates/units; repair canonical labels", "Validate, exclude blocking failures; retain flagged anomalies", "Aggregate trusted facts or document governed fields", "Export local reporting snapshot"]
        for i in range(len(path) - 1):
            edges.append({"lineage_id": f"{table}:{i}", "source": path[i], "transformation": transformations[i], "target": path[i+1], "description": f"{table}: {transformations[i]}"})
        edges.append({"lineage_id": f"{table}:exceptions", "source": f"clean_{table}", "transformation": "Persist one exception per failed rule and source occurrence", "target": "dq_exception", "description": "Incoming canonical/duplicate checks retain raw values; other checks use cleaned values"})
        if table.startswith("dim_"):
            edges.append({"lineage_id": f"{table}:reference", "source": f"reference.{table}", "transformation": "Canonical labels and identifier membership", "target": f"clean_{table}", "description": "Trusted synthetic master reference guides standardization and validation"})
        for col, parent in FOREIGN_KEYS.get(table, {}).items():
            edges.append({"lineage_id": f"{table}:fk:{col}", "source": parent, "transformation": f"Validate {col} against accepted parent identifiers", "target": table, "description": "Invalid parent rows cause dependent facts to be quarantined"})
    glossary = [{"term": t, "definition": d, "business_owner": "PackRight Analytics Owner", "related_field": f, "calculation": c} for t,d,f,c in GLOSSARY]
    coverage = []
    m = pd.DataFrame(metadata)
    for table, subset in m.groupby("table_name"):
        count = len(subset)
        critical = int(subset.critical_data_element.sum())
        coverage.append({"table_name": table, "fields": count, "documented_fields": count, "owned_fields": count, "critical_fields": critical,
                         "documented_critical_fields": critical, "lineage_edges": sum(e["lineage_id"].startswith(table + ":") for e in edges),
                         "glossary_terms": sum(g["related_field"].startswith(table + ".") for g in glossary), "metadata_coverage": 1., "ownership_coverage": 1., "critical_coverage": 1. if critical else 0.})
    return {"metadata_catalog": m, "data_owner": pd.DataFrame(owners), "business_glossary": pd.DataFrame(glossary), "data_lineage": pd.DataFrame(edges), "governance_coverage": pd.DataFrame(coverage)}
