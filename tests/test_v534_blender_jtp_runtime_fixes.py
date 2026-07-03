from pathlib import Path

from data_curation_tool.models.adapters import _parse_prediction_table


def test_jtp3_headerless_score_row_maps_to_metadata_tags():
    tags = ["tag_a", "tag_b", "rating_safe", "tag_c"]
    parsed = _parse_prediction_table(",0.12,0.88,0.95,0.04\n", tag_names=tags)
    assert parsed == [("tag_a", 0.12), ("tag_b", 0.88), ("rating_safe", 0.95), ("tag_c", 0.04)]


def test_jtp3_filename_score_row_maps_to_metadata_tags():
    tags = ["alpha", "beta", "gamma"]
    parsed = _parse_prediction_table("C:/dataset/image.jpg,0.1,0.2,0.3\n", tag_names=tags)
    assert parsed == [("alpha", 0.1), ("beta", 0.2), ("gamma", 0.3)]


def test_blender_viewport_exporter_is_blender5_safe():
    script = Path("integrations/blender_scripts/dct_export_viewer_payload.py").read_text(encoding="utf-8")
    assert "calc_normals()" not in script
    assert "calc_loop_triangles()" in script
