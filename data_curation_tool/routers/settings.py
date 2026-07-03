from __future__ import annotations

from fastapi import APIRouter, Request

from .deps import ctx
from ..schemas import SettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
def get_settings(request: Request):
    return ctx(request).settings.to_safe_dict(include_secrets=False)


@router.put("")
def update_settings(payload: SettingsUpdate, request: Request):
    c = ctx(request)
    allowed = set(c.settings.__dataclass_fields__.keys())
    for key, value in payload.values.items():
        if key not in allowed:
            continue
        if key == "api_token_profiles" and isinstance(value, dict):
            current = getattr(c.settings, "api_token_profiles", {}) or {}
            merged = {}
            for provider, rows in value.items():
                old_rows = current.get(provider, []) if isinstance(current, dict) else []
                old_by_name = {str((row or {}).get("name") or (row or {}).get("label") or "").lower(): row for row in old_rows if isinstance(row, dict)}
                out_rows = []
                for row in rows or []:
                    if not isinstance(row, dict):
                        continue
                    item = dict(row)
                    key_name = str(item.get("name") or item.get("label") or "").lower()
                    if item.get("token") == "********" and key_name in old_by_name:
                        item["token"] = old_by_name[key_name].get("token")
                    out_rows.append(item)
                merged[provider] = out_rows
            value = merged
        setattr(c.settings, key, value)
        c.db.set_setting(key, value)
    c.settings.save(c.paths.settings)
    return c.settings.to_safe_dict(include_secrets=False)
