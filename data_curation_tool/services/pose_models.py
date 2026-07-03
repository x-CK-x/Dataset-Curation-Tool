from __future__ import annotations

"""Pose-model adapters and skeleton topology helpers.

The spatial editor stores joints as named dictionaries and bones as index/name
pairs.  These helpers normalize model-specific results into that durable format
so 2D/3D poses can be overlaid, edited, exported, and sent to Blender without
coupling saved annotations to a particular inference library.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from PIL import Image

from .annotation_models import AnnotationModelError, normalize_bbox_xyxy


@dataclass(frozen=True)
class SkeletonTemplate:
    key: str
    label: str
    names: tuple[str, ...]
    edges: tuple[tuple[int, int], ...]
    dimension: str = "2d"

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "names": list(self.names),
            "edges": [list(edge) for edge in self.edges],
            "dimension": self.dimension,
        }


COCO17_NAMES = (
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
)
COCO17_EDGES = (
    (0, 1), (0, 2), (1, 3), (2, 4),
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
    (5, 11), (6, 12), (11, 12),
    (11, 13), (13, 15), (12, 14), (14, 16),
    (0, 5), (0, 6),
)

OPENPOSE18_NAMES = (
    "nose", "neck", "right_shoulder", "right_elbow", "right_wrist",
    "left_shoulder", "left_elbow", "left_wrist", "right_hip",
    "right_knee", "right_ankle", "left_hip", "left_knee", "left_ankle",
    "right_eye", "left_eye", "right_ear", "left_ear",
)
OPENPOSE18_EDGES = (
    (0, 1), (1, 2), (2, 3), (3, 4), (1, 5), (5, 6), (6, 7),
    (1, 8), (8, 9), (9, 10), (1, 11), (11, 12), (12, 13),
    (0, 14), (14, 16), (0, 15), (15, 17), (8, 11),
)

H36M17_NAMES = (
    "pelvis", "right_hip", "right_knee", "right_ankle", "left_hip",
    "left_knee", "left_ankle", "spine", "thorax", "neck", "head",
    "left_shoulder", "left_elbow", "left_wrist", "right_shoulder",
    "right_elbow", "right_wrist",
)
H36M17_EDGES = (
    (0, 1), (1, 2), (2, 3), (0, 4), (4, 5), (5, 6),
    (0, 7), (7, 8), (8, 9), (9, 10),
    (8, 11), (11, 12), (12, 13), (8, 14), (14, 15), (15, 16),
)

BLAZEPOSE33_NAMES = (
    "nose", "left_eye_inner", "left_eye", "left_eye_outer",
    "right_eye_inner", "right_eye", "right_eye_outer", "left_ear",
    "right_ear", "mouth_left", "mouth_right", "left_shoulder",
    "right_shoulder", "left_elbow", "right_elbow", "left_wrist",
    "right_wrist", "left_pinky", "right_pinky", "left_index",
    "right_index", "left_thumb", "right_thumb", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle", "left_heel",
    "right_heel", "left_foot_index", "right_foot_index",
)
BLAZEPOSE33_EDGES = (
    (0, 1), (1, 2), (2, 3), (3, 7),
    (0, 4), (4, 5), (5, 6), (6, 8), (9, 10),
    (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
    (17, 19), (12, 14), (14, 16), (16, 18), (16, 20), (16, 22),
    (18, 20), (11, 23), (12, 24), (23, 24),
    (23, 25), (25, 27), (27, 29), (29, 31), (27, 31),
    (24, 26), (26, 28), (28, 30), (30, 32), (28, 32),
)

SKELETON_TEMPLATES: dict[str, SkeletonTemplate] = {
    "coco17": SkeletonTemplate("coco17", "COCO 17 (human 2D)", COCO17_NAMES, COCO17_EDGES, "2d"),
    "openpose18": SkeletonTemplate("openpose18", "OpenPose 18 (human 2D)", OPENPOSE18_NAMES, OPENPOSE18_EDGES, "2d"),
    "blazepose33": SkeletonTemplate("blazepose33", "MediaPipe BlazePose 33 (2D + world 3D)", BLAZEPOSE33_NAMES, BLAZEPOSE33_EDGES, "3d"),
    "h36m17": SkeletonTemplate("h36m17", "Human3.6M 17 (human 3D)", H36M17_NAMES, H36M17_EDGES, "3d"),
    "custom": SkeletonTemplate("custom", "Custom / no predefined topology", tuple(), tuple(), "mixed"),
}

MMPOSE_ALIASES: dict[str, tuple[str, str, str]] = {
    "mmpose-rtmpose-human": ("pose2d", "human", "coco17"),
    "mmpose-vitpose-base": ("pose2d", "vitpose-b", "coco17"),
    "mmpose-rtmpose-wholebody": ("pose2d", "wholebody", "custom"),
    "mmpose-rtmpose-animal": ("pose2d", "animal", "custom"),
    "mmpose-motionbert-human3d": ("pose3d", "human3d", "h36m17"),
    "mmpose-internet-hand3d": ("pose3d", "hand3d", "custom"),
}


def list_skeleton_templates() -> list[dict[str, Any]]:
    return [template.to_dict() for template in SKELETON_TEMPLATES.values()]


def skeleton_for_key(key: str | None) -> SkeletonTemplate:
    return SKELETON_TEMPLATES.get(str(key or "").lower(), SKELETON_TEMPLATES["custom"])


def infer_skeleton_key(count: int, model_key: str = "", dimension: str = "2d") -> str:
    key = str(model_key or "").lower()
    if "mediapipe" in key or count == 33:
        return "blazepose33"
    if "motionbert" in key or dimension == "3d" and count == 17:
        return "h36m17"
    if "openpose" in key or count == 18:
        return "openpose18"
    if count == 17:
        return "coco17"
    return "custom"


def normalize_edges(edges: Iterable[Any] | None) -> list[list[int | str]]:
    out: list[list[int | str]] = []
    seen: set[tuple[str, str]] = set()
    for edge in edges or []:
        if not isinstance(edge, (list, tuple)) or len(edge) < 2:
            continue
        a, b = edge[0], edge[1]
        if isinstance(a, float) and a.is_integer():
            a = int(a)
        if isinstance(b, float) and b.is_integer():
            b = int(b)
        if not isinstance(a, (int, str)) or not isinstance(b, (int, str)) or a == b:
            continue
        fingerprint = tuple(sorted((str(a), str(b))))
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        out.append([a, b])
    return out


def normalize_keypoints(
    points: Iterable[Any] | None,
    *,
    names: Iterable[str] | None = None,
    dimension: str = "2d",
    image_size: tuple[int, int] | None = None,
    scores: Iterable[Any] | None = None,
) -> list[dict[str, Any]]:
    name_list = list(names or [])
    score_list = list(scores or [])
    width, height = image_size or (0, 0)
    out: list[dict[str, Any]] = []
    for index, raw in enumerate(points or []):
        if isinstance(raw, dict):
            item = dict(raw)
            x = item.get("x", item.get("image_x", 0.0))
            y = item.get("y", item.get("image_y", 0.0))
            z = item.get("z", 0.0)
            score = item.get("score", item.get("confidence", item.get("visibility")))
            name = str(item.get("name") or (name_list[index] if index < len(name_list) else f"kp_{index}"))
        elif isinstance(raw, (list, tuple)):
            x = raw[0] if len(raw) > 0 else 0.0
            y = raw[1] if len(raw) > 1 else 0.0
            z = raw[2] if len(raw) > 2 and dimension == "3d" else 0.0
            score = raw[3] if len(raw) > 3 and dimension == "3d" else (raw[2] if len(raw) > 2 and dimension != "3d" else None)
            name = name_list[index] if index < len(name_list) else f"kp_{index}"
            item = {}
        else:
            continue
        try:
            x_f, y_f, z_f = float(x), float(y), float(z)
        except (TypeError, ValueError):
            continue
        row: dict[str, Any] = {"name": name, "x": x_f, "y": y_f}
        if dimension == "3d":
            row["z"] = z_f
            if "image_x" in item:
                row["image_x"] = float(item.get("image_x") or 0.0)
            if "image_y" in item:
                row["image_y"] = float(item.get("image_y") or 0.0)
        if score is None and index < len(score_list):
            score = score_list[index]
        try:
            if score is not None:
                row["score"] = float(score)
        except (TypeError, ValueError):
            pass
        if width and height and dimension == "2d":
            row["x"] = max(0.0, min(float(width), row["x"]))
            row["y"] = max(0.0, min(float(height), row["y"]))
        out.append(row)
    return out


def bbox_from_keypoints(points: Iterable[dict[str, Any]], width: int, height: int, padding: float = 0.04) -> dict[str, float]:
    visible = [p for p in points if float(p.get("score", 1.0) or 0.0) > 0.01]
    if not visible:
        return {}
    xs = [float(p.get("image_x", p.get("x", 0.0))) for p in visible]
    ys = [float(p.get("image_y", p.get("y", 0.0))) for p in visible]
    pad_x, pad_y = width * padding, height * padding
    return normalize_bbox_xyxy(min(xs) - pad_x, min(ys) - pad_y, max(xs) + pad_x, max(ys) + pad_y, width, height)


def _mean_score(points: Iterable[dict[str, Any]], fallback: float = 1.0) -> float:
    values = [float(p.get("score")) for p in points if p.get("score") is not None]
    return sum(values) / len(values) if values else fallback


def _device_for_mmpose(device: str) -> str:
    value = str(device or "auto")
    if value == "auto":
        try:
            import torch
            return "cuda:0" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"
    if value == "cuda":
        return "cuda:0"
    return value


def propose_with_mediapipe(
    image_path: str | Path,
    checkpoint: str | Path,
    *,
    model_key: str,
    label: str = "pose",
    threshold: float = 0.25,
    annotation_type: str = "pose3d",
    options: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Run MediaPipe Pose Landmarker and return editable 2D/world-3D poses."""
    try:
        import mediapipe as mp
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision
    except Exception as exc:
        raise AnnotationModelError("MediaPipe is not installed. Run install_pose_models.bat mediapipe or pip install mediapipe.") from exc

    checkpoint_path = Path(checkpoint).expanduser()
    if not checkpoint_path.exists():
        raise AnnotationModelError(f"MediaPipe Pose Landmarker model was not found: {checkpoint_path}")
    options = dict(options or {})
    max_poses = max(1, int(options.get("max_proposals") or options.get("num_poses") or 5))
    min_score = max(0.0, min(1.0, float(threshold if threshold is not None else 0.25)))
    try:
        task_options = vision.PoseLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(checkpoint_path)),
            running_mode=vision.RunningMode.IMAGE,
            num_poses=max_poses,
            min_pose_detection_confidence=min_score,
            min_pose_presence_confidence=min_score,
            min_tracking_confidence=min_score,
            output_segmentation_masks=False,
        )
        image = mp.Image.create_from_file(str(image_path))
        with vision.PoseLandmarker.create_from_options(task_options) as landmarker:
            result = landmarker.detect(image)
    except Exception as exc:
        raise AnnotationModelError(f"MediaPipe Pose Landmarker inference failed: {exc}") from exc

    with Image.open(image_path) as pil:
        width, height = pil.size
    image_poses = list(getattr(result, "pose_landmarks", None) or [])
    world_poses = list(getattr(result, "pose_world_landmarks", None) or [])
    proposals: list[dict[str, Any]] = []
    edges = [list(edge) for edge in BLAZEPOSE33_EDGES]
    for pose_index, landmarks in enumerate(image_poses[:max_poses]):
        keypoints_2d: list[dict[str, Any]] = []
        for index, landmark in enumerate(landmarks):
            score = float(getattr(landmark, "visibility", getattr(landmark, "presence", 1.0)) or 0.0)
            keypoints_2d.append({
                "name": BLAZEPOSE33_NAMES[index] if index < len(BLAZEPOSE33_NAMES) else f"kp_{index}",
                "x": float(getattr(landmark, "x", 0.0)) * width,
                "y": float(getattr(landmark, "y", 0.0)) * height,
                "z": float(getattr(landmark, "z", 0.0)),
                "score": score,
            })
        keypoints_3d: list[dict[str, Any]] = []
        world = world_poses[pose_index] if pose_index < len(world_poses) else []
        for index, landmark in enumerate(world):
            image_point = keypoints_2d[index] if index < len(keypoints_2d) else {}
            score = float(getattr(landmark, "visibility", image_point.get("score", 1.0)) or 0.0)
            keypoints_3d.append({
                "name": BLAZEPOSE33_NAMES[index] if index < len(BLAZEPOSE33_NAMES) else f"kp_{index}",
                "x": float(getattr(landmark, "x", 0.0)),
                "y": -float(getattr(landmark, "y", 0.0)),
                "z": -float(getattr(landmark, "z", 0.0)),
                "image_x": float(image_point.get("x", 0.0)),
                "image_y": float(image_point.get("y", 0.0)),
                "score": score,
            })
        confidence = _mean_score(keypoints_2d, fallback=min_score)
        metadata = {
            "keypoints_2d": keypoints_2d,
            "keypoints_3d": keypoints_3d,
            "edges": edges,
            "skeleton_template": "blazepose33",
            "coordinate_system": "image_pixels+mediapipe_world_meters",
            "pose_index": pose_index,
        }
        proposals.append({
            "label": label or "pose",
            "annotation_type": "pose3d" if annotation_type in {"pose3d", "animation_pose"} else "pose2d",
            "bbox": bbox_from_keypoints(keypoints_2d, width, height),
            "polygon": [],
            "confidence": confidence,
            "source": "mediapipe_pose_landmarker",
            "model_key": model_key,
            "metadata": metadata,
        })
    return proposals


