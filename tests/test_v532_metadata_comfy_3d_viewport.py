from __future__ import annotations

import json
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.three_d_service import ThreeDService
from data_curation_tool.models.registry import ModelRegistry


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def test_comfy_bridge_is_neutral_and_serves_node_package(tmp_path: Path):
    client = _client(tmp_path)
    status = client.get("/api/comfy/status")
    assert status.status_code == 200
    assert status.json()["ok"] is True
    assert "Data Curation Tool" in status.json()["bridge_name"]

    response = client.get("/api/comfy/nodes/package")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/zip")
    assert all(token not in response.content for token in [bytes([75, 90]), bytes([75, 68, 90])])


def test_obj_viewport_payload_and_modes(tmp_path: Path):
    client = _client(tmp_path)
    obj = tmp_path / "tri.obj"
    obj.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nvt 0 0\nvt 1 0\nvt 0 1\nf 1/1 2/2 3/3\n", encoding="utf-8")
    response = client.post("/api/three-d/viewport/prepare", json={"asset_path": str(obj), "force_blender": False})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert payload["mesh_count"] == 1
    assert payload["payload"]["meshes"][0]["faces"] == [[0, 1, 2]]

    modes = client.get("/api/three-d/viewport/modes").json()
    keys = {row["key"] for row in modes}
    assert {"wireframe", "uv_topology", "normals", "material", "rendered"}.issubset(keys)


def test_model_catalog_contains_extended_3d_and_animation_entries(tmp_path: Path):
    names = {row["name"] for row in ModelRegistry(tmp_path / "models").list()}
    for expected in {
        "instantmesh-image-to-3d",
        "wonder3d-image-to-3d",
        "zero123plus-multiview",
        "sv3d-stable-video-3d",
        "hunyuan3d-25-catalog",
        "mesh-topology-inspector",
        "nonhumanoid-skeleton-contract",
        "animation-concept-dataset-tools",
    }:
        assert expected in names


def test_custom_skeleton_templates_round_trip(tmp_path: Path):
    client = _client(tmp_path)
    skeleton = {
        "key": "dragon_custom",
        "label": "Dragon Custom",
        "nodes": [
            {"id": "root", "label": "Root", "group": "body", "position": [0, 0, 0]},
            {"id": "tail", "label": "Tail", "group": "tail", "position": [0, -1, 0]},
        ],
        "edges": [{"from": "root", "to": "tail", "label": "tail spine", "group": "tail"}],
        "metadata": {"species": "non-humanoid"},
    }
    response = client.post("/api/reference/annotations/custom-skeletons", json=skeleton)
    assert response.status_code == 200, response.text
    templates = client.get("/api/reference/annotations/pose-templates").json()
    assert any(row.get("key") == "dragon_custom" for row in templates)


def test_no_legacy_node_prefix_leakage_in_generated_integrations():
    roots = [Path("data_curation_tool"), Path("integrations"), Path("docs")]
    leaked = []
    for root in roots:
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".py", ".js", ".css", ".md", ".json", ".txt", ".html"}:
                text = path.read_text(encoding="utf-8", errors="ignore")
                if any(token in text for token in [chr(75)+chr(90), chr(75)+chr(68)+chr(90), chr(75)+chr(90)+chr(77)+chr(84)]):
                    leaked.append(str(path))
    assert not leaked

    zip_path = Path("integrations/data_curation_tool_comfyui_nodes.zip")
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path) as zf:
        blob = b"".join(zf.read(name) for name in zf.namelist() if not name.endswith("/"))
    assert all(token not in blob for token in [bytes([75,90]), bytes([75,68,90]), bytes([75,90,77,84])])
