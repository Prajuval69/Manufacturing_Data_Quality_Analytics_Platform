"""Declarative rules. The serialized catalog is evaluated by the generic engine."""
from src.config import TABLES, FOREIGN_KEYS, CATEGORIES, UNITS

def build_rules():
    rules = []
    def add(table, col, dimension, kind, severity="High", phase="cleaned", reject=True, **params):
        rule_id = f"{table}.{col}.{kind}"
        rules.append({"rule_id": rule_id, "rule_name": f"{col} {kind.replace('_', ' ')}", "description": f"{table}.{col}: {kind}; {params}",
                      "dimension": dimension, "severity": severity, "source_system": TABLES[table][0].upper(), "table_name": table,
                      "column_name": col, "validation_logic": kind, "phase": phase, "reject": reject, "active": True, "parameters": params})
    for table, (_, _, key, date, columns) in TABLES.items():
        for col in columns:
            add(table, col, "completeness", "not_null")
        add(table, key, "uniqueness", "unique", phase="raw")
        prefix = {"customer_id": "C", "product_id": "P", "facility_id": "F", "supplier_id": "S", "material_id": "M", "warehouse_id": "W", "order_id": "O", "line_id": "OL", "production_id": "PR", "inventory_id": "I", "shipment_id": "SH"}[key]
        add(table, key, "validity", "pattern", pattern=f"{prefix}[0-9]{{{'3' if key in ['facility_id','warehouse_id'] else '5'}}}")
        if table.startswith("dim_"):
            add(table, key, "referential_integrity", "reference", target=table, reference=True, severity="Critical")
        for col, target in FOREIGN_KEYS.get(table, {}).items():
            add(table, col, "referential_integrity", "reference", target=target, severity="Critical")
        for col in ["quantity", "unit_price"]:
            if col in columns:
                add(table, col, "validity", "nonnegative")
        if "quantity" in columns:
            limit = 10000 if table == "fact_inventory" else 8000 if table == "fact_production" else 5000
            add(table, "quantity", "anomaly", "upper_bound", severity="Medium", reject=False, maximum=limit)
        if "uom" in columns:
            add(table, "uom", "validity", "allowed", severity="Medium", values=UNITS)
            add(table, "uom", "consistency", "canonical_unit", severity="Medium", phase="raw", reject=False)
            if table.startswith("fact_") and "product_id" in columns:
                add(table, "uom", "consistency", "product_unit", severity="High")
        if "category" in columns:
            add(table, "category", "validity", "allowed", values=CATEGORIES)
        if "country" in columns:
            add(table, "country", "validity", "allowed", values=["IN", "US", "DE", "SG", "AE"])
        for col in columns:
            if col.endswith("_date"):
                add(table, col, "validity", "date")
                add(table, col, "timeliness", "not_future", severity="Medium", reject=True)
        for col in ["customer_name", "product_description", "facility_name", "supplier_name", "material_name", "warehouse_name"]:
            if col in columns:
                add(table, col, "consistency", "canonical_label", phase="raw", reject=False, severity="Medium", key=key)
        if table == "fact_inventory":
            add(table, "warehouse_id", "consistency", "warehouse_facility")
        if table == "fact_sales_order_line":
            add(table, "order_id", "consistency", "order_line")
        if table == "fact_shipment":
            add(table, "delivery_date", "validity", "date_order", earlier="ship_date")
            add(table, "promised_date", "validity", "date_order", earlier="ship_date")
            add(table, "ship_date", "consistency", "shipment_order")
            add(table, "delivery_date", "anomaly", "delivery_delay", severity="Low", reject=False, maximum=90)
    return rules
