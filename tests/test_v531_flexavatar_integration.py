from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths


def _client(tmp_path: Path) -> tuple[TestClient, AppPaths]:
    paths = AppPaths.create(
        runtime=tmp_path / "runtime",
        models=tmp_path / "models",
        outputs=tmp_path / "outputs",
    )
    return TestClient(create_app(paths)), paths


def _import_portraits(client: TestClient, tmp_path: Path, count: int = 2) -> list[int]:
    root = tmp_path / "portrait_dataset"
    root.mkdir(exist_ok=True)
    for index in range(count):
        Image.new("RGB", (96 + index * 8, 112), (40 + index * 30, 90, 130)).save(root / f"portrait_{index}.png")
    response = client.post(
        "/api/datasets/import",
        json={
            "root_path": str(root),
            "recursive": True,
            "read_sidecars": False,
            "compute_sha256": False,
            "probe_dimensions": True,
        },
    )
    assert response.status_code == 200, response.text
    return [int(row["id"]) for row in client.get("/api/media", params={"page_size": 10}).json()["items"]]


def test_flexavatar_status_model_catalog_and_source_bundle(tmp_path: Path):
    client, _ = _client(tmp_path)
    status = client.get("/api/flexavatar/status")
    assert status.status_code == 200, status.text
    body = status.json()
    assert body["source_ready"] is True
    assert body["license"].startswith("CC BY-NC")
    assert body["paper_baseline"]["training_steps"] == 1_000_000
    assert body["paper_baseline"]["batch_size"] == 20
    assert Path(body["source_path"], "src", "flexavatar", "model", "flexavatar_model.py").exists()
    assert Path(body["bridge_script"]).exists()

    models = {row["name"]: row for row in client.get("/api/models").json()}
    assert "flexavatar-flex-1" in models
    assert "single_image_avatar" in models["flexavatar-flex-1"]["capabilities"]
    audit = client.get("/api/system/feature-audit").json()
    assert audit["flexavatar_present"] is True
    client.close()


def test_flexavatar_staging_assets_interpolation_and_file_security(tmp_path: Path):
    client, paths = _client(tmp_path)
    media_ids = _import_portraits(client, tmp_path, count=2)
    stage = client.post(
        "/api/flexavatar/stage",
        json={
            "avatar_name": "few shot subject",
            "mode": "few_shot",
            "media_ids": media_ids,
            "paths": [],
            "role": "source",
            "replace": True,
        },
    )
    assert stage.status_code == 200, stage.text
    staged = stage.json()
    assert staged["avatar_name"] == "few_shot_subject"
    assert len(staged["items"]) == 2
    assert Path(staged["manifest"]).is_file()
    assert all(Path(row["path"]).suffix == ".png" and Path(row["path"]).is_file() for row in staged["items"])

    code_dir = paths.runtime / "flexavatar" / "avatar_codes" / "itw"
    code_dir.mkdir(parents=True, exist_ok=True)
    code_a = code_dir / "avatar_code_a.npy"
    code_b = code_dir / "avatar_code_b.npy"
    np.save(code_a, np.zeros((1, 4, 4, 3), dtype=np.float32))
    np.save(code_b, np.ones((1, 4, 4, 3), dtype=np.float32))
    blend = client.post(
        "/api/flexavatar/interpolate",
        json={"first": str(code_a), "second": str(code_b), "alpha": 0.25, "output_name": "blend"},
    )
    assert blend.status_code == 200, blend.text
    blend_path = Path(blend.json()["path"])
    assert blend_path.is_file()
    assert np.allclose(np.load(blend_path), 0.75)

    assets = client.get("/api/flexavatar/assets").json()
    assert any(row["path"] == staged["manifest"] for row in assets["manifests"])
    assert any(row["path"] == str(blend_path) for row in assets["avatar_codes"])
    allowed = client.get("/api/flexavatar/file", params={"path": staged["manifest"]})
    assert allowed.status_code == 200
    outside = tmp_path / "outside.txt"
    outside.write_text("no", encoding="utf-8")
    denied = client.get("/api/flexavatar/file", params={"path": str(outside)})
    assert denied.status_code == 403
    client.close()


