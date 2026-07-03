from pathlib import Path
from zipfile import ZipFile

from fastapi.testclient import TestClient
from PIL import Image, PngImagePlugin

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths
from data_curation_tool.models.registry import ModelRegistry
from data_curation_tool.models.adapters import _parse_prediction_table


def _client(tmp_path: Path) -> TestClient:
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    return TestClient(create_app(paths))


def _write_a1111_png(path: Path) -> None:
    img = Image.new("RGB", (64, 64), (32, 48, 64))
    info = PngImagePlugin.PngInfo()
    info.add_text(
        "parameters",
        "1girl, blue hair, (smile:1.2), <lora:sample_style:0.8>\n"
        "Negative prompt: blurry, lowres\n"
        "Steps: 20, Sampler: Euler a, CFG scale: 7, Seed: 1234, Size: 512x768",
    )
    img.save(path, pnginfo=info)


def test_metadata_schema_compose_and_chat_history(tmp_path: Path):
    client = _client(tmp_path)
    image_path = tmp_path / "a1111.png"
    _write_a1111_png(image_path)

    meta = client.post("/api/metadata/path", json={"path": str(image_path), "include_raw": True}).json()
    assert meta["source_app"]
    assert "blue_hair" in meta.get("tags", []) or "blue hair" in meta.get("positive_prompt", "")

    schema = client.post("/api/media-tools/metadata/schema", json={"path": str(image_path), "include_raw": True, "max_items": 5000}).json()
    paths = [entry["path"] for entry in schema["results"][0]["schema"]["entries"]]
    assert any("positive_prompt" in p for p in paths)

    chosen = next(p for p in paths if "positive_prompt" in p)
    composed = client.post(
        "/api/media-tools/metadata/compose",
        json={"path": str(image_path), "selected_paths": [chosen], "input_delimiter": "auto", "output_delimiter": ", ", "split_to_tags": True, "keep_weight_syntax": False},
    ).json()
    tokens = composed["results"][0]["tokens"]
    assert "blue_hair" in tokens
    assert "smile" in tokens

    first = client.post(
        "/api/models/chat",
        json={
            "model_name": "dataset-assistant",
            "prompt": "Use metadata context to suggest cleanup.",
            "external_paths": [str(image_path)],
            "include_metadata_context": True,
        },
    ).json()
    assert first["conversation_id"]
    conv = client.get(f"/api/models/chat/conversations/{first['conversation_id']}").json()
    assert len(conv["messages"]) >= 2
    user_context = conv["messages"][0].get("context") or {}
    assert user_context.get("generation_metadata")
    assert user_context["generation_metadata"][0].get("positive_prompt")
    fork = client.post("/api/models/chat/conversations/fork", json={"message_id": conv["messages"][0]["id"]}).json()
    assert fork["conversation"]["id"] != first["conversation_id"]


def test_runtime_audit_and_jtp3_parser_contract(tmp_path: Path):
    registry = ModelRegistry(tmp_path / "models")
    audit = registry.runtime_audit()
    assert audit["ok"] is True
    assert audit["specialized_parsers"]["jtp3_headerless_wide_csv"] is True
    names = [f"tag_{i}" for i in range(7504)]
    parsed = _parse_prediction_table("," + ",".join("0.1" for _ in names), tag_names=names)
    assert len(parsed) == len(names)


def test_metadata_toolkit_no_legacy_ui_names_and_bridge_package(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    text_files = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".py", ".js", ".html", ".css", ".md", ".json", ".txt"}:
            if path.name == Path(__file__).name or "runtime" in path.parts or "outputs" in path.parts or "__pycache__" in path.parts:
                continue
            text_files.append(path)
    banned = ["".join(x) for x in [["K","Z"], ["K","D","Z"], ["k","z","m","t"], ["K","Z","M","T"]]]
    leaks = []
    for path in text_files:
        data = path.read_text(encoding="utf-8", errors="ignore")
        for token in banned:
            if token in data:
                leaks.append((str(path.relative_to(root)), token))
    assert not leaks
    comfy_zip = root / "integrations" / "data_curation_tool_comfyui_nodes.zip"
    assert comfy_zip.exists()
    with ZipFile(comfy_zip) as zf:
        names = zf.namelist()
        assert any(name.endswith("__init__.py") for name in names)
        for name in names:
            if name.lower().endswith((".py", ".js", ".md", ".json", ".txt")):
                content = zf.read(name).decode("utf-8", errors="ignore")
                assert not any(token in content for token in banned)
