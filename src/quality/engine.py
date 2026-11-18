"""Row-level validation evidence, stable exceptions, and weighted check scoring."""
import hashlib
import json
from datetime import datetime, timezone
import pandas as pd
from src.config import TABLES

def failure_mask(rule, frame, curated, reference, as_of):
    col, kind, p = rule["column_name"], rule["validation_logic"], rule["parameters"]
    s = frame[col]
    present = s.notna() & s.astype("string").str.strip().ne("")
    empty = pd.Series(False, index=frame.index)
    if kind == "not_null":
        bad = ~present
    elif kind == "unique":
        bad = s.duplicated(keep="first") & present
    elif kind == "pattern":
        bad = present & ~s.astype("string").str.fullmatch(p["pattern"], na=False)
    elif kind == "reference":
        target = (reference if p.get("reference") else curated).get(p["target"])
        valid = [] if target is None else target[TABLES[p["target"]][2]]
        bad = present & ~s.isin(valid)
    elif kind == "nonnegative":
        numeric = pd.to_numeric(s, errors="coerce")
        bad = present & (numeric.isna() | numeric.lt(0) | ~numeric.map(lambda v: pd.isna(v) or abs(v) != float("inf")))
    elif kind == "upper_bound":
        bad = pd.to_numeric(s, errors="coerce").gt(p["maximum"])
    elif kind == "allowed":
        bad = present & ~s.isin(p["values"])
    elif kind == "canonical_unit":
        bad = present & ~s.isin(["EA", "KG", "L"])
    elif kind == "canonical_label":
        target = reference[rule["table_name"]].set_index(p["key"])[col]
        expected = frame[p["key"]].map(target)
        bad = present & expected.notna() & s.ne(expected)
    elif kind in ["date", "not_future"]:
        date = pd.to_datetime(s, errors="coerce", format="%Y-%m-%d")
        bad = present & (date.isna() if kind == "date" else date.gt(pd.Timestamp(as_of)))
    elif kind in ["date_order", "delivery_delay"]:
        date = pd.to_datetime(s, errors="coerce")
        earlier = pd.to_datetime(frame[p.get("earlier", "promised_date")], errors="coerce")
        days = (date - earlier).dt.days
        bad = days.lt(0) if kind == "date_order" else days.gt(p["maximum"])
    elif kind == "product_unit":
        target = curated.get("dim_product", reference["dim_product"]).set_index("product_id").uom
        expected = frame.product_id.map(target)
        bad = present & expected.notna() & s.ne(expected)
    elif kind == "warehouse_facility":
        target = curated.get("dim_warehouse", reference["dim_warehouse"]).set_index("warehouse_id").facility_id
        expected = frame.warehouse_id.map(target)
        bad = expected.notna() & frame.facility_id.notna() & frame.facility_id.ne(expected)
    elif kind == "order_line":
        orders = curated.get("fact_sales_order")
        if orders is None:
            return empty
        orders = orders.set_index("order_id")
        bad = empty.copy()
        for field in ["product_id", "quantity", "unit_price", "uom", "order_date"]:
            expected = frame.order_id.map(orders[field])
            bad |= expected.notna() & frame[field].notna() & frame[field].ne(expected)
    elif kind == "shipment_order":
        orders = curated.get("fact_sales_order")
        if orders is None:
            return empty
        orders = orders.set_index("order_id")
        expected_date = pd.to_datetime(frame.order_id.map(orders.order_date), errors="coerce")
        expected_facility = frame.order_id.map(orders.facility_id)
        bad = pd.to_datetime(s, errors="coerce").lt(expected_date) | (expected_facility.notna() & frame.facility_id.ne(expected_facility))
    else:
        raise ValueError(f"Unknown validation logic: {kind}")
    return bad.fillna(False).astype(bool)