def test_flexavatar_local_checkpoint_training_bundle_and_nonexistent_trainer_guard(tmp_path: Path):
    client, paths = _client(tmp_path)
    media_ids = _import_portraits(client, tmp_path, count=1)
    checkpoint = tmp_path / "ckpt-900k.pt"
    checkpoint.write_bytes(b"FLEX" + b"\0" * (1024 * 1024 + 32))
    queued = client.post(
        "/api/flexavatar/checkpoint",
        json={"local_path": str(checkpoint), "force": True},
    )
    assert queued.status_code == 200, queued.text
    job = client.get(f"/api/jobs/{queued.json()['job_id']}").json()
    assert job["status"] == "completed", job
    installed = paths.runtime / "flexavatar" / "models" / "FLEX-1" / "checkpoints" / "ckpt-900k.pt"
    assert installed.is_file() and installed.stat().st_size == checkpoint.stat().st_size

    bundle = client.post(
        "/api/flexavatar/training/bundle",
        json={
            "name": "research_bundle",
            "media_ids": media_ids,
            "source_type": "monocular_2d",
            "steps": 1_000_000,
            "batch_size": 20,
            "perceptual_start_step": 400_000,
            "mixed_precision": "bf16",
            "nproc_per_node": 2,
            "device_ids": [0, 1],
        },
    )
    assert bundle.status_code == 200, bundle.text
    bundle_body = bundle.json()
    config = json.loads(Path(bundle_body["config"]).read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in Path(bundle_body["manifest"]).read_text(encoding="utf-8").splitlines()]
    assert rows[0]["bias_sink_id"] == 0
    assert config["architecture"]["avatar_code_shape"] == [32, 32, 768]
    assert config["optimization"]["losses"] == ["L1", "SSIM", "DINOv2 perceptual", "SAM perceptual"]
    assert config["trainer"]["available_in_upstream_release"] is False

    plan = client.post(
        "/api/flexavatar/training/plan",
        json={"config_path": bundle_body["config"], "trainer_entrypoint": "", "nproc_per_node": 2, "extra_args": []},
    )
    assert plan.status_code == 200, plan.text
    plan_body = plan.json()
    assert plan_body["runnable"] is False
    assert plan_body["entrypoint_exists"] is False
    assert "does not include a full training entrypoint" in plan_body["warning"]
    client.close()


def test_flexavatar_frontend_scripts_docs_and_license_are_packaged():
    root = Path(__file__).resolve().parents[1]
    app_js = (root / "data_curation_tool" / "static" / "app.js").read_text(encoding="utf-8")
    for text in (
        "FlexAvatar",
        "Install / Update Quick Runtime",
        "Install Full Pixel3DMM Runtime",
        "Stage Selected / Local Source Inputs",
        "Track Source Manifest",
        "Create / Fit / Render",
        "Launch Official Interactive Viewer",
        "Create Interpolated Avatar Code",
        "Create Mixed-Supervision Training Bundle",
        "The attached official release does not include the authors’ complete base-model training program",
    ):
        assert text in app_js

    assert (root / "install_flexavatar.bat").is_file()
    assert (root / "install_flexavatar.sh").is_file()
    assert (root / "integrations" / "flexavatar" / "environment-dct.yml").is_file()
    assert (root / "integrations" / "flexavatar" / "FLEXAVATAR_LICENSE.txt").is_file()
    assert (root / "docs" / "V5_31_FLEXAVATAR_INTEGRATION.md").is_file()
    source = root / "integrations" / "flexavatar" / "source"
    assert (source / "scripts" / "render_example.py").is_file()
    assert (source / "scripts" / "run_gui.py").is_file()
    assert (source / "scripts" / "track_pixel3dmm_itw.py").is_file()


def test_flexavatar_seed_examples_include_tracking_and_ready_manifests(tmp_path: Path):
    client, paths = _client(tmp_path)
    queued = client.post('/api/flexavatar/seed-examples')
    assert queued.status_code == 200, queued.text
    job = client.get(f"/api/jobs/{queued.json()['job_id']}").json()
    assert job['status'] == 'completed', job
    result = job.get('result') or {}
    assert 'marble_sculpture' in result.get('pretracked_examples', [])
    manifest = paths.runtime / 'flexavatar' / 'manifests' / 'marble_sculpture_source.json'
    assert manifest.is_file()
    payload = json.loads(manifest.read_text(encoding='utf-8'))
    assert payload['bundled_pretracked'] is True
    assert Path(payload['items'][0]['path']).is_file()
    assert (paths.runtime / 'flexavatar' / 'pixel3dmm_processing' / 'processing' / 'itw' / 'marble_sculpture').is_dir()
    assert (paths.runtime / 'flexavatar' / 'pixel3dmm_processing' / 'tracking' / 'itw' / 'marble_sculpture').is_dir()
    assert (paths.runtime / 'flexavatar' / 'pixel3dmm_processing' / 'tracking' / 'nersemble' / '240').is_dir()
    client.close()


def test_flexavatar_environment_declares_complete_fitting_dependencies():
    root = Path(__file__).resolve().parents[1]
    env_text = (root / 'integrations' / 'flexavatar' / 'environment-dct.yml').read_text(encoding='utf-8')
    for dependency in ('sam_loss', 'dino_loss', 'numpy<2', 'imageio-ffmpeg', 'dearpygui'):
        assert dependency in env_text
    assert '--extra-index-url https://pypi.org/simple' in env_text

    gui_text = (root / 'integrations' / 'flexavatar' / 'source' / 'scripts' / 'run_gui.py').read_text(encoding='utf-8')
    assert "DCT_FLEXAVATAR_DEFAULT_AVATAR" in gui_text
    assert 'if not ret or frame is None' in gui_text
