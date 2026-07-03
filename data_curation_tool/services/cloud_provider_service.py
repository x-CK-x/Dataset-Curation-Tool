from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from ..config import AppSettings


@dataclass
class CloudProviderService:
    settings: AppSettings

    def _token(self, provider: str, token_profile: str | None = None) -> str:
        token = self.settings.resolve_api_token(provider, token_profile) if hasattr(self.settings, "resolve_api_token") else None
        if not token:
            raise ValueError(f"No API token configured for provider '{provider}'" + (f" profile '{token_profile}'" if token_profile else ""))
        return token

    @staticmethod
    def _json_or_text(response: requests.Response) -> Any:
        try:
            return response.json()
        except Exception:
            return {"text": response.text}

    def runpod(self, *, endpoint_id: str, input_payload: dict[str, Any], sync: bool = False, token_profile: str | None = None, extra: dict[str, Any] | None = None, timeout: int = 300) -> dict[str, Any]:
        endpoint = str(endpoint_id or "").strip()
        if not endpoint:
            raise ValueError("RunPod endpoint_id is required.")
        route = "runsync" if sync else "run"
        url = f"https://api.runpod.ai/v2/{endpoint}/{route}"
        body = {"input": input_payload or {}}
        if extra:
            body.update(extra)
        resp = requests.post(url, headers={"Authorization": f"Bearer {self._token('runpod', token_profile)}", "Content-Type": "application/json"}, json=body, timeout=timeout)
        data = self._json_or_text(resp)
        if resp.status_code >= 400:
            raise RuntimeError(f"RunPod {route} request failed with HTTP {resp.status_code}: {data}")
        return {"provider": "runpod", "endpoint_id": endpoint, "sync": sync, "status_code": resp.status_code, "result": data}

    def vastai(self, *, method: str = "GET", path: str = "/instances/", params: dict[str, Any] | None = None, body: dict[str, Any] | None = None, token_profile: str | None = None, timeout: int = 120) -> dict[str, Any]:
        clean_path = "/" + str(path or "").lstrip("/")
        url = f"https://console.vast.ai/api/v0{clean_path}"
        resp = requests.request(str(method or "GET").upper(), url, headers={"Authorization": f"Bearer {self._token('vastai', token_profile)}"}, params=params or None, json=body if body is not None else None, timeout=timeout)
        data = self._json_or_text(resp)
        if resp.status_code >= 400:
            raise RuntimeError(f"Vast.ai request failed with HTTP {resp.status_code}: {data}")
        return {"provider": "vastai", "method": str(method or "GET").upper(), "path": clean_path, "status_code": resp.status_code, "result": data}

    def lambda_labs(self, *, method: str = "GET", path: str = "/instances", params: dict[str, Any] | None = None, body: dict[str, Any] | None = None, token_profile: str | None = None, timeout: int = 120) -> dict[str, Any]:
        clean_path = "/" + str(path or "").lstrip("/")
        # Lambda Cloud's public API browser is rooted at cloud.lambdalabs.com/api/v1.
        url = f"https://cloud.lambdalabs.com/api/v1{clean_path}"
        token = self._token('lambda_labs', token_profile)
        resp = requests.request(str(method or "GET").upper(), url, auth=(token, ""), params=params or None, json=body if body is not None else None, timeout=timeout)
        data = self._json_or_text(resp)
        if resp.status_code >= 400:
            raise RuntimeError(f"Lambda Labs request failed with HTTP {resp.status_code}: {data}")
        return {"provider": "lambda_labs", "method": str(method or "GET").upper(), "path": clean_path, "status_code": resp.status_code, "result": data}
