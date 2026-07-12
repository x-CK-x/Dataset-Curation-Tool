from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
from PIL import Image, ImageChops, ImageFilter, ImageOps

from ..database import Database, now_iso
from ..paths import AppPaths
from ..utils import normalize_tag, read_text_if_exists, tag_string, write_text
from .media_service import MediaService
from .global_dataset_service import GlobalDatasetService

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".jfif"}


def _json_loads(value: Any, default: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if value in (None, ""):
        return default
    try:
        data = json.loads(str(value))
        return data if data is not None else default
    except Exception:
        return default


def _safe_slug(value: str, fallback: str = "character") -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "").strip()).strip("._-")
    return clean or fallback


def _as_float_list(value: Sequence[float] | np.ndarray) -> list[float]:
    arr = np.asarray(value, dtype=np.float32).reshape(-1)
    norm = float(np.linalg.norm(arr))
    if norm > 0:
        arr = arr / norm
    return [float(x) for x in arr.tolist()]


def _mean_vector(vectors: Sequence[Sequence[float]]) -> list[float]:
    if not vectors:
        return []
    arr = np.asarray(vectors, dtype=np.float32)
    return _as_float_list(arr.mean(axis=0))


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b:
        return 0.0
    av = np.asarray(a, dtype=np.float32)
    bv = np.asarray(b, dtype=np.float32)
    if av.shape != bv.shape:
        n = min(av.size, bv.size)
        if n <= 0:
            return 0.0
        av = av[:n]
        bv = bv[:n]
    den = float(np.linalg.norm(av) * np.linalg.norm(bv))
    return float(np.dot(av, bv) / den) if den else 0.0


def _image_from_path(path: Path) -> Image.Image:
    with Image.open(path) as im:
        return ImageOps.exif_transpose(im).convert("RGB")


