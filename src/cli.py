import argparse
import json
import pandas as pd
from src.config import Settings
from src.data.generate import generate
from src.pipeline.run import run
from src.reporting.export import export

def main():
    parser = argparse.ArgumentParser(description="PackRight synthetic manufacturing platform")
    parser.add_argument("command", choices=["generate", "pipeline", "all", "profile", "report", "governance", "verify"])
    parser.add_argument("--root", default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--corruption-rate", type=float, default=.03)
    parser.add_argument("--scale", type=float, default=1.)
    parser.add_argument("--as-of", default="2026-07-31")
    args = parser.parse_args()
    settings = Settings(**({"root": args.root} if args.root else {}), seed=args.seed, corruption_rate=args.corruption_rate, as_of=args.as_of)
    if args.command in ["generate", "all"]:
        result = generate(settings, args.scale)
    if args.command in ["pipeline", "all"]:
        result = run(settings)
    if args.command in ["profile", "report", "governance"]:
        if args.command == "profile":
            from src.pipeline.ingestion import ingest
            from src.profiling.engine import profile
            settings.prepare()
            pd.concat([profile(t, f) for t,f in ingest(settings).items()]).to_csv(settings.root / "outputs/profiling/raw_profile.csv", index=False)
        result = {"exported_files": export(settings)}
    if args.command == "verify":
        from src.verification import verify
        result = verify(settings)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
