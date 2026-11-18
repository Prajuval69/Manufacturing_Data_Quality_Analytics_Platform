"""CSV source adapters enforce contracts; reference feeds are trusted separately."""
import pandas as pd
from src.config import TABLES, Settings

def ingest(settings: Settings):
    frames = {}
    for table, (source, filename, _, _, columns) in TABLES.items():
        path = settings.root / "data/raw" / source / filename
        frame = pd.read_csv(path, dtype="string", keep_default_na=False)
        missing = set(columns) - set(frame.columns)
        extra = set(frame.columns) - set(columns)
        if missing or extra:
            raise ValueError(f"Schema drift in {table}: missing={sorted(missing)}, extra={sorted(extra)}")
        frame = frame.replace(r"^\s*$", pd.NA, regex=True)
        frame["source_row"] = range(len(frame))
        frames[table] = frame
        frame.to_csv(settings.root / "data/staging" / f"{table}.csv", index=False)
    return frames

def references(settings: Settings):
    return {path.stem: pd.read_csv(path, dtype="string") for path in sorted((settings.root / "data/reference").glob("dim_*.csv"))}
