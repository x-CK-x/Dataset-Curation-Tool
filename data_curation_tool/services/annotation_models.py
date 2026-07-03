from __future__ import annotations

import json
import math
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageDraw

from .annotation_classes import inspect_model_classes, resolve_class_query


class AnnotationModelError(RuntimeError):
    """Raised when an annotation model cannot be used with the current install."""


@dataclass
class AnnotationProposal:
    label: str
    annotation_type: str
    bbox: dict[str, float]
    polygon: list[list[float]]
    confidence: float
    source: str
    model_key: str
    mask_path: str = ""
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "annotation_type": self.annotation_type,
            "bbox": self.bbox,
            "polygon": self.polygon,
            "confidence": float(self.confidence),
            "source": self.source,
            "model_key": self.model_key,
            "mask_path": self.mask_path,
            "metadata": self.metadata or {},
        }


def normalize_bbox_xyxy(x1: float, y1: float, x2: float, y2: float, width: int | None = None, height: int | None = None) -> dict[str, float]:
    width = int(width or 0)
    height = int(height or 0)
    lo_x, hi_x = sorted((float(x1), float(x2)))
    lo_y, hi_y = sorted((float(y1), float(y2)))
    if width > 0:
        lo_x = max(0.0, min(float(width), lo_x)); hi_x = max(0.0, min(float(width), hi_x))
    if height > 0:
        lo_y = max(0.0, min(float(height), lo_y)); hi_y = max(0.0, min(float(height), hi_y))
    return {"x1": lo_x, "y1": lo_y, "x2": hi_x, "y2": hi_y}


def bbox_from_xywh(x: float, y: float, w: float, h: float, width: int | None = None, height: int | None = None) -> dict[str, float]:
    return normalize_bbox_xyxy(float(x), float(y), float(x) + float(w), float(y) + float(h), width, height)


def bbox_from_polygon(points: Iterable[Iterable[float]], width: int | None = None, height: int | None = None) -> dict[str, float]:
    pts = [(float(p[0]), float(p[1])) for p in points if len(list(p)) >= 2]
    if not pts:
        return normalize_bbox_xyxy(0, 0, width or 0, height or 0, width, height)
    xs, ys = zip(*pts)
    return normalize_bbox_xyxy(min(xs), min(ys), max(xs), max(ys), width, height)


def center_fallback(image_path: str | Path, label: str, model_key: str, threshold: float = 0.25, annotation_type: str = "bbox") -> list[dict[str, Any]]:
    with Image.open(image_path) as im:
        w, h = im.size
    bbox = normalize_bbox_xyxy(w * 0.18, h * 0.12, w * 0.82, h * 0.88, w, h)
    return [AnnotationProposal(
        label=label or "object",
        annotation_type="bbox_mask" if "mask" in annotation_type else annotation_type,
        bbox=bbox,
        polygon=[],
        confidence=max(float(threshold or 0.25), 0.25),
        source="fallback",
        model_key=model_key or "demo_center_bbox",
        metadata={"fallback": True, "reason": "No model-backed annotation adapter was selected."},
    ).to_dict()]


def _safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text or "annotation").strip("_") or "annotation"


def _save_polygon_mask(image_path: str | Path, polygon: list[list[float]], out_dir: Path, stem: str) -> str:
    with Image.open(image_path) as im:
        w, h = im.size
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{_safe_name(stem)}.png"
    mask = Image.new("L", (w, h), 0)
    if polygon:
        ImageDraw.Draw(mask).polygon([(float(x), float(y)) for x, y in polygon], fill=255)
    mask.save(out)
    return str(out)


def _save_bool_mask(mask: Any, out_dir: Path, stem: str) -> str:
    import numpy as np
    try:
        if hasattr(mask, "detach"):
            mask = mask.detach()
        if hasattr(mask, "cpu"):
            mask = mask.cpu()
        if hasattr(mask, "numpy"):
            mask = mask.numpy()
    except Exception:
        pass
    arr = np.asarray(mask)
    if arr.ndim > 2:
        arr = arr.squeeze()
    arr = (arr > 0).astype("uint8") * 255
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{_safe_name(stem)}.png"
    Image.fromarray(arr, mode="L").save(out)
    return str(out)


def _tensor_to_list(value: Any) -> Any:
    try:
        if hasattr(value, "detach"):
            value = value.detach()
        if hasattr(value, "cpu"):
            value = value.cpu()
        if hasattr(value, "numpy"):
            value = value.numpy()
        if hasattr(value, "tolist"):
            return value.tolist()
    except Exception:
        pass
    return value


