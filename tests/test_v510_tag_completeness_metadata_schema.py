import csv
import json
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image, PngImagePlugin

from data_curation_tool.app import create_app
from data_curation_tool.database import Database
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.tag_service import TagService


def test_v510_dictionary_import_keeps_zero_count_tags(tmp_path: Path):
    paths = AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")
    db = Database(paths.database)
    tags = TagService(db, paths)
    csv_path = tmp_path / "tags.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "category", "post_count"])
        writer.writerow([1, "active_character", 4, 123])
        writer.writerow([2, "zero_count_character", 4, 0])
        writer.writerow([3, "zero_count_artist", 1, 0])
    count = tags.import_dictionary_csv(csv_path, profile_key="e621", replace_existing=True)
    assert count == 3
    assert tags.metadata(["zero_count_character"], "e621")["zero_count_character"]["known"] is True
    assert tags.metadata(["zero_count_character"], "e621")["zero_count_character"]["category"] == "character"
    assert any(item["tag"] == "zero_count_character" for item in tags.suggest("zero_count", profile_key="e621", limit=10))


def test_v510_metadata_schema_parses_nested_json_and_composes_wrapped_tokens(tmp_path: Path):
    image_path = tmp_path / "schema.png"
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text(
        "workflow",
        json.dumps({"nodes": [{"inputs": {"text": "(blue hair:1.2), {solo}, [smile]"}}]}),
    )
    Image.new("RGB", (16, 16), (1, 2, 3)).save(image_path, pnginfo=metadata)
    client = TestClient(create_app(AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")))
    schema = client.post("/api/media-tools/metadata/schema", json={"path": str(image_path), "include_raw": True}).json()
    entries = schema["results"][0]["schema"]["entries"]
    selected_path = "$.raw.pil_info.workflow::<json>.nodes[0].inputs.text"
    assert any(entry["path"] == selected_path for entry in entries)
    composed = client.post(
        "/api/media-tools/metadata/compose",
        json={
            "path": str(image_path),
            "selected_paths": [selected_path],
            "input_delimiter": "auto",
            "output_delimiter": " | ",
            "split_to_tags": True,
            "keep_parentheses": False,
            "keep_curly_braces": False,
            "keep_square_brackets": False,
            "keep_weight_syntax": False,
        },
    ).json()
    result = composed["results"][0]
    assert result["tokens"] == ["blue_hair", "solo", "smile"]
    assert result["text"] == "blue_hair | solo | smile"
    assert result["token_analysis"][0]["has_parentheses"] is True
    assert result["token_analysis"][1]["has_curly_braces"] is True