def _character_crops(im: Image.Image, crop_strategy: str = "whole_plus_head") -> list[tuple[str, Image.Image]]:
    """Dependency-light crop proposals for one/few-shot character reference.

    The app can use richer detectors when installed.  This fallback deliberately
    avoids training a detector and gives deterministic candidate regions: full
    image, top/center headshot, torso crop, and central square.  The highest
    similarity across these regions becomes the candidate score.
    """
    w, h = im.size
    crops: list[tuple[str, Image.Image]] = [("whole", im)]
    if w <= 0 or h <= 0:
        return crops
    side = min(w, h)
    # Top-center head/face-biased square.  Works acceptably for portraits and
    # character-sheet examples and is intentionally conservative.
    head_side = max(64, int(side * 0.58))
    left = max(0, (w - head_side) // 2)
    top = max(0, int(h * 0.05))
    crops.append(("headshot_top_center", im.crop((left, top, min(w, left + head_side), min(h, top + head_side)))))
    torso_w = max(64, int(w * 0.72))
    torso_h = max(64, int(h * 0.72))
    left = max(0, (w - torso_w) // 2)
    top = max(0, int(h * 0.10))
    crops.append(("upper_body", im.crop((left, top, min(w, left + torso_w), min(h, top + torso_h)))))
    center_side = min(w, h)
    left = max(0, (w - center_side) // 2)
    top = max(0, (h - center_side) // 2)
    crops.append(("center_square", im.crop((left, top, left + center_side, top + center_side))))
    if crop_strategy == "whole_only":
        return crops[:1]
    if crop_strategy == "headshot_only":
        return [crops[1]]
    return crops


def _feature_embedding(path: Path, crop_strategy: str = "whole_plus_head") -> dict[str, Any]:
    im = _image_from_path(path)
    candidates: list[dict[str, Any]] = []
    for crop_name, crop in _character_crops(im, crop_strategy=crop_strategy):
        crop = ImageOps.exif_transpose(crop).convert("RGB")
        resized = crop.resize((96, 96), Image.Resampling.BICUBIC)
        # Color distribution: useful for characters with consistent markings/outfits.
        hist: list[float] = []
        for channel in resized.split():
            h = channel.histogram()[:256]
            bins = [sum(h[i:i + 16]) for i in range(0, 256, 16)]
            hist.extend(bins)
        # Low-res layout: approximate silhouette/color placement.
        layout = np.asarray(resized.resize((16, 16), Image.Resampling.BILINEAR), dtype=np.float32).reshape(-1) / 255.0
        # Edge energy: weak silhouette signal without external detectors.
        gray = ImageOps.grayscale(resized)
        edges = ImageChops.difference(gray, gray.filter(ImageFilter.GaussianBlur(radius=2.0)))
        edge_layout = np.asarray(edges.resize((12, 12), Image.Resampling.BILINEAR), dtype=np.float32).reshape(-1) / 255.0
        vec = np.concatenate([np.asarray(hist, dtype=np.float32), layout, edge_layout])
        candidates.append({"crop": crop_name, "embedding": _as_float_list(vec)})
    if not candidates:
        return {"path": str(path), "embedding": [], "crop_embeddings": []}
    return {"path": str(path), "embedding": candidates[0]["embedding"], "crop_embeddings": candidates}


class CharacterReferenceService:
    """Zero/one/few-shot character reference and pruning service.

    This is deliberately a *no-new-training-required* layer. It stores reusable
    positive/negative prototypes from reference images and verified examples,
    then ranks local/global/branch images by similarity. Optional model-backed
    DINOv2/CLIP/OWLv2/Grounding-DINO pipelines are exposed as contracts; the
    CPU fallback remains deterministic for machines without those dependencies.
    """

    def __init__(self, db: Database, paths: AppPaths, media: MediaService, global_dataset: GlobalDatasetService | None = None):
        self.db = db
        self.paths = paths
        self.media = media
        self.global_dataset = global_dataset
        self.root = self.paths.outputs / "character_reference"
        self.root.mkdir(parents=True, exist_ok=True)
        self.ensure_schema()

    def ensure_schema(self) -> None:
        with self.db._lock, self.db.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS character_reference_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_name TEXT NOT NULL UNIQUE,
                    notes TEXT NOT NULL DEFAULT '',
                    pipeline TEXT NOT NULL DEFAULT 'dino_clip_fallback',
                    threshold REAL NOT NULL DEFAULT 0.62,
                    crop_strategy TEXT NOT NULL DEFAULT 'whole_plus_head',
                    reference_paths_json TEXT NOT NULL DEFAULT '[]',
                    positive_media_ids_json TEXT NOT NULL DEFAULT '[]',
                    negative_media_ids_json TEXT NOT NULL DEFAULT '[]',
                    positive_paths_json TEXT NOT NULL DEFAULT '[]',
                    negative_paths_json TEXT NOT NULL DEFAULT '[]',
                    prototype_json TEXT NOT NULL DEFAULT '{}',
                    negative_prototype_json TEXT NOT NULL DEFAULT '{}',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS character_reference_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_id INTEGER REFERENCES character_reference_profiles(id) ON DELETE SET NULL,
                    target_name TEXT NOT NULL,
                    pipeline TEXT NOT NULL DEFAULT 'dino_clip_fallback',
                    threshold REAL NOT NULL DEFAULT 0.62,
                    scope_json TEXT NOT NULL DEFAULT '{}',
                    status TEXT NOT NULL DEFAULT 'created',
                    result_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    finished_at TEXT
                );
                CREATE TABLE IF NOT EXISTS character_reference_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL REFERENCES character_reference_runs(id) ON DELETE CASCADE,
                    media_id INTEGER,
                    global_asset_id INTEGER,
                    branch_item_id INTEGER,
                    path TEXT NOT NULL,
                    score REAL NOT NULL,
                    positive_score REAL NOT NULL DEFAULT 0,
                    negative_score REAL NOT NULL DEFAULT 0,
                    decision TEXT NOT NULL DEFAULT 'uncertain',
                    best_crop TEXT NOT NULL DEFAULT 'whole',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_character_reference_scores_run ON character_reference_scores(run_id, score DESC);
                CREATE INDEX IF NOT EXISTS idx_character_reference_profiles_target ON character_reference_profiles(target_name);
                """
            )

    # ------------------------------------------------------------------
    # Catalog/status/profile CRUD
    # ------------------------------------------------------------------
    def status(self) -> dict[str, Any]:
        profiles = self.db.query_one("SELECT COUNT(*) AS c FROM character_reference_profiles WHERE active=1") or {"c": 0}
        runs = self.db.query_one("SELECT COUNT(*) AS c FROM character_reference_runs") or {"c": 0}
        scores = self.db.query_one("SELECT COUNT(*) AS c FROM character_reference_scores") or {"c": 0}
        return {
            "profile_count": int(profiles.get("c") or 0),
            "run_count": int(runs.get("c") or 0),
            "score_count": int(scores.get("c") or 0),
            "pipelines": self.pipeline_catalog(),
            "outputs_dir": str(self.root),
        }

    def pipeline_catalog(self) -> list[dict[str, Any]]:
        return [
            {
                "key": "dino_clip_fallback",
                "label": "Character prototype verifier (DINO/CLIP contract + CPU fallback)",
                "available": True,
                "requires": [],
                "recommended": True,
                "description": "No-training one/few-shot reference matching. Uses deterministic image features now and can route to DINOv2/CLIP embeddings when installed.",
            },
            {
                "key": "dinov2_embedding",
                "label": "DINOv2 few-shot visual embedding",
                "available": self._optional_available("torch", "transformers"),
                "requires": ["torch", "transformers", "facebook/dinov2-base or larger"],
                "description": "Strong self-supervised features for visual retrieval/prototype similarity without fine-tuning.",
            },
            {
                "key": "clip_siglip_embedding",
                "label": "CLIP/SigLIP reference embedding",
                "available": self._optional_available("torch", "transformers"),
                "requires": ["torch", "transformers", "CLIP/SigLIP weights"],
                "description": "Image embedding and optional text prompt guidance for reference search and cross-domain pruning.",
            },
            {
                "key": "owlv2_image_guided",
                "label": "OWLv2 image-guided one-shot detector",
                "available": self._optional_available("torch", "transformers"),
                "requires": ["torch", "transformers", "google/owlv2-base-patch16-ensemble"],
                "description": "Image-guided object detection contract for locating a reference object/character in a target image.",
            },
            {
                "key": "grounding_dino_sam_verify",
                "label": "Grounding-DINO/SAM proposal + prototype verification",
                "available": self._optional_available("torch", "transformers"),
                "requires": ["torch", "transformers", "Grounding-DINO", "SAM/SAM2 optional"],
                "description": "Open-set prompt proposals plus reference-prototype verification and optional masks.",
            },
        ]

    @staticmethod
    def _optional_available(*modules: str) -> bool:
        import importlib.util
        return all(importlib.util.find_spec(m) is not None for m in modules)

    def list_profiles(self) -> list[dict[str, Any]]:
        rows = self.db.query("SELECT * FROM character_reference_profiles WHERE active=1 ORDER BY updated_at DESC, target_name")
        return [self._decode_profile(row) for row in rows]

    def get_profile(self, target_name: str) -> dict[str, Any] | None:
        row = self.db.query_one("SELECT * FROM character_reference_profiles WHERE target_name=? AND active=1", (str(target_name or "").strip(),))
        return self._decode_profile(row) if row else None

    def delete_profile(self, target_name: str) -> dict[str, Any]:
        self.db.execute("UPDATE character_reference_profiles SET active=0, updated_at=? WHERE target_name=?", (now_iso(), str(target_name or "").strip()))
        return {"ok": True, "target_name": target_name}

    def upsert_profile(self, payload: Any) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        target = str(data.get("target_name") or data.get("character_name") or "").strip()
        if not target:
            raise ValueError("target_name is required.")
        reference_paths = self._path_list(data.get("reference_paths"))
        positive_paths = self._path_list(data.get("positive_paths"))
        negative_paths = self._path_list(data.get("negative_paths"))
        positive_media_ids = [int(x) for x in (data.get("positive_media_ids") or []) if str(x).strip()]
        negative_media_ids = [int(x) for x in (data.get("negative_media_ids") or []) if str(x).strip()]
        pipeline = str(data.get("pipeline") or "dino_clip_fallback")
        crop_strategy = str(data.get("crop_strategy") or "whole_plus_head")
        threshold = float(data.get("threshold") if data.get("threshold") is not None else 0.62)
        prototype, negative_prototype, meta = self._build_prototypes(reference_paths, positive_paths, negative_paths, positive_media_ids, negative_media_ids, crop_strategy)
        now = now_iso()
        existing = self.db.query_one("SELECT id FROM character_reference_profiles WHERE target_name=?", (target,))
        params = (
            target,
            str(data.get("notes") or ""),
            pipeline,
            threshold,
            crop_strategy,
            json.dumps(reference_paths, ensure_ascii=False),
            json.dumps(positive_media_ids),
            json.dumps(negative_media_ids),
            json.dumps(positive_paths, ensure_ascii=False),
            json.dumps(negative_paths, ensure_ascii=False),
            json.dumps(prototype, ensure_ascii=False),
            json.dumps(negative_prototype, ensure_ascii=False),
            json.dumps(meta, ensure_ascii=False),
            now,
            now,
        )
        if existing:
            self.db.execute(
                """
                UPDATE character_reference_profiles
                SET notes=?, pipeline=?, threshold=?, crop_strategy=?, reference_paths_json=?, positive_media_ids_json=?, negative_media_ids_json=?, positive_paths_json=?, negative_paths_json=?, prototype_json=?, negative_prototype_json=?, metadata_json=?, active=1, updated_at=?
                WHERE target_name=?
                """,
                (params[1], params[2], params[3], params[4], params[5], params[6], params[7], params[8], params[9], params[10], params[11], params[12], now, target),
            )
        else:
            self.db.execute(
                """
                INSERT INTO character_reference_profiles(target_name, notes, pipeline, threshold, crop_strategy, reference_paths_json, positive_media_ids_json, negative_media_ids_json, positive_paths_json, negative_paths_json, prototype_json, negative_prototype_json, metadata_json, active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                params,
            )
        return self.get_profile(target) or {"target_name": target}

    def rebuild_profile_from_run(self, target_name: str, run_id: int | None = None, accept_threshold: float = 0.72, reject_threshold: float = 0.40) -> dict[str, Any]:
        profile = self.get_profile(target_name)
        if not profile:
            raise ValueError(f"Unknown character reference profile: {target_name}")
        where = ["r.target_name=?"]
        params: list[Any] = [target_name]
        if run_id:
            where.append("s.run_id=?"); params.append(int(run_id))
        rows = self.db.query(
            f"""
            SELECT s.* FROM character_reference_scores s
            JOIN character_reference_runs r ON r.id=s.run_id
            WHERE {' AND '.join(where)}
            ORDER BY s.score DESC, s.id DESC
            LIMIT 2000
            """,
            params,
        )
        positive_paths = set(profile.get("positive_paths") or [])
        negative_paths = set(profile.get("negative_paths") or [])
        for row in rows:
            path = str(row.get("path") or "")
            if not path:
                continue
            score = float(row.get("score") or 0)
            if score >= accept_threshold:
                positive_paths.add(path)
            elif score <= reject_threshold:
                negative_paths.add(path)
        payload = {
            **profile,
            "positive_paths": sorted(positive_paths),
            "negative_paths": sorted(negative_paths),
            "reference_paths": profile.get("reference_paths") or [],
        }
        return self.upsert_profile(payload)

    def _decode_profile(self, row: dict[str, Any]) -> dict[str, Any]:
        payload = dict(row)
        payload["reference_paths"] = _json_loads(payload.pop("reference_paths_json", "[]"), [])
        payload["positive_media_ids"] = _json_loads(payload.pop("positive_media_ids_json", "[]"), [])
        payload["negative_media_ids"] = _json_loads(payload.pop("negative_media_ids_json", "[]"), [])
        payload["positive_paths"] = _json_loads(payload.pop("positive_paths_json", "[]"), [])
        payload["negative_paths"] = _json_loads(payload.pop("negative_paths_json", "[]"), [])
        payload["prototype"] = _json_loads(payload.pop("prototype_json", "{}"), {})
        payload["negative_prototype"] = _json_loads(payload.pop("negative_prototype_json", "{}"), {})
        payload["metadata"] = _json_loads(payload.pop("metadata_json", "{}"), {})
        return payload

    # ------------------------------------------------------------------
    # Ranking/pruning
    # ------------------------------------------------------------------
    def rank(self, payload: Any, progress=None) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        target = str(data.get("target_name") or data.get("character_name") or "").strip()
        if not target:
            raise ValueError("target_name is required.")
        profile = self.get_profile(target)
        if not profile:
            profile = self.upsert_profile(data)
        threshold = float(data.get("threshold") if data.get("threshold") is not None else profile.get("threshold") or 0.62)
        uncertain_margin = float(data.get("uncertain_margin") if data.get("uncertain_margin") is not None else 0.06)
        max_items = max(1, min(50000, int(data.get("max_items") or 5000)))
        candidates = self._candidate_paths(data, max_items=max_items)
        now = now_iso()
        run_id = int(self.db.execute(
            """
            INSERT INTO character_reference_runs(profile_id, target_name, pipeline, threshold, scope_json, status, result_json, created_at)
            VALUES (?, ?, ?, ?, ?, 'running', '{}', ?)
            """,
            (profile.get("id"), target, data.get("pipeline") or profile.get("pipeline") or "dino_clip_fallback", threshold, json.dumps(data, ensure_ascii=False, default=str), now),
        ))
        prototype = (profile.get("prototype") or {}).get("embedding") or []
        negative = (profile.get("negative_prototype") or {}).get("embedding") or []
        scored: list[dict[str, Any]] = []
        total = max(1, len(candidates))
        for idx, candidate in enumerate(candidates, start=1):
            if progress:
                progress((idx - 1) / total, f"Character reference rank {idx}/{len(candidates)}")
            path = Path(candidate["path"]).expanduser()
            if not path.exists() or path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            score_payload = self._score_path(path, prototype, negative, crop_strategy=str(profile.get("crop_strategy") or "whole_plus_head"))
            pos_score = float(score_payload["positive_score"])
            neg_score = float(score_payload["negative_score"])
            final_score = float(score_payload["score"])
            if final_score >= threshold:
                decision = "match"
            elif final_score >= (threshold - uncertain_margin):
                decision = "uncertain"
            else:
                decision = "reject"
            metadata = {"source": candidate.get("source"), "candidate": candidate.get("metadata") or {}, "crop_scores": score_payload.get("crop_scores") or []}
            score_id = self.db.execute(
                """
                INSERT INTO character_reference_scores(run_id, media_id, global_asset_id, branch_item_id, path, score, positive_score, negative_score, decision, best_crop, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, candidate.get("media_id"), candidate.get("global_asset_id"), candidate.get("branch_item_id"), str(path), final_score, pos_score, neg_score, decision, score_payload.get("best_crop") or "whole", json.dumps(metadata, ensure_ascii=False), now_iso()),
            )
            scored.append({"id": int(score_id), **candidate, "score": round(final_score, 6), "positive_score": round(pos_score, 6), "negative_score": round(neg_score, 6), "decision": decision, "best_crop": score_payload.get("best_crop") or "whole"})
        scored.sort(key=lambda x: float(x.get("score") or 0), reverse=True)
        result = {
            "ok": True,
            "run_id": run_id,
            "target_name": target,
            "threshold": threshold,
            "candidate_count": len(candidates),
            "scored_count": len(scored),
            "matches": sum(1 for x in scored if x.get("decision") == "match"),
            "uncertain": sum(1 for x in scored if x.get("decision") == "uncertain"),
            "rejects": sum(1 for x in scored if x.get("decision") == "reject"),
            "items": scored[: int(data.get("return_limit") or 500)],
        }
        self.db.execute("UPDATE character_reference_runs SET status='complete', finished_at=?, result_json=? WHERE id=?", (now_iso(), json.dumps({k: v for k, v in result.items() if k != "items"}, ensure_ascii=False), run_id))
        if progress:
            progress(1.0, "Character reference ranking complete")
        return result

    def prune_plan(self, payload: Any) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        if data.get("run_id"):
            rows = self.db.query("SELECT * FROM character_reference_scores WHERE run_id=? ORDER BY score DESC", (int(data["run_id"]),))
            run = self.db.query_one("SELECT * FROM character_reference_runs WHERE id=?", (int(data["run_id"]),)) or {}
            threshold = float(data.get("threshold") if data.get("threshold") is not None else run.get("threshold") or 0.62)
        else:
            ranked = self.rank(data)
            rows = self.db.query("SELECT * FROM character_reference_scores WHERE run_id=? ORDER BY score DESC", (int(ranked["run_id"]),))
            threshold = float(ranked.get("threshold") or 0.62)
        keep = []
        reject = []
        uncertain = []
        for row in rows:
            item = {**row, "metadata": _json_loads(row.get("metadata_json"), {})}
            decision = str(row.get("decision") or "")
            if decision == "match" or float(row.get("score") or 0) >= threshold:
                keep.append(item)
            elif decision == "uncertain":
                uncertain.append(item)
            else:
                reject.append(item)
        return {"ok": True, "threshold": threshold, "keep": keep, "uncertain": uncertain, "reject": reject, "counts": {"keep": len(keep), "uncertain": len(uncertain), "reject": len(reject)}}

    def apply_prune_to_branch(self, payload: Any) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        branch_id = int(data.get("branch_id") or 0)
        if not branch_id:
            raise ValueError("branch_id is required.")
        run_id = int(data.get("run_id") or 0)
        if not run_id:
            raise ValueError("run_id is required.")
        mode = str(data.get("mode") or "exclude_rejects")
        rows = self.db.query("SELECT * FROM character_reference_scores WHERE run_id=? AND branch_item_id IS NOT NULL", (run_id,))
        changed = 0
        now = now_iso()
        for row in rows:
            decision = str(row.get("decision") or "")
            include = None
            if mode == "include_matches_only":
                include = 1 if decision == "match" else 0
            elif mode == "exclude_rejects" and decision == "reject":
                include = 0
            elif mode == "mark_uncertain" and decision == "uncertain":
                # Preserve include but annotate config.
                include = None
            if include is not None:
                self.db.execute("UPDATE dataset_branch_items SET include=?, updated_at=? WHERE id=? AND branch_id=?", (include, now, int(row["branch_item_id"]), branch_id))
                changed += 1
            if mode == "mark_uncertain" and decision == "uncertain":
                item = self.db.query_one("SELECT * FROM dataset_branch_items WHERE id=? AND branch_id=?", (int(row["branch_item_id"]), branch_id))
                if item:
                    cfg = _json_loads(item.get("item_config_json"), {})
                    cfg.setdefault("review_flags", []).append({"kind": "character_reference_uncertain", "run_id": run_id, "score": row.get("score"), "target": data.get("target_name")})
                    self.db.execute("UPDATE dataset_branch_items SET item_config_json=?, updated_at=? WHERE id=?", (json.dumps(cfg, ensure_ascii=False), now, int(item["id"])))
                    changed += 1
        return {"ok": True, "branch_id": branch_id, "run_id": run_id, "mode": mode, "changed": changed}

    def _score_path(self, path: Path, prototype: Sequence[float], negative: Sequence[float], crop_strategy: str) -> dict[str, Any]:
        emb_payload = _feature_embedding(path, crop_strategy=crop_strategy)
        crop_scores: list[dict[str, Any]] = []
        best = {"score": -999.0, "positive_score": 0.0, "negative_score": 0.0, "best_crop": "whole"}
        for item in emb_payload.get("crop_embeddings") or []:
            emb = item.get("embedding") or []
            pos = _cosine(emb, prototype)
            neg = _cosine(emb, negative) if negative else 0.0
            score = pos - max(0.0, neg) * 0.18
            crop_scores.append({"crop": item.get("crop"), "positive_score": round(pos, 6), "negative_score": round(neg, 6), "score": round(score, 6)})
            if score > best["score"]:
                best = {"score": score, "positive_score": pos, "negative_score": neg, "best_crop": str(item.get("crop") or "whole")}
        best["crop_scores"] = crop_scores
        return best

    def _build_prototypes(self, reference_paths: list[str], positive_paths: list[str], negative_paths: list[str], positive_media_ids: list[int], negative_media_ids: list[int], crop_strategy: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        pos_paths = list(dict.fromkeys([*reference_paths, *positive_paths, *self._media_paths(positive_media_ids)]))
        neg_paths = list(dict.fromkeys([*negative_paths, *self._media_paths(negative_media_ids)]))
        pos_embeddings = []
        neg_embeddings = []
        for path in pos_paths:
            p = Path(path).expanduser()
            if p.exists() and p.suffix.lower() in IMAGE_EXTENSIONS:
                payload = _feature_embedding(p, crop_strategy=crop_strategy)
                # Use all crop embeddings so a profile can match full-body and face/detail views.
                for item in payload.get("crop_embeddings") or []:
                    if item.get("embedding"):
                        pos_embeddings.append(item["embedding"])
        for path in neg_paths:
            p = Path(path).expanduser()
            if p.exists() and p.suffix.lower() in IMAGE_EXTENSIONS:
                payload = _feature_embedding(p, crop_strategy=crop_strategy)
                for item in payload.get("crop_embeddings") or []:
                    if item.get("embedding"):
                        neg_embeddings.append(item["embedding"])
        if not pos_embeddings:
            raise ValueError("At least one readable reference/positive image is required for a character reference profile.")
        proto = {"embedding": _mean_vector(pos_embeddings), "count": len(pos_embeddings), "paths": pos_paths, "backend": "deterministic_visual_features"}
        neg = {"embedding": _mean_vector(neg_embeddings), "count": len(neg_embeddings), "paths": neg_paths, "backend": "deterministic_visual_features"} if neg_embeddings else {}
        meta = {"positive_image_count": len(pos_paths), "negative_image_count": len(neg_paths), "crop_strategy": crop_strategy, "created_by": "character_reference_service"}
        return proto, neg, meta

    def _media_paths(self, media_ids: Iterable[int]) -> list[str]:
        paths: list[str] = []
        for media_id in media_ids or []:
            media = self.db.query_one("SELECT path FROM media WHERE id=? AND active=1", (int(media_id),))
            if media and media.get("path"):
                paths.append(str(media["path"]))
        return paths

    def _path_list(self, value: Any) -> list[str]:
        if isinstance(value, str):
            raw = re.split(r"[\r\n]+", value)
        else:
            raw = list(value or [])
        out = []
        seen = set()
        for item in raw:
            text = str(item or "").strip().strip('"')
            if text and text not in seen:
                seen.add(text); out.append(text)
        return out

    def _candidate_paths(self, data: dict[str, Any], max_items: int = 5000) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        seen: set[str] = set()
        def add(path: Any, **meta: Any) -> None:
            if len(out) >= max_items:
                return
            text = str(path or "").strip()
            if not text:
                return
            key = str(Path(text).expanduser().resolve(strict=False)).lower()
            if key in seen:
                return
            seen.add(key)
            out.append({"path": text, **meta})
        for media_id in data.get("media_ids") or []:
            row = self.db.query_one("SELECT * FROM media WHERE id=? AND active=1", (int(media_id),))
            if row:
                add(row.get("path"), source="media_ids", media_id=int(row["id"]), metadata={"dataset_id": row.get("dataset_id")})
        if data.get("dataset_id"):
            rows = self.db.query("SELECT * FROM media WHERE dataset_id=? AND active=1 AND media_type='image' ORDER BY id ASC LIMIT ?", (int(data["dataset_id"]), max_items))
            for row in rows:
                add(row.get("path"), source="dataset", media_id=int(row["id"]), metadata={"dataset_id": row.get("dataset_id")})
        if data.get("branch_id") and self.global_dataset is not None:
            payload = self.global_dataset.branch_items(int(data["branch_id"]))
            for row in payload.get("items") or []:
                media_path = row.get("media_path") or row.get("original_path")
                add(media_path, source="branch", global_asset_id=row.get("global_asset_id"), branch_item_id=row.get("id"), metadata={"branch_id": data.get("branch_id"), "role": row.get("role")})
        if data.get("branch_name") and self.global_dataset is not None:
            try:
                branch = self.global_dataset.resolve_branch(branch_name=str(data["branch_name"]), create=False)
                payload = self.global_dataset.branch_items(int(branch["id"]))
                for row in payload.get("items") or []:
                    media_path = row.get("media_path") or row.get("original_path")
                    add(media_path, source="branch", global_asset_id=row.get("global_asset_id"), branch_item_id=row.get("id"), metadata={"branch_id": branch.get("id"), "role": row.get("role")})
            except Exception:
                pass
        folder = str(data.get("folder") or "").strip()
        if folder:
            root = Path(folder).expanduser()
            if not root.exists():
                raise FileNotFoundError(str(root))
            recursive = bool(data.get("recursive", True))
            iterator = root.rglob("*") if recursive else root.glob("*")
            for p in iterator:
                if len(out) >= max_items:
                    break
                if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS:
                    add(p, source="folder", metadata={"folder": str(root)})
        return out[:max_items]
