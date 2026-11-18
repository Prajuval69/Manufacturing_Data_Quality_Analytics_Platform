"""Seeded synthetic sources with explicit, measurable defect injection."""
import json
import numpy as np
import pandas as pd
from src.config import Settings, TABLES, CATEGORIES

def generate(settings: Settings, scale: float = 1.0):
    if scale <= 0:
        raise ValueError("scale must be positive")
    settings.prepare()
    rng = np.random.default_rng(settings.seed)
    n = lambda size: max(10, int(size * scale))
    ids = lambda prefix, count: [f"{prefix}{i:05d}" for i in range(1, count + 1)]
    pick = lambda values, size: rng.choice(values, size).tolist()
    dates = lambda size: (pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 546, size), unit="D")).strftime("%Y-%m-%d").tolist()
    tables = {}
    tables["dim_customer"] = pd.DataFrame({"customer_id": ids("C", n(500)), "customer_name": [f"PACKRIGHT CUSTOMER {i:04d}" for i in range(n(500))], "country": pick(["IN", "US", "DE", "SG", "AE"], n(500))})
    tables["dim_supplier"] = pd.DataFrame({"supplier_id": ids("S", n(100)), "supplier_name": [f"SYNTHETIC SUPPLIER {i:04d}" for i in range(n(100))], "country": pick(["IN", "US", "DE"], n(100))})
    tables["dim_facility"] = pd.DataFrame({"facility_id": ["F001", "F002", "F003", "F004", "F005"], "facility_name": ["CHENNAI", "HYDERABAD", "PUNE", "MUMBAI", "BENGALURU"], "city": ["Chennai", "Hyderabad", "Pune", "Mumbai", "Bengaluru"]})
    tables["dim_product"] = pd.DataFrame({"product_id": ids("P", n(150)), "product_description": [f"PACKRIGHT CONTAINER {i:04d}" for i in range(n(150))], "category": [CATEGORIES[i % 5] for i in range(n(150))], "uom": "EA", "supplier_id": pick(tables["dim_supplier"].supplier_id, n(150))})
    tables["dim_material"] = pd.DataFrame({"material_id": ids("M", n(60)), "material_name": [f"SYNTHETIC MATERIAL {i:03d}" for i in range(n(60))], "supplier_id": pick(tables["dim_supplier"].supplier_id, n(60)), "uom": "KG"})
    tables["dim_warehouse"] = pd.DataFrame({"warehouse_id": [f"W{i:03d}" for i in range(1, 6)], "facility_id": tables["dim_facility"].facility_id, "warehouse_name": [f"{c} WAREHOUSE" for c in tables["dim_facility"].facility_name]})
    for name, frame in tables.items():
        frame.to_csv(settings.root / "data/reference" / f"{name}.csv", index=False)
    pd.DataFrame({"uom": ["EA", "KG", "L"], "description": ["Each", "Kilogram", "Litre"]}).to_csv(settings.root / "data/reference/uom.csv", index=False)
    pd.DataFrame({"category": CATEGORIES}).to_csv(settings.root / "data/reference/product_categories.csv", index=False)
    # The MDM feed is authoritative; ERP snapshots deliberately disagree with it.
    mdm = settings.root / "data/raw/master_data"
    mdm.mkdir(parents=True, exist_ok=True)
    for name in ["dim_customer", "dim_product"]:
        tables[name].to_csv(mdm / f"{name}_reference.csv", index=False)
    count = n(5000)
    orders = pd.DataFrame({"order_id": ids("O", count), "customer_id": pick(tables["dim_customer"].customer_id, count), "product_id": pick(tables["dim_product"].product_id, count), "facility_id": pick(tables["dim_facility"].facility_id, count), "order_date": dates(count), "quantity": rng.integers(20, 1001, count), "unit_price": rng.integers(50, 501, count), "uom": "EA"})
    tables["fact_sales_order"] = orders
    # One line per order is intentional: order header contains the single ordered product.
    tables["fact_sales_order_line"] = orders[["order_id", "product_id", "order_date", "quantity", "unit_price", "uom"]].assign(line_id=ids("OL", count))
    for name, size, key, prefix, date in [("fact_production", n(8000), "production_id", "PR", "production_date"), ("fact_inventory", n(5000), "inventory_id", "I", "stock_date")]:
        facility = pick(tables["dim_facility"].facility_id, size)
        frame = pd.DataFrame({key: ids(prefix, size), "product_id": pick(tables["dim_product"].product_id, size), "facility_id": facility, date: dates(size), "quantity": rng.integers(100, 4001, size), "uom": "EA"})
        if name == "fact_production":
            frame["material_id"] = pick(tables["dim_material"].material_id, size)
        else:
            frame["warehouse_id"] = ["W" + f[1:] for f in facility]
        tables[name] = frame
    shipped = pd.to_datetime(orders.order_date) + pd.to_timedelta(rng.integers(1, 4, count), unit="D")
    promised = shipped + pd.to_timedelta(5, unit="D")
    delivery = shipped + pd.to_timedelta(rng.integers(2, 10, count), unit="D")
    tables["fact_shipment"] = pd.DataFrame({"shipment_id": ids("SH", count), "order_id": orders.order_id, "facility_id": orders.facility_id, "carrier": pick(["SYNTHETIC EXPRESS", "PACKRIGHT FREIGHT", "DEMO LOGISTICS"], count), "ship_date": shipped.dt.strftime("%Y-%m-%d"), "promised_date": promised.dt.strftime("%Y-%m-%d"), "delivery_date": delivery.dt.strftime("%Y-%m-%d"), "quantity": orders.quantity})
    defects = []
    def inject(table, column, kind, value):
        frame = tables[table]
        count = max(1, int(len(frame) * settings.corruption_rate / 5)) if settings.corruption_rate else 0
        # Avoid turning a configured 3% rate into 40% corruption on five-row masters.
        if len(frame) < 20 and kind not in ["facility_alias"]:
            count = 0
        if not count:
            return
        indexes = rng.choice(frame.index, count, replace=False)
        frame[column] = frame[column].astype(object)
        for i in indexes:
            before = frame.at[i, column]
            after = value(before) if callable(value) else value
            frame.at[i, column] = after
            defects.append({"table_name": table, "source_row": int(i), "column_name": column, "defect_type": kind, "before": str(before), "after": str(after)})
    for table, frame in tables.items():
        for column in ["customer_id", "facility_id", "supplier_id", "category"]:
            if column in frame and column != TABLES[table][2]:
                inject(table, column, "missing", None)
        for column in ["customer_id", "product_id", "facility_id"]:
            if column in frame and column != TABLES[table][2]:
                inject(table, column, "orphan", "NONEXISTENT")
        if "uom" in frame:
            inject(table, "uom", "unit_alias", lambda x: "pcs" if x == "EA" else "kilograms")
            inject(table, "uom", "invalid_unit", "BANANAS")
        if "quantity" in frame:
            inject(table, "quantity", "negative_quantity", -25)
            inject(table, "quantity", "anomaly", 999999)
        date = TABLES[table][3]
        if date:
            inject(table, date, "impossible_date", "2025-02-30")
            inject(table, date, "missing_date", None)
            inject(table, date, "future_date", "2030-01-01")
        for col in ["customer_name", "product_description"]:
            if col in frame:
                inject(table, col, "formatting", lambda x: "  " + str(x).lower() + "   ")
                inject(table, col, "conflicting_description", "WRONG MASTER DESCRIPTION")
        if settings.corruption_rate:
            duplicate_count = max(1, int(len(frame) * settings.corruption_rate / 5))
            dup = frame.iloc[rng.choice(len(frame), duplicate_count, replace=False)].copy()
            for offset, (_, row) in enumerate(dup.iterrows()):
                defects.append({"table_name": table, "source_row": len(frame) + offset, "column_name": TABLES[table][2], "defect_type": "duplicate", "before": str(row[TABLES[table][2]]), "after": str(row[TABLES[table][2]])})
            tables[table] = pd.concat([frame, dup], ignore_index=True)
    inject("dim_facility", "facility_name", "facility_alias", lambda x: "CHN Plant" if x == "CHENNAI" else str(x).title() + " plant")
    inject("fact_shipment", "delivery_date", "impossible_duration", "2024-01-01")
    inject("fact_shipment", "delivery_date", "long_delay", "2026-07-20")
    counts = {}
    for name, frame in tables.items():
        source, filename, _, _, columns = TABLES[name]
        path = settings.root / "data/raw" / source
        path.mkdir(parents=True, exist_ok=True)
        frame[columns].to_csv(path / filename, index=False)
        counts[name] = len(frame)
    pd.DataFrame(defects, columns=["table_name", "source_row", "column_name", "defect_type", "before", "after"]).to_csv(settings.root / "outputs/reports/injected_defects.csv", index=False)
    manifest = {"company": "PackRight Manufacturing (fictional)", "seed": settings.seed, "corruption_rate": settings.corruption_rate, "scale": scale, "as_of": settings.as_of, "period": ["2025-01-01", "2026-06-30"], "raw_counts": counts, "defect_operations": len(defects)}
    (settings.root / "data/raw/manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
