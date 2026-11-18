"""Real loopback HTTP smoke test. Run while uvicorn is listening locally."""
import json
from pathlib import Path
import sys
import httpx

ROOT = Path(__file__).resolve().parents[1]

def smoke(base="http://127.0.0.1:8000"):
    results = []
    with httpx.Client(base_url=base, timeout=20) as client:
        def record(method, path, expected=200, **kwargs):
            response = client.request(method, path, **kwargs)
            body = response.json()
            passed = response.status_code == expected and bool(body)
            results.append({"method": method, "path": path, "expected_status": expected, "status": response.status_code, "passed": passed})
            if not passed:
                raise AssertionError(f"{method} {path}: {response.status_code} {body}")
            return body
        health = record("GET", "/health")
        local_run = json.loads((ROOT / "outputs/reports/pipeline_summary.json").read_text(encoding="utf-8"))["run_id"]
        assert health["company"] == "PackRight Manufacturing" and health["run_id"] == local_run
        for path in ["/openapi.json", "/api/kpis/summary", "/api/kpis/facilities", "/api/kpis/products", "/api/data-quality/summary", "/api/data-quality/rules", "/api/governance/metadata", "/api/governance/glossary", "/api/governance/lineage", "/api/profiling/fact_production"]:
            record("GET", path)
        queue = record("GET", "/api/exceptions?status=Open&severity=High&limit=2")
        assert queue["total"] > 0 and len(queue["items"]) > 0
        eid = queue["items"][0]["exception_id"]
        original = record("GET", "/api/exceptions/" + eid)
        changed = record("PATCH", "/api/exceptions/" + eid, json={"status": "In Review"})
        assert changed["status"] == "In Review"
        # Restore exact original queue state after verifying mutation.
        record("PATCH", "/api/exceptions/" + eid, json={"status": original["status"]})
        record("GET", "/api/exceptions/not-present", expected=404)
        record("GET", "/api/profiling/not-present", expected=404)
        record("GET", "/api/exceptions?limit=0", expected=422)
        record("PATCH", "/api/exceptions/" + eid, expected=422, json={"status": "Resolved"})
        assistant = record("POST", "/api/assistant/ask", json={"question": "Which rules are failing most often?", "use_llm": False})
        assert assistant["mode"] == "deterministic" and assistant["evidence"]["top_failed_rules"]
    result = {"base_url": base, "run_id": health["run_id"], "passed": len(results), "failed": 0, "results": results, "assistant_mode": assistant["mode"]}
    (ROOT / "outputs/reports/api_smoke.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result

if __name__ == "__main__":
    print(json.dumps(smoke(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"), indent=2))