def propose_with_yolo(
    image_path: str | Path,
    model_path: str,
    *,
    model_key: str,
    label: str = "object",
    threshold: float = 0.25,
    annotation_type: str = "bbox",
    device: str = "auto",
    output_dir: str | Path | None = None,
    options: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Run an Ultralytics YOLO-family model and normalize boxes/masks/keypoints.

    Supports official/custom detection, segmentation, pose and OBB checkpoints as
    long as ``ultralytics.YOLO(model_path)`` can load them.
    """
    try:
        from ultralytics import YOLO
    except Exception as exc:
        raise AnnotationModelError("Ultralytics is not installed. Run install_annotation_models.bat or pip install ultralytics.") from exc

    options = dict(options or {})
    with Image.open(image_path) as im:
        width, height = im.size
    model = YOLO(str(model_path))
    max_props = max(1, int(options.get("max_proposals") or options.get("max_det") or 100))
    class_query = str(options.get("class_query") or options.get("class_token") or "").strip()
    class_info = inspect_model_classes(
        model_path,
        model_key=model_key,
        provider="ultralytics",
        capabilities={"yolo", "detect", "segment"},
        custom_model_type=str(options.get("custom_model_type") or "yolo"),
        allow_runtime_load=False,
    )
    # The just-loaded model is authoritative and avoids another checkpoint load.
    model_names = getattr(model, "names", {}) or {}
    runtime_classes = []
    if isinstance(model_names, dict):
        runtime_classes = [{"id": int(idx), "name": str(name)} for idx, name in model_names.items()]
    elif isinstance(model_names, (list, tuple)):
        runtime_classes = [{"id": idx, "name": str(name)} for idx, name in enumerate(model_names)]
    if runtime_classes:
        class_info = class_info | {
            "mode": "closed_set",
            "classes": runtime_classes,
            "class_count": len(runtime_classes),
            "source": "ultralytics_model.names",
            "prompt_affects_geometry": True,
        }
    class_resolution = resolve_class_query(class_info.get("classes") or [], class_query)
    if class_query and not class_resolution.get("all_classes"):
        if class_resolution.get("missing"):
            suggestions = ", ".join(class_resolution.get("suggestions") or []) or "none"
            available_preview = ", ".join(str(row.get("name")) for row in (class_info.get("classes") or [])[:30])
            raise AnnotationModelError(
                f"Class token(s) not supported by {model_key}: {', '.join(class_resolution['missing'])}. "
                f"Closest classes: {suggestions}. Available examples: {available_preview or 'class metadata unavailable'}."
            )
        if not class_resolution.get("class_ids"):
            raise AnnotationModelError(
                f"Class token {class_query!r} did not resolve to a model class. Inspect the model class list before running inference."
            )
    predict_kwargs: dict[str, Any] = {
        "source": str(image_path),
        "conf": float(threshold if threshold is not None else 0.25),
        "verbose": False,
        "max_det": max_props,
    }
    if options.get("imgsz"):
        predict_kwargs["imgsz"] = int(options["imgsz"])
    if options.get("iou") is not None:
        predict_kwargs["iou"] = float(options["iou"])
    if class_resolution.get("class_ids"):
        predict_kwargs["classes"] = list(class_resolution["class_ids"])
    if options.get("agnostic_nms") is not None:
        predict_kwargs["agnostic_nms"] = bool(options.get("agnostic_nms"))
    if options.get("augment") is not None:
        predict_kwargs["augment"] = bool(options.get("augment"))
    if options.get("retina_masks") is not None:
        predict_kwargs["retina_masks"] = bool(options.get("retina_masks"))
    if options.get("half") is not None:
        predict_kwargs["half"] = bool(options.get("half"))
    if device and device not in {"auto", "cpu", "cuda"}:
        predict_kwargs["device"] = device.replace("cuda:", "")
    elif device == "cpu":
        predict_kwargs["device"] = "cpu"
    results = model.predict(**predict_kwargs)
    proposals: list[dict[str, Any]] = []
    out_dir = Path(output_dir) if output_dir else None
    names = getattr(model, "names", {}) or {}
    run_id = _safe_name(str(options.get("run_id") or uuid.uuid4().hex[:12]))
    annotation_label = str(options.get("annotation_label") or "").strip()
    for result_index, result in enumerate(results or []):
        boxes_obj = getattr(result, "boxes", None)
        masks_obj = getattr(result, "masks", None)
        kpts_obj = getattr(result, "keypoints", None)
        xyxy = _tensor_to_list(getattr(boxes_obj, "xyxy", [])) if boxes_obj is not None else []
        confs = _tensor_to_list(getattr(boxes_obj, "conf", [])) if boxes_obj is not None else []
        clss = _tensor_to_list(getattr(boxes_obj, "cls", [])) if boxes_obj is not None else []
        mask_polys = _tensor_to_list(getattr(masks_obj, "xy", [])) if masks_obj is not None else []
        keypoints = _tensor_to_list(getattr(kpts_obj, "xy", [])) if kpts_obj is not None else []
        keypoint_conf = _tensor_to_list(getattr(kpts_obj, "conf", [])) if kpts_obj is not None else []
        count = max(len(xyxy or []), len(mask_polys or []), len(keypoints or []), 0)
        applied_class_ids = {int(value) for value in (class_resolution.get("class_ids") or [])}
        for i in range(count):
            cls_id = int(float(clss[i])) if i < len(clss or []) else None
            # Keep the adapter correct even when a third-party/exported backend
            # ignores the runtime ``classes`` argument.
            if applied_class_ids and cls_id not in applied_class_ids:
                continue
            cls_name = str(names.get(cls_id, label) if isinstance(names, dict) else label)
            # Preserve the checkpoint's true class label unless the user supplied
            # a separate annotation label. The previous code renamed every result
            # to the typed token even when that token was never used by inference.
            out_label = annotation_label or cls_name or label or "object"
            conf = float(confs[i]) if i < len(confs or []) else float(threshold if threshold is not None else 0.25)
            box = normalize_bbox_xyxy(0, 0, width, height, width, height)
            if i < len(xyxy or []):
                vals = xyxy[i]
                if vals and len(vals) >= 4:
                    box = normalize_bbox_xyxy(vals[0], vals[1], vals[2], vals[3], width, height)
            polygon: list[list[float]] = []
            mask_path = ""
            # Normalize mask polygons from Ultralytics.
            if i < len(mask_polys or []) and mask_polys[i] is not None:
                polygon = []
                for p in mask_polys[i]:
                    try:
                        polygon.append([float(p[0]), float(p[1])])
                    except Exception:
                        pass
                if polygon:
                    box = bbox_from_polygon(polygon, width, height)
                    if out_dir and ("mask" in annotation_type or "seg" in annotation_type or "pose" not in annotation_type):
                        mask_path = _save_polygon_mask(image_path, polygon, out_dir, f"{Path(image_path).stem}_{model_key}_{run_id}_{result_index}_{i}")
            metadata: dict[str, Any] = {
                "class_id": cls_id,
                "class_name": cls_name,
                "result_index": result_index,
                "requested_class_query": class_query,
                "applied_class_ids": class_resolution.get("class_ids") or [],
                "matched_classes": class_resolution.get("matches") or [],
                "model_class_count": class_info.get("class_count"),
                "class_source": class_info.get("source"),
                "inference_options": {
                    "conf": predict_kwargs.get("conf"),
                    "iou": predict_kwargs.get("iou"),
                    "max_det": predict_kwargs.get("max_det"),
                    "classes": predict_kwargs.get("classes"),
                    "agnostic_nms": predict_kwargs.get("agnostic_nms", False),
                    "augment": predict_kwargs.get("augment", False),
                    "retina_masks": predict_kwargs.get("retina_masks", False),
                },
                "run_id": run_id,
            }
            ann_type = annotation_type
            if keypoints and i < len(keypoints or []):
                pts = []
                for p in keypoints[i] or []:
                    try:
                        pts.append({"x": float(p[0]), "y": float(p[1])})
                    except Exception:
                        pass
                metadata["keypoints_2d"] = pts
                if keypoint_conf and i < len(keypoint_conf or []):
                    metadata["keypoint_confidence"] = keypoint_conf[i]
                ann_type = "pose2d"
            elif polygon and ("mask" in annotation_type or "segment" in annotation_type or model_key.endswith("seg")):
                ann_type = "mask"
            elif "mask" in annotation_type:
                ann_type = "bbox_mask"
            proposals.append(AnnotationProposal(out_label, ann_type, box, polygon, conf, "model", model_key, mask_path, metadata).to_dict())
            if len(proposals) >= max_props:
                return proposals
    return proposals


def _torch_device_arg(device: str = "auto") -> str:
    if device == "cpu":
        return "cpu"
    if device and device not in {"auto", "cuda"}:
        return device
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _load_sam_runtime(*, hq: bool = False):
    """Return SAM runtime classes for vanilla SAM or SAM-HQ.

    SAM-HQ intentionally uses its own package when available. A vanilla SAM
    runtime can import the HQ checkpoint name but cannot reliably load HQ weights,
    which is the failure mode this helper avoids.
    """
    if hq:
        try:
            from segment_anything_hq import SamAutomaticMaskGenerator, SamPredictor, sam_model_registry
            return SamAutomaticMaskGenerator, SamPredictor, sam_model_registry, "segment_anything_hq"
        except Exception as exc:
            raise AnnotationModelError(
                "SAM-HQ runtime is not installed. Run the Segmentation & Masks dependency installer, "
                "or run: pip install segment-anything-hq"
            ) from exc
    try:
        from segment_anything import SamAutomaticMaskGenerator, SamPredictor, sam_model_registry
        return SamAutomaticMaskGenerator, SamPredictor, sam_model_registry, "segment_anything"
    except Exception as exc:
        raise AnnotationModelError(
            "segment-anything is not installed. Run install_annotation_models.bat or pip install git+https://github.com/facebookresearch/segment-anything.git."
        ) from exc


def _bbox_prompt_to_xyxy(prompt: dict[str, Any] | None, width: int, height: int) -> list[float] | None:
    if not prompt or not any(key in prompt for key in ("x1", "x", "xyxy")):
        return None
    if prompt.get("xyxy"):
        values = [float(value) for value in prompt["xyxy"][:4]]
    else:
        x1 = float(prompt.get("x1", prompt.get("x", 0)))
        y1 = float(prompt.get("y1", prompt.get("y", 0)))
        x2 = float(prompt.get("x2", x1 + float(prompt.get("w", width))))
        y2 = float(prompt.get("y2", y1 + float(prompt.get("h", height))))
        values = [x1, y1, x2, y2]
    normalized = normalize_bbox_xyxy(*values, width, height)
    return [normalized["x1"], normalized["y1"], normalized["x2"], normalized["y2"]]


def _bbox_prompt_list(
    bbox_prompt: dict[str, Any] | None,
    options: dict[str, Any],
    width: int,
    height: int,
) -> list[list[float]]:
    prompts: list[dict[str, Any]] = []
    if bbox_prompt:
        prompts.append(bbox_prompt)
    for item in options.get("bbox_prompts") or []:
        if isinstance(item, dict):
            prompts.append(item)
    boxes = []
    seen = set()
    for prompt in prompts:
        box = _bbox_prompt_to_xyxy(prompt, width, height)
        if not box:
            continue
        key = tuple(round(value, 3) for value in box)
        if key in seen:
            continue
        seen.add(key)
        boxes.append(box)
    return boxes


def _point_prompt_arrays(
    options: dict[str, Any],
    width: int,
    height: int,
) -> tuple[list[list[float]], list[int]]:
    """Normalize SAM-family positive/negative point prompts.

    The UI sends ``point_prompts`` as dictionaries with x/y plus either
    ``label`` (1 foreground, 0 background) or ``positive``.  The parser also
    accepts compact ``[x, y, label]`` rows and the older positive_points /
    negative_points split so API callers can use the same inference path.
    Invalid and duplicate points are ignored rather than reaching a predictor
    with malformed arrays.
    """
    rows: list[tuple[Any, int]] = []
    for item in options.get("point_prompts") or []:
        if isinstance(item, dict):
            raw_label = item.get("label")
            if raw_label is None:
                raw_label = 1 if item.get("positive", True) else 0
            rows.append((item, 1 if int(raw_label) > 0 else 0))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            raw_label = item[2] if len(item) >= 3 else 1
            rows.append((item, 1 if int(raw_label) > 0 else 0))
    for key, label in (("positive_points", 1), ("negative_points", 0)):
        for item in options.get(key) or []:
            rows.append((item, label))

    coords: list[list[float]] = []
    labels: list[int] = []
    seen: set[tuple[float, float, int]] = set()
    for item, label in rows:
        try:
            if isinstance(item, dict):
                x = float(item.get("x"))
                y = float(item.get("y"))
            else:
                x = float(item[0])
                y = float(item[1])
        except (TypeError, ValueError, IndexError):
            continue
        if not math.isfinite(x) or not math.isfinite(y):
            continue
        x = max(0.0, min(float(max(0, width - 1)), x))
        y = max(0.0, min(float(max(0, height - 1)), y))
        key = (round(x, 3), round(y, 3), int(label))
        if key in seen:
            continue
        seen.add(key)
        coords.append([x, y])
        labels.append(int(label))
    return coords, labels


def _prompt_conditioning(box: list[float] | None, point_labels: list[int]) -> str:
    if box and point_labels:
        return "bbox_and_points"
    if point_labels:
        return "positive_negative_points"
    return "bbox_prompt"


def _semantic_union_proposal(
    candidates_by_prompt: list[list[tuple[dict[str, Any], Any]]],
    *,
    image_path: str | Path,
    model_key: str,
    label: str,
    width: int,
    height: int,
    out_dir: Path | None,
    run_id: str,
    metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    """Union the best real candidate from each prompt into one class layer."""
    import numpy as np

    selected: list[tuple[dict[str, Any], Any]] = []
    for group in candidates_by_prompt:
        if group:
            selected.append(max(group, key=lambda row: float(row[0].get("confidence") or 0.0)))
    if not selected:
        return []
    union = np.zeros((height, width), dtype=bool)
    scores: list[float] = []
    source_prompts: list[dict[str, Any]] = []
    for proposal, mask in selected:
        arr = np.asarray(mask).squeeze().astype(bool)
        if arr.shape != union.shape or not arr.any():
            continue
        union |= arr
        scores.append(float(proposal.get("confidence") or 0.0))
        source_prompts.append(dict((proposal.get("metadata") or {}).get("prompt") or {}))
    if not union.any():
        return []
    ys, xs = np.where(union)
    bbox = normalize_bbox_xyxy(float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max()), width, height)
    mask_path = _save_bool_mask(union, out_dir, f"{Path(image_path).stem}_{model_key}_{run_id}_semantic_union") if out_dir else ""
    proposal = AnnotationProposal(
        label,
        "mask",
        bbox,
        [],
        sum(scores) / max(1, len(scores)),
        "model",
        model_key,
        mask_path,
        metadata | {
            "output_mode": "semantic_union",
            "component_count": len(scores),
            "source_prompts": source_prompts,
            "run_id": run_id,
        },
    )
    return [proposal.to_dict()]


def propose_with_sam(
    image_path: str | Path,
    checkpoint_path: str,
    *,
    model_key: str,
    model_type: str,
    label: str = "object",
    threshold: float = 0.0,
    annotation_type: str = "mask",
    bbox_prompt: dict[str, Any] | None = None,
    device: str = "auto",
    output_dir: str | Path | None = None,
    options: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    import numpy as np
    options = dict(options or {})
    hq = bool(options.get("hq_sam") or model_key.startswith("sam-hq-") or options.get("custom_model_type") == "sam_hq")
    SamAutomaticMaskGenerator, SamPredictor, sam_model_registry, runtime_name = _load_sam_runtime(hq=hq)
    checkpoint = Path(str(checkpoint_path or "")).expanduser()
    if not checkpoint.exists():
        raise AnnotationModelError(f"SAM checkpoint was not found: {checkpoint or checkpoint_path}. Download the selected weights or provide a valid local checkpoint path.")
    with Image.open(image_path).convert("RGB") as im:
        image = np.asarray(im)
        width, height = im.size
    key = model_type or options.get("sam_model_type") or "vit_b"
    if key not in sam_model_registry:
        key = {
            "sam-vit-b": "vit_b", "sam-vit-l": "vit_l", "sam-vit-h": "vit_h",
            "sam-hq-vit-b": "vit_b", "sam-hq-vit-l": "vit_l", "sam-hq-vit-h": "vit_h",
        }.get(model_key, key)
    if key not in sam_model_registry:
        raise AnnotationModelError(f"SAM runtime {runtime_name} does not expose model type {key!r}. Available types: {sorted(sam_model_registry.keys())}")
    sam = sam_model_registry[key](checkpoint=str(checkpoint))
    dev = _torch_device_arg(device)
    try:
        sam.to(device=dev)
    except Exception:
        if dev != "cpu":
            sam.to(device="cpu")
    out_dir = Path(output_dir) if output_dir else None
    proposals: list[dict[str, Any]] = []
    max_props = max(1, int(options.get("max_proposals") or 32))
    run_id = _safe_name(str(options.get("run_id") or uuid.uuid4().hex[:12]))
    prompt_boxes = _bbox_prompt_list(bbox_prompt, options, width, height)
    point_coords, point_labels = _point_prompt_arrays(options, width, height)
    if prompt_boxes or point_coords:
        predictor = SamPredictor(sam)
        predictor.set_image(image)
        prompt_groups: list[list[float] | None] = prompt_boxes or [None]
        candidates_by_prompt: list[list[tuple[dict[str, Any], Any]]] = []
        semantic_union = str(options.get("output_mode") or "instance").lower() in {"semantic", "semantic_union", "class_union"}
        limit_reached = False
        for prompt_index, box in enumerate(prompt_groups):
            predict_kwargs: dict[str, Any] = {
                "multimask_output": bool(options.get("multimask", True)),
            }
            if box is not None:
                predict_kwargs["box"] = np.array(box)
            if point_coords:
                predict_kwargs["point_coords"] = np.asarray(point_coords, dtype=np.float32)
                predict_kwargs["point_labels"] = np.asarray(point_labels, dtype=np.int32)
            masks, scores, _ = predictor.predict(**predict_kwargs)
            group: list[tuple[dict[str, Any], Any]] = []
            for candidate_index, mask in enumerate(masks):
                if len(proposals) >= max_props:
                    limit_reached = True
                    break
                score = float(scores[candidate_index]) if candidate_index < len(scores) else 0.0
                if threshold is not None and score < float(threshold):
                    continue
                mask_array = np.asarray(mask).squeeze().astype(bool)
                if mask_array.shape != (height, width) or not mask_array.any():
                    continue
                mask_path = _save_bool_mask(
                    mask_array,
                    out_dir,
                    f"{Path(image_path).stem}_{model_key}_{run_id}_p{prompt_index}_m{candidate_index}",
                ) if out_dir else ""
                ys, xs = np.where(mask_array)
                proposal = AnnotationProposal(
                    label,
                    "mask",
                    normalize_bbox_xyxy(float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max()), width, height),
                    [],
                    score,
                    "model",
                    model_key,
                    mask_path,
                    {
                        "sam_model_type": key,
                        "runtime": runtime_name,
                        "prompt_bbox": box,
                        "point_coords": point_coords,
                        "point_labels": point_labels,
                        "prompt_index": prompt_index,
                        "candidate_index": candidate_index,
                        "run_id": run_id,
                        "conditioning": _prompt_conditioning(box, point_labels),
                        "prompt": {
                            "bbox": box,
                            "points": [
                                {"x": coords[0], "y": coords[1], "label": point_labels[index]}
                                for index, coords in enumerate(point_coords)
                            ],
                        },
                    },
                ).to_dict()
                proposals.append(proposal)
                group.append((proposal, mask_array))
            candidates_by_prompt.append(group)
            if limit_reached:
                break
        if semantic_union:
            return _semantic_union_proposal(
                candidates_by_prompt,
                image_path=image_path,
                model_key=model_key,
                label=label,
                width=width,
                height=height,
                out_dir=out_dir,
                run_id=run_id,
                metadata={
                    "sam_model_type": key,
                    "runtime": runtime_name,
                    "conditioning": _prompt_conditioning(prompt_groups[0], point_labels),
                },
            )
        return proposals
    generator_kwargs: dict[str, Any] = {
        "points_per_side": int(options.get("points_per_side") or 32),
        "pred_iou_thresh": float(options.get("pred_iou_thresh") if options.get("pred_iou_thresh") is not None else max(float(threshold or 0.0), 0.0) or 0.88),
        "stability_score_thresh": float(options.get("stability_score_thresh") if options.get("stability_score_thresh") is not None else 0.95),
        "min_mask_region_area": int(options.get("min_mask_region_area") or 0),
        "box_nms_thresh": float(options.get("box_nms_thresh") if options.get("box_nms_thresh") is not None else 0.7),
        "crop_n_layers": int(options.get("crop_n_layers") or 0),
        "crop_n_points_downscale_factor": int(options.get("crop_n_points_downscale_factor") or 1),
    }
    generator = SamAutomaticMaskGenerator(sam, **generator_kwargs)
    masks = generator.generate(image)
    masks = sorted(masks, key=lambda m: float(m.get("predicted_iou") or 0), reverse=True)[:max_props]
    for i, m in enumerate(masks):
        bbox = bbox_from_xywh(*(m.get("bbox") or [0, 0, width, height]), width, height)
        score = float(m.get("predicted_iou") or m.get("stability_score") or 0)
        mask_path = _save_bool_mask(m.get("segmentation"), out_dir, f"{Path(image_path).stem}_{model_key}_{run_id}_auto_{i}") if out_dir and m.get("segmentation") is not None else ""
        proposals.append(AnnotationProposal(label, "mask", bbox, [], score, "model", model_key, mask_path, {
            "sam_model_type": key,
            "runtime": runtime_name,
            "area": m.get("area"),
            "stability_score": m.get("stability_score"),
            "run_id": run_id,
            "conditioning": "automatic_class_agnostic",
            "generator_options": generator_kwargs,
        }).to_dict())
    return proposals


def _sam2_config_for_model(model_key: str, options: dict[str, Any] | None = None) -> str:
    opts = dict(options or {})
    if opts.get("sam2_config"):
        return str(opts["sam2_config"])
    key = (model_key or "").lower()
    if "tiny" in key:
        return "configs/sam2.1/sam2.1_hiera_t.yaml"
    if "small" in key:
        return "configs/sam2.1/sam2.1_hiera_s.yaml"
    if "base" in key:
        return "configs/sam2.1/sam2.1_hiera_b+.yaml"
    return "configs/sam2.1/sam2.1_hiera_l.yaml"


def propose_with_sam2(
    image_path: str | Path,
    checkpoint_path: str,
    *,
    model_key: str,
    label: str = "object",
    threshold: float = 0.0,
    annotation_type: str = "mask",
    bbox_prompt: dict[str, Any] | None = None,
    device: str = "auto",
    output_dir: str | Path | None = None,
    options: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Run SAM2.1 image segmentation when the optional sam2 runtime is installed."""
    import numpy as np
    options = dict(options or {})
    checkpoint = Path(str(checkpoint_path or "")).expanduser()
    if not checkpoint.exists():
        raise AnnotationModelError(f"SAM2 checkpoint was not found: {checkpoint or checkpoint_path}. Download the selected SAM2.1 weights first.")
    try:
        import torch
        from sam2.build_sam import build_sam2
        from sam2.sam2_image_predictor import SAM2ImagePredictor
    except Exception as exc:
        raise AnnotationModelError(
            "SAM2 runtime is not installed. Use 'Install + SAM2 Deps' in Segmentation & Masks, or install from https://github.com/facebookresearch/sam2."
        ) from exc
    with Image.open(image_path).convert("RGB") as im:
        image = np.asarray(im)
        width, height = im.size
    model_cfg = _sam2_config_for_model(model_key, options)
    dev = _torch_device_arg(device)
    model = build_sam2(model_cfg, str(checkpoint), device=dev if dev != "cpu" else "cpu")
    predictor = SAM2ImagePredictor(model)
    proposals: list[dict[str, Any]] = []
    out_dir = Path(output_dir) if output_dir else None
    max_props = max(1, int(options.get("max_proposals") or 16))
    run_id = _safe_name(str(options.get("run_id") or uuid.uuid4().hex[:12]))
    prompt_boxes = _bbox_prompt_list(bbox_prompt, options, width, height)
    point_coords, point_labels = _point_prompt_arrays(options, width, height)
    if prompt_boxes or point_coords:
        with torch.inference_mode():
            predictor.set_image(image)
        prompt_groups: list[list[float] | None] = prompt_boxes or [None]
        candidates_by_prompt: list[list[tuple[dict[str, Any], Any]]] = []
        semantic_union = str(options.get("output_mode") or "instance").lower() in {"semantic", "semantic_union", "class_union"}
        limit_reached = False
        for prompt_index, box in enumerate(prompt_groups):
            predict_kwargs: dict[str, Any] = {
                "multimask_output": bool(options.get("multimask", True)),
            }
            if box is not None:
                predict_kwargs["box"] = np.asarray(box)
            if point_coords:
                predict_kwargs["point_coords"] = np.asarray(point_coords, dtype=np.float32)
                predict_kwargs["point_labels"] = np.asarray(point_labels, dtype=np.int32)
            with torch.inference_mode():
                masks, scores, _ = predictor.predict(**predict_kwargs)
            group: list[tuple[dict[str, Any], Any]] = []
            for candidate_index, mask in enumerate(masks):
                if len(proposals) >= max_props:
                    limit_reached = True
                    break
                score = float(scores[candidate_index]) if candidate_index < len(scores) else 0.0
                if threshold is not None and score < float(threshold):
                    continue
                arr = np.asarray(mask).squeeze().astype(bool)
                if arr.shape != (height, width) or not arr.any():
                    continue
                mask_path = _save_bool_mask(arr, out_dir, f"{Path(image_path).stem}_{model_key}_{run_id}_p{prompt_index}_m{candidate_index}") if out_dir else ""
                ys, xs = np.where(arr)
                proposal = AnnotationProposal(label, "mask", normalize_bbox_xyxy(float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max()), width, height), [], score, "model", model_key, mask_path, {
                    "sam2_config": model_cfg,
                    "prompt_bbox": box,
                    "point_coords": point_coords,
                    "point_labels": point_labels,
                    "prompt_index": prompt_index,
                    "candidate_index": candidate_index,
                    "run_id": run_id,
                    "conditioning": _prompt_conditioning(box, point_labels),
                    "prompt": {
                        "bbox": box,
                        "points": [
                            {"x": coords[0], "y": coords[1], "label": point_labels[index]}
                            for index, coords in enumerate(point_coords)
                        ],
                    },
                }).to_dict()
                proposals.append(proposal)
                group.append((proposal, arr))
            candidates_by_prompt.append(group)
            if limit_reached:
                break
        if semantic_union:
            return _semantic_union_proposal(
                candidates_by_prompt,
                image_path=image_path,
                model_key=model_key,
                label=label,
                width=width,
                height=height,
                out_dir=out_dir,
                run_id=run_id,
                metadata={
                    "sam2_config": model_cfg,
                    "conditioning": _prompt_conditioning(prompt_groups[0], point_labels),
                },
            )
        return proposals
    # Automatic mask generator is optional in SAM2; use it when available.
    try:
        from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
    except Exception as exc:
        raise AnnotationModelError("SAM2 automatic mask generation is unavailable in this install. Draw/copy a bbox or add positive/negative points and use them as a prompt, or update the sam2 package.") from exc
    generator_kwargs: dict[str, Any] = {
        "points_per_side": int(options.get("points_per_side") or 32),
        "pred_iou_thresh": float(options.get("pred_iou_thresh") if options.get("pred_iou_thresh") is not None else max(float(threshold or 0.0), 0.0) or 0.88),
        "stability_score_thresh": float(options.get("stability_score_thresh") if options.get("stability_score_thresh") is not None else 0.95),
        "box_nms_thresh": float(options.get("box_nms_thresh") if options.get("box_nms_thresh") is not None else 0.7),
        "crop_n_layers": int(options.get("crop_n_layers") or 0),
        "crop_n_points_downscale_factor": int(options.get("crop_n_points_downscale_factor") or 1),
        "min_mask_region_area": int(options.get("min_mask_region_area") or 0),
    }
    generator = SAM2AutomaticMaskGenerator(model, **generator_kwargs)
    masks = generator.generate(image)
    masks = sorted(masks, key=lambda m: float(m.get("predicted_iou") or 0), reverse=True)[:max_props]
    for i, m in enumerate(masks):
        bbox = bbox_from_xywh(*(m.get("bbox") or [0, 0, width, height]), width, height)
        score = float(m.get("predicted_iou") or m.get("stability_score") or 0)
        mask_path = _save_bool_mask(m.get("segmentation"), out_dir, f"{Path(image_path).stem}_{model_key}_{run_id}_auto_{i}") if out_dir and m.get("segmentation") is not None else ""
        proposals.append(AnnotationProposal(label, "mask", bbox, [], score, "model", model_key, mask_path, {
            "sam2_config": model_cfg,
            "area": m.get("area"),
            "run_id": run_id,
            "conditioning": "automatic_class_agnostic",
            "generator_options": generator_kwargs,
        }).to_dict())
    return proposals

