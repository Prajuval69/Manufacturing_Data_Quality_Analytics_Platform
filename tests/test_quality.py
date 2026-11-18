import pandas as pd
import pytest
from src.config import Settings, WEIGHTS
from src.pipeline.standardization import normalize_text, standardize
from src.quality.engine import failure_mask, weighted_score
from src.profiling.engine import profile

def rule(kind, column="x", **parameters):
    return {"column_name": column, "validation_logic": kind, "parameters": parameters}

@pytest.mark.parametrize("kind,values,params,expected", [
    ("not_null", [None, "", "A"], {}, [True, True, False]),
    ("unique", ["A", "A", "B"], {}, [False, True, False]),
    ("pattern", ["C00001", "WRONG", None], {"pattern": "C[0-9]{5}"}, [False, True, False]),
    ("nonnegative", [-1, 0, 5], {}, [True, False, False]),
    ("upper_bound", [1, 100, 101], {"maximum": 100}, [False, False, True]),
    ("allowed", ["EA", "pcs", None], {"values": ["EA"]}, [False, True, False]),
    ("canonical_unit", ["EA", "pcs", "KG"], {}, [False, True, False]),
    ("date", ["2025-02-28", "2025-02-30", None], {}, [False, True, False]),
    ("not_future", ["2025-01-01", "2030-01-01", None], {}, [False, True, False]),
])
def test_rule_logic(kind, values, params, expected):
    frame = pd.DataFrame({"x": values})
    actual = failure_mask(rule(kind, **params), frame, {}, {}, "2026-07-31")
    assert actual.tolist() == expected

def test_referential_integrity():
    frame = pd.DataFrame({"customer_id": ["C00001", "UNKNOWN", None]})
    target = pd.DataFrame({"customer_id": ["C00001"]})
    result = failure_mask(rule("reference", "customer_id", target="dim_customer"), frame, {"dim_customer": target}, {}, "2026-07-31")
    assert result.tolist() == [False, True, False]

def test_date_order():
    frame = pd.DataFrame({"delivery_date": ["2025-01-01", "2025-01-03"], "ship_date": ["2025-01-02"] * 2})
    assert failure_mask(rule("date_order", "delivery_date", earlier="ship_date"), frame, {}, {}, "2026-07-31").tolist() == [True, False]

def test_consistency_canonical():
    frame = pd.DataFrame({"customer_id": ["C1", "C2"], "customer_name": ["wrong", "RIGHT"]})
    ref = {"dim_customer": pd.DataFrame({"customer_id": ["C1", "C2"], "customer_name": ["RIGHT", "RIGHT"]})}
    r = {**rule("canonical_label", "customer_name", key="customer_id"), "table_name": "dim_customer"}
    assert failure_mask(r, frame, {}, ref, "2026-07-31").tolist() == [True, False]

def test_unit_and_label_standardization():
    frame = pd.DataFrame({"product_id": [" p00001 "], "product_description": ["wrong"], "category": ["fiber packaging"], "uom": ["pcs"], "supplier_id": ["s00001"], "source_row": [0]})
    ref = {"dim_product": pd.DataFrame({"product_id": ["P00001"], "product_description": ["CANONICAL"]})}
    clean = standardize("dim_product", frame, ref)
    assert clean.iloc[0].uom == "EA" and clean.iloc[0].product_description == "CANONICAL"
    assert clean.iloc[0].product_id == "P00001"

def test_text_normalization():
    assert normalize_text(pd.Series(["  chennai   plant  ", ""])).iloc[0] == "CHENNAI PLANT"
    assert pd.isna(normalize_text(pd.Series([""])).iloc[0])

def test_weighted_score_known_case():
    checks = pd.DataFrame({"dimension": ["completeness", "completeness", "validity"], "passed": [1, 0, 1]})
    assert weighted_score(checks, WEIGHTS) == round(100 * (.30 * .5 + .25) / .55, 4)

def test_timeliness_anomaly_pooling():
    checks = pd.DataFrame({"dimension": ["timeliness", "anomaly", "anomaly"], "passed": [1, 0, 0]})
    assert weighted_score(checks, WEIGHTS) == 33.3333

def test_no_checks_is_unknown():
    assert weighted_score(pd.DataFrame(), WEIGHTS) is None

def test_invalid_weights():
    with pytest.raises(ValueError):
        Settings(weights={"completeness": .2})

def test_wrong_weight_keys_even_if_total_one():
    with pytest.raises(ValueError):
        Settings(weights={"something_else": 1.0})

def test_nonfinite_quantity_rejected():
    frame = pd.DataFrame({"x": [float("inf"), float("-inf"), 10]})
    assert failure_mask(rule("nonnegative"), frame, {}, {}, "2026-07-31").tolist() == [True, True, False]

def test_profile_statistics():
    frame = pd.DataFrame({"quantity": [10, 20, None], "key": ["a", "a", "b"]})
    result = profile("sample", frame).set_index("column_name")
    assert result.loc["quantity", "mean_value"] == 15
    assert result.loc["quantity", "median_value"] == 15
    assert result.loc["quantity", "null_count"] == 1
    assert result.loc["key", "duplicate_count"] == 1
