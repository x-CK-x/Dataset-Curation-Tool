from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from .deps import ctx
from ..schemas import SqlQuery
from ..utils import is_safe_readonly_sql

router = APIRouter(prefix="/database", tags=["database"])


@router.post("/query")
def query(payload: SqlQuery, request: Request):
    c = ctx(request)
    if not c.settings.enable_write_sql and not is_safe_readonly_sql(payload.sql):
        raise HTTPException(status_code=403, detail="Only read-only SELECT/WITH/PRAGMA queries are enabled by default.")
    return {"rows": c.db.query(payload.sql, payload.params)}
