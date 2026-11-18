"""Local portfolio API; reads a verified SQLite snapshot, never arbitrary SQL."""
from contextlib import contextmanager
from datetime import datetime, timezone
from enum import Enum
from typing import Literal
import sqlite3
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator
from src.config import Settings, TABLES

class ExceptionStatus(str, Enum):
    open = "Open"
    review = "In Review"
    resolved = "Resolved"
    accepted = "Accepted"

class ExceptionPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: ExceptionStatus | None = None
    assigned_to: str | None = Field(default=None, min_length=1, max_length=120)
    resolution_note: str | None = Field(default=None, min_length=1, max_length=2000)

    @model_validator(mode="after")
    def valid_patch(self):
        if not self.model_fields_set or any(getattr(self, k) is None for k in self.model_fields_set):
            raise ValueError("Provide at least one non-null update field")
        if self.status in [ExceptionStatus.resolved, ExceptionStatus.accepted] and not (self.resolution_note and self.resolution_note.strip()):
            raise ValueError("Resolved/Accepted requires a resolution note")
        return self

class AssistantQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=3, max_length=2000)
    use_llm: bool = False

class HealthResponse(BaseModel):
    status: str
    company: str
    run_id: str
    synthetic_only: bool

def create_app(settings: Settings | None = None):
    settings = settings or Settings()
    app = FastAPI(title="PackRight Data Quality & Governance", version="1.0.0",
                  description="Synthetic portfolio data only. Local demonstration; no authentication.")
    app.state.settings = settings

    @contextmanager
    def connection(write=False):
        if not settings.db_path.exists():
            raise HTTPException(503, "Database unavailable; run python -m src.cli all")
        # mode=rw/ro prevents silently creating an empty database.
        conn = sqlite3.connect(settings.db_path.as_uri() + ("?mode=rw" if write else "?mode=ro"), uri=True, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            if write:
                conn.commit()
        finally:
            conn.close()

    def rows(sql, params=()):
        with connection() as conn:
            return [dict(r) for r in conn.execute(sql, params)]

    @app.get("/health", response_model=HealthResponse)
    def health():
        runs = rows("SELECT run_id FROM dq_run")
        if not runs:
            raise HTTPException(503, "No completed pipeline snapshot")
        return {"status": "ok", "company": "PackRight Manufacturing", "run_id": runs[0]["run_id"], "synthetic_only": True}

    @app.get("/api/kpis/summary")
    def kpis():
        return rows("SELECT * FROM executive_kpis")[0]

    @app.get("/api/kpis/facilities")
    def facilities():
        return rows("SELECT * FROM facility_performance ORDER BY facility_id")

    @app.get("/api/kpis/products")
    def products(limit: int = Query(200, ge=1, le=1000), offset: int = Query(0, ge=0)):
        return rows("SELECT * FROM product_performance ORDER BY product_id LIMIT ? OFFSET ?", (limit, offset))

    @app.get("/api/data-quality/summary")
    def quality_summary():
        return {"run": rows("SELECT * FROM dq_run")[0], "scores": rows("SELECT * FROM dq_score ORDER BY scope,group_name"),
                "exception_statuses": rows("SELECT status,COUNT(*) AS count FROM dq_exception GROUP BY status")}

    @app.get("/api/data-quality/rules")
    def quality_rules(dimension: str | None = None):
        return rows("SELECT * FROM dq_rule WHERE (? IS NULL OR dimension=?) ORDER BY rule_id", (dimension, dimension))

    @app.get("/api/exceptions")
    def exceptions(status: ExceptionStatus | None = None, severity: Literal["Critical", "High", "Medium", "Low"] | None = None,
                   source_system: str | None = None, table_name: str | None = None, facility_id: str | None = None,
                   limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
        values = [status.value if status else None, severity, source_system, table_name, facility_id]
        where = " AND ".join(f"(? IS NULL OR {field}=?)" for field in ["status", "severity", "source_system", "table_name", "facility_id"])
        params = tuple(v for value in values for v in (value, value))
        total = rows("SELECT COUNT(*) AS count FROM dq_exception WHERE " + where, params)[0]["count"]
        items = rows("SELECT * FROM dq_exception WHERE " + where + " ORDER BY detected_at,exception_id LIMIT ? OFFSET ?", params + (limit, offset))
        return {"total": total, "limit": limit, "offset": offset, "items": items}

    @app.get("/api/exceptions/{exception_id}")
    def exception(exception_id: str):
        result = rows("SELECT * FROM dq_exception WHERE exception_id=?", (exception_id,))
        if not result:
            raise HTTPException(404, "Exception not found")
        return result[0]

    @app.patch("/api/exceptions/{exception_id}")
    def patch_exception(exception_id: str, patch: ExceptionPatch):
        values = patch.model_dump(exclude_unset=True, mode="json")
        if "status" in values:
            values["resolved_at"] = datetime.now(timezone.utc).isoformat() if values["status"] in ["Resolved", "Accepted"] else None
        fields = ",".join(f"{k}=?" for k in values)
        with connection(write=True) as conn:
            result = conn.execute("UPDATE dq_exception SET " + fields + " WHERE exception_id=?", tuple(values.values()) + (exception_id,))
            if not result.rowcount:
                raise HTTPException(404, "Exception not found")
            conn.execute("UPDATE executive_kpis SET open_exceptions=(SELECT COUNT(*) FROM dq_exception WHERE status IN ('Open','In Review')), critical_exceptions=(SELECT COUNT(*) FROM dq_exception WHERE status IN ('Open','In Review') AND severity='Critical')")
        return exception(exception_id)

    @app.get("/api/governance/metadata")
    def metadata(table_name: str | None = None):
        return rows("SELECT * FROM metadata_catalog WHERE (? IS NULL OR table_name=?) ORDER BY table_name,field_name", (table_name, table_name))

    @app.get("/api/governance/glossary")
    def glossary():
        return rows("SELECT * FROM business_glossary ORDER BY term")

    @app.get("/api/governance/lineage")
    def lineage():
        return rows("SELECT * FROM data_lineage ORDER BY lineage_id")

    @app.get("/api/profiling/{table_name}")
    def profiling(table_name: str, stage: Literal["raw", "cleaned", "curated"] = "raw"):
        if table_name not in TABLES:
            raise HTTPException(404, "Unknown contracted table")
        return rows("SELECT * FROM profiling_result WHERE table_name=? AND stage=? ORDER BY column_name", (table_name, stage))

    @app.post("/api/assistant/ask")
    def ask(question: AssistantQuestion):
        from src.ai.assistant import Assistant
        with connection() as conn:
            return Assistant(conn).answer(question.question, use_llm=question.use_llm)

    return app

app = create_app()
