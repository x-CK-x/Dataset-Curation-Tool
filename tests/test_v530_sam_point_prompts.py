from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
from PIL import Image

from data_curation_tool.services import annotation_models as sam_mod


class _FakeSam:
    def __init__(self, checkpoint: str):
        self.checkpoint = checkpoint
        self.device = None

    def to(self, device: str | None = None, **_kwargs):
        self.device = device
        return self


class _FakeSamPredictor:
    calls: list[dict] = []
    invocation = 0
    return_empty = False

    def __init__(self, _model):
        pass

    def set_image(self, image):
        self.image_shape = image.shape

    def predict(self, **kwargs):
        type(self).calls.append(kwargs)
        index = type(self).invocation
        type(self).invocation += 1
        height, width = self.image_shape[:2]
        if type(self).return_empty:
            masks = np.zeros((1, height, width), dtype=bool)
            return masks, np.asarray([0.99]), np.zeros_like(masks, dtype=float)
        mask_a = np.zeros((height, width), dtype=bool)
        mask_b = np.zeros((height, width), dtype=bool)
        if index % 2 == 0:
            mask_a[1:5, 1:5] = True
            mask_b[0:2, 0:2] = True
        else:
            mask_a[5:9, 5:9] = True
            mask_b[7:9, 0:2] = True
        return np.stack([mask_a, mask_b]), np.asarray([0.95, 0.55]), np.zeros((2, height, width), dtype=float)


def _image_and_checkpoint(tmp_path: Path) -> tuple[Path, Path]:
    image = tmp_path / "source.png"
    Image.new("RGB", (10, 10), (30, 60, 90)).save(image)
    checkpoint = tmp_path / "fake.pth"
    checkpoint.write_bytes(b"fake")
    return image, checkpoint


def _patch_sam_runtime(monkeypatch):
    _FakeSamPredictor.calls = []
    _FakeSamPredictor.invocation = 0
    _FakeSamPredictor.return_empty = False
    registry = {"vit_b": lambda checkpoint: _FakeSam(checkpoint)}
    monkeypatch.setattr(
        sam_mod,
        "_load_sam_runtime",
        lambda hq=False: (object, _FakeSamPredictor, registry, "fake_segment_anything_hq" if hq else "fake_segment_anything"),
    )


def test_point_prompt_parser_uses_native_foreground_background_labels():
    coords, labels = sam_mod._point_prompt_arrays(
        {
            "point_prompts": [
                {"x": 3, "y": 4, "label": 1},
                {"x": 7, "y": 8, "positive": False},
                [12, -2, 1],
                {"x": 3, "y": 4, "label": 1},
            ],
            "positive_points": [[2, 2]],
            "negative_points": [{"x": 5, "y": 5}],
        },
        10,
        10,
    )
    assert coords == [[3.0, 4.0], [7.0, 8.0], [9.0, 0.0], [2.0, 2.0], [5.0, 5.0]]
    assert labels == [1, 0, 1, 1, 0]


def test_sam_combines_bbox_positive_negative_points_and_semantic_union(monkeypatch, tmp_path: Path):
    _patch_sam_runtime(monkeypatch)
    image, checkpoint = _image_and_checkpoint(tmp_path)
    proposals = sam_mod.propose_with_sam(
        image,
        str(checkpoint),
        model_key="sam-vit-b",
        model_type="vit_b",
        label="person",
        bbox_prompt={"x1": 0, "y1": 0, "x2": 6, "y2": 6},
        output_dir=tmp_path / "masks",
        options={
            "bbox_prompts": [{"x1": 4, "y1": 4, "x2": 9, "y2": 9}],
            "point_prompts": [{"x": 2, "y": 2, "label": 1}, {"x": 4, "y": 4, "label": 0}],
            "output_mode": "semantic_union",
            "max_proposals": 4,
            "multimask": True,
            "run_id": "sam-test",
        },
    )
    assert len(_FakeSamPredictor.calls) == 2
    for call in _FakeSamPredictor.calls:
        assert call["point_coords"].tolist() == [[2.0, 2.0], [4.0, 4.0]]
        assert call["point_labels"].tolist() == [1, 0]
        assert call["box"].shape == (4,)
    assert len(proposals) == 1
    proposal = proposals[0]
    assert proposal["annotation_type"] == "mask"
    assert proposal["metadata"]["output_mode"] == "semantic_union"
    assert proposal["metadata"]["component_count"] == 2
    assert proposal["metadata"]["conditioning"] == "bbox_and_points"
    mask = np.asarray(Image.open(proposal["mask_path"]).convert("L")) > 0
    assert mask[2, 2]
    assert mask[6, 6]


