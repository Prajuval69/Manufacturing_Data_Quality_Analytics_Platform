import pytest
from fastapi.testclient import TestClient
from src.api.app import create_app
from src.config import Settings

@pytest.mark.parametrize("path", [
    "/health", "/api/kpis/summary", "/api/kpis/facilities", "/api/kpis/products", "/api/data-quality/summary",
    "/api/data-quality/rules", "/api/exceptions", "/api/governance/metadata", "/api/governance/glossary",
    "/api/governance/lineage", "/api/profiling/fact_production",
])
def test_read_endpoints(client, path):
    response = client.get(path)
    assert response.status_code == 200 and response.json()

def test_filter_and_pagination(client):
    first = client.get("/api/exceptions", params={"status": "Open", "severity": "Critical", "limit": 1}).json()
    second = client.get("/api/exceptions", params={"status": "Open", "severity": "Critical", "limit": 1, "offset": 1}).json()
    assert first["total"] > 1
    assert first["items"][0]["status"] == "Open" and first["items"][0]["severity"] == "Critical"
    assert first["items"][0]["exception_id"] != second["items"][0]["exception_id"]

def test_exception_workflow(client):
    eid = client.get("/api/exceptions", params={"status": "Open", "limit": 1}).json()["items"][0]["exception_id"]
    original = client.get("/api/exceptions/" + eid).json()
    before = client.get("/api/kpis/summary").json()["open_exceptions"]
    changed = client.patch("/api/exceptions/" + eid, json={"status": "Resolved", "resolution_note": "Verified synthetic source correction", "assigned_to": "Test Steward"})
    assert changed.status_code == 200 and changed.json()["resolved_at"]
    assert client.get("/api/kpis/summary").json()["open_exceptions"] == before - 1
    reopened = client.patch("/api/exceptions/" + eid, json={"status": "Open"}).json()
    assert reopened["resolved_at"] is None
    client.patch("/api/exceptions/" + eid, json={"status": original["status"], "assigned_to": original["assigned_to"]})

@pytest.mark.parametrize("body", [{}, {"status": "INVALID"}, {"status": "Resolved"}, {"status": None}, {"unknown": "x"}, {"status": "Accepted", "resolution_note": "  "}])
def test_invalid_patch(client, body):
    eid = client.get("/api/exceptions?limit=1").json()["items"][0]["exception_id"]
    assert client.patch("/api/exceptions/" + eid, json=body).status_code == 422

@pytest.mark.parametrize("path,status", [("/api/exceptions/absent",404), ("/api/profiling/not_a_table",404), ("/api/exceptions?limit=0",422), ("/api/exceptions?status=Bad",422), ("/api/kpis/products?offset=-1",422)])
def test_error_responses(client, path, status):
    assert client.get(path).status_code == status

def test_missing_database_returns_503(tmp_path):
    client = TestClient(create_app(Settings(root=tmp_path, database_url="sqlite:///absent.db")))
    assert client.get("/health").status_code == 503

def test_metadata_filter(client):
    rows = client.get("/api/governance/metadata?table_name=dim_product").json()
    assert len(rows) == 5 and all(r["table_name"] == "dim_product" for r in rows)

def test_assistant_endpoint(client, monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    result = client.post("/api/assistant/ask", json={"question": "Which facility has the most exceptions?", "use_llm": True})
    assert result.status_code == 200 and result.json()["mode"] == "deterministic"
    assert result.json()["evidence"]["facility_exceptions"]