def _flatten_mmpose_predictions(raw: Any) -> list[dict[str, Any]]:
    value = raw
    while isinstance(value, list) and len(value) == 1 and isinstance(value[0], list):
        value = value[0]
    if isinstance(value, dict):
        return [value]
    if not isinstance(value, list):
        return []
    out: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            out.append(item)
        elif isinstance(item, list):
            out.extend(row for row in item if isinstance(row, dict))
    return out


def _mmpose_dataset_meta(inferencer: Any, dimension: str) -> tuple[list[str], list[list[int | str]]]:
    candidates = []
    for attr in ("pose3d_model", "pose2d_model", "model") if dimension == "3d" else ("pose2d_model", "model", "pose3d_model"):
        model = getattr(inferencer, attr, None)
        if model is not None:
            candidates.append(getattr(model, "dataset_meta", None) or getattr(model, "metainfo", None) or {})
    meta = next((m for m in candidates if isinstance(m, dict) and m), {})
    id_to_name = meta.get("keypoint_id2name") or {}
    if isinstance(id_to_name, dict):
        names = [str(id_to_name[index]) for index in sorted(id_to_name) if index in id_to_name]
    else:
        names = list(meta.get("keypoint_name") or [])
    edges: list[list[int | str]] = []
    raw_edges = meta.get("skeleton_links") or meta.get("skeleton") or []
    name_to_id = meta.get("keypoint_name2id") or {name: idx for idx, name in enumerate(names)}
    for edge in raw_edges:
        if isinstance(edge, dict):
            edge = edge.get("link") or edge.get("edge") or []
        if not isinstance(edge, (list, tuple)) or len(edge) < 2:
            continue
        a, b = edge[:2]
        if isinstance(a, str) and a in name_to_id:
            a = int(name_to_id[a])
        if isinstance(b, str) and b in name_to_id:
            b = int(name_to_id[b])
        edges.append([a, b])
    return names, normalize_edges(edges)


