from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

from PIL import Image, PngImagePlugin
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data_curation_tool.app import create_app
from data_curation_tool.paths import AppPaths
from data_curation_tool.models.registry import ModelRegistry
from data_curation_tool.models.adapters import _parse_prediction_table


def _make_test_png(path: Path) -> None:
    img = Image.new("RGB", (48, 48), (80, 40, 120))
    info = PngImagePlugin.PngInfo()
    info.add_text("parameters", "portrait, blue hair, (smile:1.2)\nNegative prompt: blurry\nSteps: 12, Sampler: Euler, Seed: 42")
    img.save(path, pnginfo=info)


def _scan_for_legacy_names(root: Path) -> list[tuple[str, str]]:
    banned = ["".join(x) for x in [["K", "Z"], ["K", "D", "Z"], ["k", "z", "m", "t"], ["K", "Z", "M", "T"]]]
    leaks: list[tuple[str, str]] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".py", ".js", ".html", ".css", ".md", ".json", ".txt"}:
            continue
        rel_parts = set(path.relative_to(root).parts)
        if {"runtime", "outputs", "__pycache__"}.intersection(rel_parts):
            continue
        if path.name == Path(__file__).name or path.name.startswith("test_v535_"):
            continue
        data = path.read_text(encoding="utf-8", errors="ignore")
        for token in banned:
            if token in data:
                leaks.append((str(path.relative_to(root)), token))
    bridge = root / "integrations" / "data_curation_tool_comfyui_nodes.zip"
    if not bridge.exists():
        leaks.append((str(bridge.relative_to(root)), "missing"))
    else:
        with ZipFile(bridge) as zf:
            for name in zf.namelist():
                if name.lower().endswith((".py", ".js", ".md", ".json", ".txt")):
                    text = zf.read(name).decode("utf-8", errors="ignore")
                    for token in banned:
                        if token in text:
                            leaks.append((f"{bridge.name}:{name}", token))
    return leaks


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        paths = AppPaths.create(runtime=tmp / "runtime", models=tmp / "models", outputs=tmp / "outputs")
        client = TestClient(create_app(paths))
        image_path = tmp / "metadata_test.png"
        _make_test_png(image_path)
        meta = client.post("/api/metadata/path", json={"path": str(image_path), "include_raw": True}).json()
        assert meta.get("source_app"), meta
        schema = client.post("/api/media-tools/metadata/schema", json={"path": str(image_path), "include_raw": True}).json()
        entries = schema["results"][0]["schema"]["entries"]
        selected = [e["path"] for e in entries if "positive_prompt" in e["path"]][:1]
        assert selected, schema
        composed = client.post("/api/media-tools/metadata/compose", json={"path": str(image_path), "selected_paths": selected, "input_delimiter": "auto", "output_delimiter": ", ", "split_to_tags": True, "keep_weight_syntax": False}).json()
        assert "blue_hair" in composed["results"][0]["tokens"], composed
        chat = client.post("/api/models/chat", json={"model_name": "dataset-assistant", "prompt": "Summarize metadata.", "external_paths": [str(image_path)], "include_metadata_context": True}).json()
        assert chat.get("conversation_id"), chat
        conversation = client.get(f"/api/models/chat/conversations/{chat['conversation_id']}").json()
        assert conversation["messages"] and conversation["messages"][0].get("context", {}).get("generation_metadata"), conversation
        fork = client.post("/api/models/chat/conversations/fork", json={"message_id": conversation["messages"][0]["id"]}).json()
        assert fork["conversation"]["id"] != chat["conversation_id"], fork
        audit = ModelRegistry(tmp / "models").runtime_audit()
        assert audit["ok"] and audit["specialized_parsers"].get("jtp3_headerless_wide_csv"), audit
        names = [f"tag_{i}" for i in range(7504)]
        parsed = _parse_prediction_table("," + ",".join("0.1" for _ in names), tag_names=names)
        assert len(parsed) == len(names)
    leaks = _scan_for_legacy_names(ROOT)
    assert not leaks, leaks[:20]
    print(json.dumps({"ok": True, "version": "5.35", "metadata_chat_runtime_audit": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
