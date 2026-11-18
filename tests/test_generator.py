import hashlib
import pandas as pd
import pytest
from src.config import Settings, TABLES
from src.data.generate import generate

def raw_hash(settings):
    return {str(p.relative_to(settings.root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (settings.root / "data/raw").rglob("*.csv")}

def test_seed_reproducibility(tmp_path):
    s = Settings(root=tmp_path)
    generate(s, .04)
    hashes = raw_hash(s)
    generate(s, .04)
    assert raw_hash(s) == hashes

def test_seed_changes_data(tmp_path):
    a = Settings(root=tmp_path / "a", seed=42)
    b = Settings(root=tmp_path / "b", seed=43)
    generate(a, .04)
    generate(b, .04)
    assert raw_hash(a) != raw_hash(b)

def test_source_contracts(built):
    root = built[0].root
    for table, (source, filename, key, date, columns) in TABLES.items():
        frame = pd.read_csv(root / "data/raw" / source / filename)
        assert list(frame.columns) == columns
        assert len(frame) > 0

def test_injected_categories(built):
    defects = pd.read_csv(built[0].root / "outputs/reports/injected_defects.csv")
    assert {"missing", "orphan", "duplicate", "anomaly", "negative_quantity", "impossible_date", "future_date", "unit_alias", "invalid_unit", "conflicting_description", "facility_alias", "long_delay"} <= set(defects.defect_type)
    for table, rows in defects.groupby("table_name"):
        source, file, *_ = TABLES[table]
        assert rows.source_row.max() < len(pd.read_csv(built[0].root / "data/raw" / source / file))

def test_clean_generation(tmp_path):
    s = Settings(root=tmp_path, corruption_rate=0)
    manifest = generate(s, .04)
    assert manifest["defect_operations"] == 0
    orders = pd.read_csv(s.root / "data/raw/erp/sales_orders.csv")
    assert orders.order_id.is_unique and orders.quantity.ge(0).all()

@pytest.mark.parametrize("rate", [-.01, .3])
def test_invalid_corruption_rate(rate):
    with pytest.raises(ValueError):
        Settings(corruption_rate=rate)

def test_invalid_scale(tmp_path):
    with pytest.raises(ValueError):
        generate(Settings(root=tmp_path), 0)

def test_date_span(built):
    frame = pd.read_csv(built[0].root / "data/raw/mes/production.csv")
    dates = pd.to_datetime(frame.production_date, errors="coerce")
    normal = dates[dates.between("2025-01-01", "2026-06-30")]
    assert (normal.max() - normal.min()).days >= 365
