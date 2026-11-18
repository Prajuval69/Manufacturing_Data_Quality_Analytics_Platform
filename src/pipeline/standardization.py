"""Only deterministic repairs are made. Invalid facts remain invalid for quarantine."""
import pandas as pd
from src.config import TABLES

UNIT_ALIASES = {"PCS": "EA", "PIECES": "EA", "EACH": "EA", "KILOGRAMS": "KG", "KGS": "KG", "LITRES": "L"}
FACILITY_ALIASES = {"CHN PLANT": "CHENNAI", "CHENNAI PLANT": "CHENNAI", "HYDERABAD PLANT": "HYDERABAD", "PUNE PLANT": "PUNE", "MUMBAI PLANT": "MUMBAI", "BENGALURU PLANT": "BENGALURU"}

def normalize_text(series):
    return series.astype("string").str.strip().str.replace(r"\s+", " ", regex=True).str.upper().replace("", pd.NA)

def standardize(table, frame, reference):
    clean = frame.copy()
    for col in TABLES[table][4]:
        if col.endswith("_date"):
            clean[col] = pd.to_datetime(clean[col], errors="coerce", format="%Y-%m-%d").dt.strftime("%Y-%m-%d").astype("string")
        elif col in ["quantity", "unit_price"]:
            clean[col] = pd.to_numeric(clean[col], errors="coerce")
        else:
            clean[col] = normalize_text(clean[col])
    if "uom" in clean:
        clean["uom"] = clean.uom.replace(UNIT_ALIASES)
    if "facility_name" in clean:
        clean["facility_name"] = clean.facility_name.replace(FACILITY_ALIASES)
    # Trusted canonical labels can be repaired using an existing identifier.
    if table in reference:
        key = TABLES[table][2]
        for col in ["customer_name", "product_description", "facility_name", "supplier_name", "material_name", "warehouse_name"]:
            if col in clean:
                mapping = reference[table].set_index(key)[col]
                canonical = clean[key].map(mapping)
                clean[col] = canonical.fillna(clean[col])
    return clean
