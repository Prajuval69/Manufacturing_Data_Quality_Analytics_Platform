"""Local source hygiene receipt without printing potential secret values."""
import ast
import json
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import Settings

def audit():
    settings = Settings()
    root = settings.root
    errors = []
    pyfiles = list((root / "src").rglob("*.py")) + list((root / "tests").rglob("*.py")) + list((root / "scripts").rglob("*.py"))
    for path in pyfiles:
        text = path.read_text(encoding="utf-8")
        ast.parse(text, filename=str(path))
        if re.search(r"[A-Z]:\\(?:Users|projects)\\", text):
            errors.append({"file": str(path.relative_to(root)), "issue": "Hardcoded host path"})
        if re.search(r"\b(?:sk|ghp|github_pat)[-_][A-Za-z0-9_-]{20,}", text):
            errors.append({"file": str(path.relative_to(root)), "issue": "Possible embedded credential"})
    secret_hits = []
    for folder in ["src", "config", "docs", "outputs", "data/raw", "data/reference"]:
        for path in (root / folder).rglob("*"):
            if not path.is_file() or path.suffix not in [".py", ".json", ".csv", ".md", ".xml"]:
                continue
            content = path.read_text(encoding="utf-8")
            if re.search(r"\b(?:sk|ghp|github_pat)[-_][A-Za-z0-9_-]{20,}", content):
                secret_hits.append(str(path.relative_to(root)))
    ignore = (root / ".gitignore").read_text(encoding="utf-8")
    env_example = (root / ".env.example").read_text(encoding="utf-8")
    missing_docs = [f for f in ["ARCHITECTURE", "DATA_MODEL", "DATA_DICTIONARY", "DATA_QUALITY_RULES", "DQ_SCORING", "GOVERNANCE", "LINEAGE", "POWER_BI_GUIDE", "API_GUIDE", "AI_ASSISTANT", "TESTING", "PROJECT_WALKTHROUGH"] if not (root / "docs" / (f + ".md")).exists()]
    result = {"python_files_parsed": len(pyfiles), "source_issues": errors, "possible_secret_files": secret_hits,
              "env_ignored": ".env" in ignore.splitlines(), "example_key_empty": "LLM_API_KEY=\n" in env_example,
              "fake_pbix_files": [str(p.relative_to(root)) for p in root.rglob("*.pbix")], "missing_docs": missing_docs,
              "temporary_build_files": [str(p.relative_to(root)) for p in (root / "data/processed").glob("*.building")],
              "git_repository_present": (root / ".git").exists()}
    result["passed"] = not (errors or secret_hits or missing_docs or result["fake_pbix_files"] or result["temporary_build_files"]) and result["env_ignored"] and result["example_key_empty"]
    (root / "outputs/reports/hygiene_audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    assert result["passed"], result
    return result

if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