def test_sam_semantic_mode_does_not_return_raw_candidates_at_proposal_limit(monkeypatch, tmp_path: Path):
    _patch_sam_runtime(monkeypatch)
    image, checkpoint = _image_and_checkpoint(tmp_path)
    proposals = sam_mod.propose_with_sam(
        image,
        str(checkpoint),
        model_key="sam-hq-vit-b",
        model_type="vit_b",
        label="object",
        bbox_prompt={"x1": 0, "y1": 0, "x2": 9, "y2": 9},
        options={"point_prompts": [[2, 2, 1]], "output_mode": "semantic_union", "max_proposals": 1},
    )
    assert len(proposals) == 1
    assert proposals[0]["metadata"]["output_mode"] == "semantic_union"
    assert proposals[0]["metadata"]["component_count"] == 1


def test_sam_rejects_empty_predictor_masks(monkeypatch, tmp_path: Path):
    _patch_sam_runtime(monkeypatch)
    _FakeSamPredictor.return_empty = True
    image, checkpoint = _image_and_checkpoint(tmp_path)
    proposals = sam_mod.propose_with_sam(
        image,
        str(checkpoint),
        model_key="sam-vit-b",
        model_type="vit_b",
        options={"point_prompts": [[2, 2, 1]]},
    )
    assert proposals == []


def test_sam2_receives_the_same_native_point_labels(monkeypatch, tmp_path: Path):
    image, checkpoint = _image_and_checkpoint(tmp_path)
    _FakeSamPredictor.calls = []
    _FakeSamPredictor.invocation = 0
    _FakeSamPredictor.return_empty = False

    build_module = types.ModuleType("sam2.build_sam")
    build_module.build_sam2 = lambda config, checkpoint, device=None: {"config": config, "checkpoint": checkpoint, "device": device}
    predictor_module = types.ModuleType("sam2.sam2_image_predictor")
    predictor_module.SAM2ImagePredictor = _FakeSamPredictor
    package = types.ModuleType("sam2")
    package.__path__ = []
    monkeypatch.setitem(sys.modules, "sam2", package)
    monkeypatch.setitem(sys.modules, "sam2.build_sam", build_module)
    monkeypatch.setitem(sys.modules, "sam2.sam2_image_predictor", predictor_module)

    proposals = sam_mod.propose_with_sam2(
        image,
        str(checkpoint),
        model_key="sam2.1-hiera-small",
        label="subject",
        bbox_prompt={"x1": 1, "y1": 1, "x2": 8, "y2": 8},
        options={
            "point_prompts": [{"x": 2, "y": 3, "label": 1}, {"x": 7, "y": 7, "label": 0}],
            "output_mode": "instance",
            "max_proposals": 2,
        },
    )
    assert len(proposals) == 2
    call = _FakeSamPredictor.calls[0]
    assert call["point_labels"].tolist() == [1, 0]
    assert call["point_coords"].tolist() == [[2.0, 3.0], [7.0, 7.0]]
    assert call["box"].tolist() == [1.0, 1.0, 8.0, 8.0]
    assert all(row["metadata"]["conditioning"] == "bbox_and_points" for row in proposals)


def test_frontend_exposes_sam_setup_point_tools_and_output_modes():
    source = (Path(__file__).resolve().parents[1] / "data_curation_tool" / "static" / "app.js").read_text(encoding="utf-8")
    for text in (
        "Set Up Runtime + Weights + Load",
        "Positive Point (+ Include)",
        "Negative Point (− Exclude)",
        "Undo Last Point",
        "Clear Positive",
        "Clear Negative",
        "Instance masks — separate candidate layers",
        "Semantic class mask — union best prompted instances",
        "point_prompts",
        "output_mode",
    ):
        assert text in source