def parse_json_proposals(text: str, *, label: str, model_key: str, annotation_type: str = "bbox") -> list[dict[str, Any]]:
    """Parse VLM/LLM JSON proposals from a response body.

    Expected shape can be either a list of proposals or an object with a
    ``proposals`` list.  Each proposal may include bbox, polygon, keypoints_2d or
    keypoints_3d.
    """
    start = text.find("{")
    arr_start = text.find("[")
    if arr_start >= 0 and (start < 0 or arr_start < start):
        start = arr_start
    if start < 0:
        return []
    raw = text[start:]
    # Trim trailing prose after the JSON value by trying progressively smaller suffixes.
    data = None
    for end in range(len(raw), max(len(raw) - 4096, 0), -1):
        try:
            data = json.loads(raw[:end])
            break
        except Exception:
            continue
    if data is None:
        return []
    rows = data.get("proposals") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        return []
    out: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        bbox = row.get("bbox") or {}
        if isinstance(bbox, list) and len(bbox) >= 4:
            bbox = normalize_bbox_xyxy(bbox[0], bbox[1], bbox[2], bbox[3])
        polygon = row.get("polygon") or row.get("segmentation") or []
        metadata = dict(row.get("metadata") or {})
        if row.get("keypoints_2d"):
            metadata["keypoints_2d"] = row.get("keypoints_2d")
        if row.get("keypoints_3d"):
            metadata["keypoints_3d"] = row.get("keypoints_3d")
        out.append(AnnotationProposal(
            str(row.get("label") or label or "object"),
            str(row.get("annotation_type") or annotation_type),
            bbox if isinstance(bbox, dict) else {},
            polygon if isinstance(polygon, list) else [],
            float(row.get("confidence") or row.get("score") or 0.0),
            "vlm",
            model_key,
            str(row.get("mask_path") or ""),
            metadata,
        ).to_dict())
    return out
