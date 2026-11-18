import json
import pandas as pd

def profile(table, frame, stage="raw"):
    rows = []
    for col in frame.columns:
        if col == "source_row":
            continue
        series = frame[col]
        numeric = pd.to_numeric(series, errors="coerce")
        is_numeric = col in ["quantity", "unit_price"] or pd.api.types.is_numeric_dtype(series)
        nonnull = series.dropna()
        rows.append({"table_name": table, "stage": stage, "column_name": col, "row_count": len(frame),
                     "column_count": len(frame.columns) - ("source_row" in frame), "data_type": str(series.dtype),
                     "null_count": int(series.isna().sum()), "null_percentage": round(100 * series.isna().mean(), 4) if len(frame) else 0.,
                     "unique_count": int(series.nunique()), "duplicate_count": int(nonnull.duplicated().sum()),
                     "row_duplicate_count": int(frame.drop(columns=["source_row"], errors="ignore").duplicated().sum()),
                     "min_value": str(numeric.min()) if is_numeric and numeric.notna().any() else (str(nonnull.min()) if len(nonnull) else None),
                     "max_value": str(numeric.max()) if is_numeric and numeric.notna().any() else (str(nonnull.max()) if len(nonnull) else None),
                     "mean_value": float(numeric.mean()) if is_numeric and numeric.notna().any() else None,
                     "median_value": float(numeric.median()) if is_numeric and numeric.notna().any() else None,
                     "sample_values": json.dumps(nonnull.astype(str).drop_duplicates().head(5).tolist())})
    result = pd.DataFrame(rows)
    for col in ["mean_value", "median_value"]:
        result[col] = pd.to_numeric(result[col], errors="coerce")
    return result
