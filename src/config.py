"""Portable settings and dataset contracts, shared by every stage."""
from dataclasses import dataclass, field
from pathlib import Path
import os
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=False)
CATEGORIES = ["FIBER PACKAGING", "METAL CONTAINERS", "POLYMER PACKAGING",
              "INDUSTRIAL DRUMS", "INTERMEDIATE BULK CONTAINERS"]
UNITS = ["EA", "KG", "L"]
WEIGHTS = {"completeness": .30, "validity": .25, "consistency": .20,
           "uniqueness": .10, "referential_integrity": .10, "timeliness_anomaly": .05}
ENV_WEIGHTS = {"completeness": "COMPLETENESS", "validity": "VALIDITY",
               "consistency": "CONSISTENCY", "uniqueness": "UNIQUENESS",
               "referential_integrity": "REFERENTIAL", "timeliness_anomaly": "ANOMALY"}

# table: (source directory, filename, primary key, event date, columns)
TABLES = {
    "dim_customer": ("erp", "customers.csv", "customer_id", None,
                     ["customer_id", "customer_name", "country"]),
    "dim_product": ("erp", "products.csv", "product_id", None,
                    ["product_id", "product_description", "category", "uom", "supplier_id"]),
    "dim_facility": ("master_data", "facilities.csv", "facility_id", None,
                     ["facility_id", "facility_name", "city"]),
    "dim_supplier": ("master_data", "suppliers.csv", "supplier_id", None,
                     ["supplier_id", "supplier_name", "country"]),
    "dim_material": ("master_data", "materials.csv", "material_id", None,
                     ["material_id", "material_name", "supplier_id", "uom"]),
    "dim_warehouse": ("wms", "warehouses.csv", "warehouse_id", None,
                      ["warehouse_id", "facility_id", "warehouse_name"]),
    "fact_sales_order": ("erp", "sales_orders.csv", "order_id", "order_date",
                         ["order_id", "customer_id", "product_id", "facility_id", "order_date", "quantity", "unit_price", "uom"]),
    "fact_sales_order_line": ("erp", "order_lines.csv", "line_id", "order_date",
                              ["line_id", "order_id", "product_id", "order_date", "quantity", "unit_price", "uom"]),
    "fact_production": ("mes", "production.csv", "production_id", "production_date",
                        ["production_id", "product_id", "facility_id", "material_id", "production_date", "quantity", "uom"]),
    "fact_inventory": ("wms", "inventory.csv", "inventory_id", "stock_date",
                       ["inventory_id", "product_id", "facility_id", "warehouse_id", "stock_date", "quantity", "uom"]),
    "fact_shipment": ("logistics", "shipments.csv", "shipment_id", "ship_date",
                      ["shipment_id", "order_id", "facility_id", "carrier", "ship_date", "promised_date", "delivery_date", "quantity"]),
}
FOREIGN_KEYS = {
    "dim_product": {"supplier_id": "dim_supplier"},
    "dim_material": {"supplier_id": "dim_supplier"},
    "dim_warehouse": {"facility_id": "dim_facility"},
    "fact_sales_order": {"customer_id": "dim_customer", "product_id": "dim_product", "facility_id": "dim_facility"},
    "fact_sales_order_line": {"order_id": "fact_sales_order", "product_id": "dim_product"},
    "fact_production": {"product_id": "dim_product", "facility_id": "dim_facility", "material_id": "dim_material"},
    "fact_inventory": {"product_id": "dim_product", "facility_id": "dim_facility", "warehouse_id": "dim_warehouse"},
    "fact_shipment": {"order_id": "fact_sales_order", "facility_id": "dim_facility"},
}
LOAD_ORDER = ["dim_supplier", "dim_customer", "dim_facility", "dim_product", "dim_material",
              "dim_warehouse", "fact_sales_order", "fact_sales_order_line", "fact_production", "fact_inventory", "fact_shipment"]

@dataclass
class Settings:
    root: Path = field(default_factory=lambda: Path(os.getenv("PACKRIGHT_ROOT", str(PROJECT_ROOT))).resolve())
    seed: int = 42
    corruption_rate: float = .03
    as_of: str = "2026-07-31"
    weights: dict = field(default_factory=lambda: {
        k: float(os.getenv("DQ_" + ENV_WEIGHTS[k] + "_WEIGHT", str(v))) for k, v in WEIGHTS.items()})
    database_url: str | None = None

    def __post_init__(self):
        self.root = Path(self.root).resolve()
        if not 0 <= self.corruption_rate <= .25:
            raise ValueError("corruption_rate must be between 0 and 0.25")
        if set(self.weights) != set(WEIGHTS) or any(v < 0 for v in self.weights.values()) or abs(sum(self.weights.values()) - 1) > 1e-9:
            raise ValueError("DQ weights must be nonnegative and sum to 1")
        from datetime import date
        date.fromisoformat(self.as_of)

    @property
    def db_path(self):
        url = self.database_url or os.getenv("DATABASE_URL", "sqlite:///data/processed/packright.db")
        if not url.startswith("sqlite:///"):
            raise ValueError("This local implementation supports SQLite URLs only")
        path = Path(url.removeprefix("sqlite:///"))
        return path if path.is_absolute() else self.root / path

    def prepare(self):
        for p in ["data/raw", "data/reference", "data/staging", "data/processed/cleaned", "data/processed/curated",
                  "outputs/profiling", "outputs/powerbi", "outputs/governance", "outputs/reports", "logs", "config", "database", "docs"]:
            (self.root / p).mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