def validate(table, raw, clean, rules, curated, reference, settings, run_id):
    results, exceptions, checks = [], [], []
    reject = pd.Series(False, index=clean.index)
    detected = datetime.now(timezone.utc).isoformat()
    for rule in rules:
        if rule["table_name"] != table or not rule["active"]:
            continue
        frame = raw if rule["phase"] == "raw" else clean
        bad = failure_mask(rule, frame, curated, reference, settings.as_of)
        if rule["reject"]:
            reject |= bad
        checked, failed = len(frame), int(bad.sum())
        results.append({"run_id": run_id, "rule_id": rule["rule_id"], "records_checked": checked,
                        "records_passed": checked - failed, "records_failed": failed,
                        "pass_rate": (checked - failed) / checked if checked else 1., "failure_rate": failed / checked if checked else 0.,
                        "severity": rule["severity"], "executed_at": detected,
                        "affected_records": json.dumps(frame.loc[bad, "source_row"].astype(int).tolist())})
        # Row checks are persisted to support transparent facility/month denominators.
        date = TABLES[table][3]
        months = pd.to_datetime(clean[date], errors="coerce").dt.strftime("%Y-%m").fillna("UNKNOWN") if date else pd.Series("MASTER", index=frame.index)
        facilities = clean["facility_id"].fillna("UNKNOWN") if "facility_id" in clean else pd.Series("UNASSIGNED", index=frame.index)
        facilities = facilities.where(facilities.isin(reference["dim_facility"].facility_id) | facilities.eq("UNASSIGNED"), "UNKNOWN")
        checks.extend((run_id, rule["rule_id"], table, int(row), rule["source_system"], rule["dimension"], str(facility), str(month), int(passed))
                      for row, facility, month, passed in zip(frame.source_row, facilities, months, ~bad))
        for i in frame.index[bad]:
            col = rule["column_name"]
            key = TABLES[table][2]
            eid = hashlib.sha256(f"{rule['rule_id']}|{frame.at[i, 'source_row']}|{frame.at[i, key]}".encode()).hexdigest()[:24]
            repaired = rule["phase"] == "raw" and rule["validation_logic"] in ["canonical_label", "canonical_unit"] and not failure_mask(rule, clean.loc[[i]], curated, reference, settings.as_of).at[i]
            duplicate = rule["validation_logic"] == "unique"
            status = "Resolved" if repaired or duplicate else "Open"
            exceptions.append({"exception_id": eid, "run_id": run_id, "rule_id": rule["rule_id"], "source_system": rule["source_system"], "table_name": table,
                               "record_key": str(frame.at[i, key]), "source_row": int(frame.at[i, "source_row"]), "column_name": col,
                               "current_value": None if pd.isna(frame.at[i, col]) else str(frame.at[i, col]),
                               "expected_condition": rule["description"], "severity": rule["severity"], "status": status, "detected_at": detected,
                               "assigned_to": rule["source_system"] + " Data Steward", "resolution_note": "Automatic canonical repair" if repaired else "Duplicate occurrence excluded" if duplicate else "",
                               "resolved_at": detected if status == "Resolved" else None, "facility_id": str(facilities.at[i]), "month": str(months.at[i])})
    return results, exceptions, checks, reject

CHECK_COLUMNS = ["run_id", "rule_id", "table_name", "source_row", "source_system", "dimension", "facility_id", "month", "passed"]

def weighted_score(checks, weights):
    if checks.empty:
        return None
    work = checks.copy()
    work["bucket"] = work.dimension.replace({"timeliness": "timeliness_anomaly", "anomaly": "timeliness_anomaly"})
    rates = work.groupby("bucket").passed.mean()
    denominator = sum(weights[k] for k in rates.index)
    return round(100 * sum(weights[k] * v for k, v in rates.items()) / denominator, 4) if denominator else None

def score_breakdowns(checks, weights):
    rows = [{"scope": "overall", "group_name": "ALL", "score": weighted_score(checks, weights), "checks": len(checks), "failed_checks": int((1 - checks.passed).sum())}]
    for column in ["source_system", "table_name", "facility_id", "month", "dimension"]:
        for name, subset in checks.groupby(column, dropna=False):
            rows.append({"scope": column, "group_name": str(name), "score": weighted_score(subset, weights), "checks": len(subset), "failed_checks": int((1 - subset.passed).sum())})
    return pd.DataFrame(rows)
