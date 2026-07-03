#!/usr/bin/env python
"""Offline structural and API verification for the FlexAvatar integration."""
from __future__ import annotations

import json
import tempfile
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    root = ROOT
    source = root / "integrations" / "flexavatar" / "source"
    require((source / "src" / "flexavatar" / "model" / "flexavatar_model.py").is_file(), "Bundled FlexAvatar model source is missing")
    require((source / "models" / "FLEX-1" / "model_config.json").is_file(), "FLEX-1 model config is missing")
    require((root / "scripts" / "flexavatar" / "flexavatar_bridge.py").is_file(), "Subprocess bridge is missing")
    env_text = (root / "integrations" / "flexavatar" / "environment-dct.yml").read_text(encoding="utf-8")
    for dependency in ("torch==2.7.1", "sam_loss", "dino_loss", "gaussian_splatting", "numpy<2"):
        require(dependency in env_text, f"Isolated runtime dependency missing: {dependency}")

    with tempfile.TemporaryDirectory(prefix="dct-flexavatar-verify-") as raw:
        temp = Path(raw)
        paths = AppPaths.create(runtime=temp / "runtime", models=temp / "models", outputs=temp / "outputs")
        client = TestClient(create_app(paths))
        status = client.get("/api/flexavatar/status").json()
        require(status["source_ready"] is True, "FlexAvatar source did not register")
        require(status["paper_baseline"]["training_steps"] == 1_000_000, "Paper baseline was not encoded")

        dataset = temp / "portraits"
        dataset.mkdir()
        for index in range(2):
            Image.new("RGB", (128, 128), (40 + index * 80, 90, 140)).save(dataset / f"portrait_{index}.png")
        imported = client.post("/api/datasets/import", json={
            "root_path": str(dataset), "recursive": True, "read_sidecars": False,
            "compute_sha256": False, "probe_dimensions": True,
        })
        require(imported.status_code == 200, imported.text)
        import_job_id = imported.json().get("job_id")
        if import_job_id:
            for _ in range(200):
                import_job = client.get(f"/api/jobs/{import_job_id}").json()
                if import_job.get("status") in {"completed", "failed", "cancelled"}:
                    break
                time.sleep(0.02)
            require(import_job.get("status") == "completed", json.dumps(import_job, indent=2))
        media_ids = [int(row["id"]) for row in client.get("/api/media", params={"page_size": 10}).json()["items"]]
        require(len(media_ids) == 2, "Dataset import did not create the verification media rows")
        stage = client.post("/api/flexavatar/stage", json={
            "avatar_name": "verification subject", "mode": "few_shot",
            "media_ids": media_ids, "paths": [], "role": "source", "replace": True,
        })
        require(stage.status_code == 200, stage.text)
        stage_body = stage.json()
        require(len(stage_body["items"]) == 2, "Few-shot staging did not preserve both observations")
        require(Path(stage_body["manifest"]).is_file(), "Staging manifest was not written")

        code_dir = paths.runtime / "flexavatar" / "avatar_codes" / "itw"
        code_dir.mkdir(parents=True, exist_ok=True)
        first = code_dir / "avatar_code_first.npy"
        second = code_dir / "avatar_code_second.npy"
        np.save(first, np.zeros((1, 2, 2, 2), dtype=np.float32))
        np.save(second, np.ones((1, 2, 2, 2), dtype=np.float32))
        blended = client.post("/api/flexavatar/interpolate", json={
            "first": str(first), "second": str(second), "alpha": 0.25, "output_name": "verified_blend",
        })
        require(blended.status_code == 200, blended.text)
        require(np.allclose(np.load(blended.json()["path"]), 0.75), "Avatar-code interpolation is incorrect")

        bundle = client.post("/api/flexavatar/training/bundle", json={
            "name": "verify_training", "media_ids": media_ids,
            "source_type": "monocular_2d", "steps": 1_000_000,
            "batch_size": 20, "perceptual_start_step": 400_000,
        })
        require(bundle.status_code == 200, bundle.text)
        config = json.loads(Path(bundle.json()["config"]).read_text(encoding="utf-8"))
        require(config["architecture"]["avatar_code_shape"] == [32, 32, 768], "Training bundle architecture mismatch")
        require(config["trainer"]["available_in_upstream_release"] is False, "Training scope must remain explicit")
        client.close()

    print("v5.31 FlexAvatar offline verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
