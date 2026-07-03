from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_curation_tool.models.adapters import _parse_prediction_table


def main() -> None:
    tags = [f"tag_{i}" for i in range(7504)]
    scores = ["0.0000"] * 7504
    scores[10] = "0.7746"
    scores[100] = "0.9999"
    parsed = _parse_prediction_table("," + ",".join(scores) + "\n", tag_names=tags)
    assert len(parsed) == 7504, len(parsed)
    assert parsed[10] == ("tag_10", 0.7746)
    assert parsed[100] == ("tag_100", 0.9999)
    blender_script = Path("integrations/blender_scripts/dct_export_viewer_payload.py").read_text(encoding="utf-8")
    assert "mesh.calc_normals()" not in blender_script
    assert "calc_loop_triangles()" in blender_script
    app_js = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "if (name === 'redrocket-jtp-3') return 'tag';" in app_js
    assert "Quick Tag / Rating Model for This Image', getMediaIds: () => [item.id], afterQueue" not in app_js
    print("v5.34 runtime fixes verified")


if __name__ == "__main__":
    main()