def propose_with_mmpose(
    image_path: str | Path,
    *,
    model_key: str,
    label: str = "pose",
    threshold: float = 0.25,
    annotation_type: str = "pose2d",
    device: str = "auto",
    options: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Run an MMPoseInferencer alias/config and normalize its predictions."""
    try:
        from mmpose.apis import MMPoseInferencer
    except Exception as exc:
        raise AnnotationModelError(
            "MMPose is not installed. Run install_pose_models.bat mmpose. "
            "The installer uses OpenMIM for MMEngine/MMCV/MMPose compatibility."
        ) from exc

    options = dict(options or {})
    default_dimension, default_alias, default_template = MMPOSE_ALIASES.get(model_key, (annotation_type if annotation_type in {"pose2d", "pose3d"} else "pose2d", "human", "custom"))
    dimension = "pose3d" if annotation_type in {"pose3d", "animation_pose"} or default_dimension == "pose3d" else "pose2d"
    alias = str(options.get("mmpose_alias") or default_alias)
    kwargs: dict[str, Any] = {"device": _device_for_mmpose(device)}
    config_path = str(options.get("mmpose_config") or options.get("pose_config") or "").strip()
    checkpoint_path = str(options.get("local_model_path") or options.get("checkpoint_path") or "").strip()
    if dimension == "pose3d":
        kwargs["pose3d"] = config_path or alias
        if checkpoint_path:
            kwargs["pose3d_weights"] = checkpoint_path
    else:
        kwargs["pose2d"] = config_path or alias
        if checkpoint_path:
            kwargs["pose2d_weights"] = checkpoint_path
    detector = str(options.get("detector") or "").strip()
    detector_weights = str(options.get("detector_weights") or "").strip()
    if detector:
        kwargs["det_model"] = detector
    if detector_weights:
        kwargs["det_weights"] = detector_weights
    try:
        inferencer = MMPoseInferencer(**kwargs)
        run_kwargs: dict[str, Any] = {
            "show": False,
            "return_vis": False,
            "bbox_thr": float(options.get("bbox_threshold") if options.get("bbox_threshold") is not None else threshold),
            "nms_thr": float(options.get("nms_threshold") or 0.3),
        }
        if options.get("pose_threshold") is not None:
            run_kwargs["kpt_thr"] = float(options["pose_threshold"])
        raw_result = next(inferencer(str(image_path), **run_kwargs))
    except Exception as exc:
        raise AnnotationModelError(f"MMPose inference failed for alias/config {config_path or alias!r}: {exc}") from exc

    with Image.open(image_path) as pil:
        width, height = pil.size
    predictions = _flatten_mmpose_predictions((raw_result or {}).get("predictions") if isinstance(raw_result, dict) else raw_result)
    names, meta_edges = _mmpose_dataset_meta(inferencer, "3d" if dimension == "pose3d" else "2d")
    max_proposals = max(1, int(options.get("max_proposals") or 25))
    proposals: list[dict[str, Any]] = []
    for pose_index, pred in enumerate(predictions[:max_proposals]):
        raw_points = pred.get("keypoints") or pred.get("keypoints_3d") or []
        while isinstance(raw_points, list) and len(raw_points) == 1 and isinstance(raw_points[0], list) and raw_points[0] and isinstance(raw_points[0][0], (list, tuple, dict)):
            raw_points = raw_points[0]
        scores = pred.get("keypoint_scores") or pred.get("keypoints_scores") or []
        while isinstance(scores, list) and len(scores) == 1 and isinstance(scores[0], list):
            scores = scores[0]
        point_dimension = "3d" if dimension == "pose3d" else "2d"
        points = normalize_keypoints(raw_points, names=names, dimension=point_dimension, image_size=(width, height), scores=scores)
        if not points:
            continue
        template_key = default_template if default_template != "custom" else infer_skeleton_key(len(points), model_key, point_dimension)
        template = skeleton_for_key(template_key)
        edges = meta_edges or [list(edge) for edge in template.edges]
        metadata: dict[str, Any] = {
            "edges": edges,
            "skeleton_template": template_key,
            "pose_index": pose_index,
            "mmpose_alias": alias,
        }
        if dimension == "pose3d":
            metadata["keypoints_3d"] = points
            # Some 3D inferencers also return source 2D keypoints.
            source_2d = pred.get("keypoints_2d") or pred.get("input_keypoints") or []
            if source_2d:
                metadata["keypoints_2d"] = normalize_keypoints(source_2d, names=names, dimension="2d", image_size=(width, height), scores=scores)
            else:
                metadata["keypoints_2d"] = [
                    {"name": p["name"], "x": float(p.get("image_x", width / 2 + p["x"])), "y": float(p.get("image_y", height / 2 - p["y"])), "score": p.get("score", 1.0)}
                    for p in points
                ]
        else:
            metadata["keypoints_2d"] = points
            metadata["keypoints_3d"] = []
        bbox_value = pred.get("bbox") or pred.get("bboxes") or {}
        bbox: dict[str, float] = {}
        if isinstance(bbox_value, dict):
            bbox = bbox_value
        elif isinstance(bbox_value, list):
            flat = bbox_value[0] if bbox_value and isinstance(bbox_value[0], list) else bbox_value
            if len(flat) >= 4:
                bbox = normalize_bbox_xyxy(float(flat[0]), float(flat[1]), float(flat[2]), float(flat[3]), width, height)
        if not bbox:
            bbox = bbox_from_keypoints(metadata.get("keypoints_2d") or [], width, height)
        confidence = float(pred.get("bbox_score") or pred.get("score") or _mean_score(points, float(threshold or 0.25)))
        proposals.append({
            "label": label or "pose",
            "annotation_type": dimension,
            "bbox": bbox,
            "polygon": [],
            "confidence": confidence,
            "source": "mmpose_inferencer",
            "model_key": model_key,
            "metadata": metadata,
        })
    return proposals
