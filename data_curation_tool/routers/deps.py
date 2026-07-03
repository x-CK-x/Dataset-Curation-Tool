from __future__ import annotations

from fastapi import Request

from ..context import AppContext


def ctx(request: Request) -> AppContext:
    return request.app.state.context
