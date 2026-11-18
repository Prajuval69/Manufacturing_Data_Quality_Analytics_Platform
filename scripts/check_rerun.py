"""Compare full-scale source and database fingerprints before/after regeneration."""
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import Settings
from src.data.generate import generate
from src.pipeline.run import run
from src.verification import snapshot_fingerprint

def check_rerun():
    settings = Settings()
    manifest = json.loads((settings.root / "data/raw/manifest.json").read_text(encoding="utf-8"))
    settings.seed = manifest["seed"]
    settings.corruption_rate = manifest["corruption_rate"]
    settings.as_of = manifest["as_of"]
    source_hash = lambda: {str(p.relative_to(settings.root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((settings.root / "data/raw").rglob("*.csv"))}
    before_sources = source_hash()
    before_db = snapshot_fingerprint(settings)
    generate(settings, manifest["scale"])
    summary = run(settings)
    after_db = snapshot_fingerprint(settings)
    result = {"same_raw_sources": before_sources == source_hash(), "same_database_fingerprints": before_db == after_db,
              "run_id": summary["run_id"], "tables": after_db}
    assert result["same_raw_sources"] and result["same_database_fingerprints"], result
    (settings.root / "outputs/reports/rerun_verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result

if __name__ == "__main__":
    print(json.dumps(check_rerun(), indent=2))
