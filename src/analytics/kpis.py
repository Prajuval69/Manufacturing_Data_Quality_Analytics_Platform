"""Inventory is a snapshot metric; sales/production/shipments are event metrics."""
import pandas as pd

def latest_inventory(inventory, by=None):
    if inventory.empty:
        return inventory.copy()
    keys = ["facility_id", "product_id", "warehouse_id"]
    if by:
        keys = [by] + keys
    return inventory.sort_values(["stock_date", "inventory_id"]).drop_duplicates(keys, keep="last")

def compute(curated, exceptions, results, score):
    orders, production, inventory, shipments = [curated[n].copy() for n in ["fact_sales_order", "fact_production", "fact_inventory", "fact_shipment"]]
    for df, col in [(orders, "order_date"), (production, "production_date"), (inventory, "stock_date"), (shipments, "ship_date")]:
        df["month"] = pd.to_datetime(df[col]).dt.strftime("%Y-%m")
        df["date"] = df[col]
    products = curated["dim_product"].set_index("product_id").category
    shipment_products = orders.set_index("order_id").product_id
    shipments["product_id"] = shipments.order_id.map(shipment_products)
    for df in [orders, production, inventory, shipments]:
        df["category"] = df.product_id.map(products)
    shipments["delay"] = (pd.to_datetime(shipments.delivery_date) - pd.to_datetime(shipments.promised_date)).dt.days
    shipments["late"] = shipments.delay.gt(0).astype(int)
    shipments["on_time"] = shipments.delay.le(0).astype(int)
    snapshot = latest_inventory(inventory)
    open_mask = exceptions.status.isin(["Open", "In Review"]) if not exceptions.empty else pd.Series(False, index=exceptions.index)
    summary = pd.DataFrame([{
        "total_orders": len(orders), "order_quantity": orders.quantity.sum(), "average_order_quantity": orders.quantity.mean() if len(orders) else 0,
        "sales_value": (orders.quantity * orders.unit_price).sum(), "production_quantity": production.quantity.sum(),
        "inventory_quantity": snapshot.quantity.sum(), "inventory_snapshot_date": inventory.stock_date.max() if len(inventory) else None,
        "shipments": len(shipments), "delivered_shipments": len(shipments), "on_time_delivery_rate": shipments.on_time.mean() if len(shipments) else 0,
        "average_delivery_delay": shipments.delay.clip(lower=0).mean() if len(shipments) else 0, "late_shipments": shipments.late.sum(),
        "order_fulfillment_rate": shipments.order_id.nunique() / len(orders) if len(orders) else 0,
        "dq_score": score, "failed_rules": sum(r["records_failed"] > 0 for r in results), "open_exceptions": int(open_mask.sum()),
        "critical_exceptions": int((open_mask & exceptions.severity.eq("Critical")).sum()) if not exceptions.empty else 0}])

    def grouped(group, inventory_frame):
        pieces = []
        if len(orders):
            pieces.append(orders.groupby(group).agg(total_orders=("order_id", "size"), order_quantity=("quantity", "sum")))
        if len(production):
            pieces.append(production.groupby(group).agg(production_quantity=("quantity", "sum")))
        if len(inventory_frame):
            pieces.append(inventory_frame.groupby(group).agg(inventory_quantity=("quantity", "sum")))
        if len(shipments):
            pieces.append(shipments.groupby(group).agg(shipments=("shipment_id", "size"), late_shipments=("late", "sum"), on_time_delivery_rate=("on_time", "mean")))
        columns = ["total_orders", "order_quantity", "production_quantity", "inventory_quantity", "shipments", "late_shipments", "on_time_delivery_rate"]
        if not pieces:
            return pd.DataFrame(columns=[group] + columns)
        frame = pd.concat(pieces, axis=1).reindex(columns=columns).fillna(0).reset_index()
        return frame
    monthly_snapshot = latest_inventory(inventory, "month")
    daily = grouped("date", latest_inventory(inventory, "date"))
    monthly = grouped("month", monthly_snapshot)
    facilities = curated["dim_facility"][["facility_id", "facility_name"]].merge(grouped("facility_id", snapshot), how="left", on="facility_id").fillna(0)
    product_perf = curated["dim_product"][["product_id", "category"]].merge(grouped("product_id", snapshot), how="left", on="product_id").fillna(0)
    inventory_trend = monthly_snapshot.groupby(["month", "facility_id", "product_id"]).agg(quantity=("quantity", "sum"), snapshot_date=("stock_date", "max")).reset_index()
    return {"executive_kpis": summary, "kpi_daily": daily, "kpi_monthly": monthly,
            "facility_performance": facilities, "product_performance": product_perf,
            "category_performance": grouped("category", snapshot), "inventory_trend": inventory_trend}
