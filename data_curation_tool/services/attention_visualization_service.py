from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AttentionVisualizationService:
    """Tag/attention visualization planning and lightweight artifact generation.

    The old tool exposed Grad-CAM / U-Net / t-SNE / cross-attention style views.
    This service restores that feature surface as a stable backend contract:
    deterministic placeholder/manifest generation works immediately, while
    model-specific integrations can plug in gradients, ViT attention, diffusion
    cross-attention maps, or embedding coordinates as those adapters mature.
    """

    METHODS: list[dict[str, Any]] = [
        {
            "key": "classifier_gradcam",
            "label": "Classifier Grad-CAM / CAM heatmap",
            "category": "classification",
            "description": "Visualize where a classifier/tagger focused for a selected tag. Supports legacy ViT/classifier contracts and future model-specific Grad-CAM adapters.",
            "requires_loaded_model": True,
            "output_types": ["overlay_png", "manifest_json"],
        },
        {
            "key": "vit_attention_rollout",
            "label": "ViT/SigLIP attention rollout",
            "category": "classification",
            "description": "Roll up ViT/SigLIP-style attention into a spatial saliency map for a tag or model prediction.",
            "requires_loaded_model": True,
            "output_types": ["overlay_png", "manifest_json"],
        },
        {
            "key": "hydra_cam_attention",
            "label": "Hydra CAM attention / PCA contract",
            "category": "classification",
            "description": "Hydra 3.5-compatible CAM/PCA visualization handoff for tag-level classifier attention.",
            "requires_loaded_model": True,
            "output_types": ["overlay_png", "manifest_json", "native_hydra_handoff"],
        },
        {
            "key": "diffusion_unet_cross_attention",
            "label": "Diffusion U-Net cross-attention heatmap",
            "category": "diffusion",
            "description": "Token/tag-to-pixel heatmap contract for diffusion pipelines that expose U-Net or transformer cross-attention tensors.",
            "requires_loaded_model": True,
            "output_types": ["overlay_png", "manifest_json", "attention_tensor_ref"],
        },
        {
            "key": "tsne_embedding_map",
            "label": "t-SNE / embedding similarity map",
            "category": "embedding",
            "description": "Project image/tag embeddings into a review map for clusters, outliers, and tag consistency checks.",
            "requires_loaded_model": False,
            "output_types": ["manifest_json", "scatter_json", "png_preview"],
        },
        {
            "key": "tag_mask_overlay",
            "label": "Tag mask/region overlay",
            "category": "annotation",
            "description": "Use existing masks/boxes/segmentations to create a tag-region overlay when no differentiable attention adapter is available.",
            "requires_loaded_model": False,
            "output_types": ["overlay_png", "manifest_json"],
        },
    ]

    def __init__(self, paths: Any, media_service: Any | None = None, model_service: Any | None = None):
        self.paths = paths
        self.media = media_service
        self.models = model_service
        self.root = Path(paths.outputs) / "attention_visualizations"
        self.root.mkdir(parents=True, exist_ok=True)
        self._native_attention_cache: dict[str, Any] = {}

    def capabilities(self) -> dict[str, Any]:
        return {
            "methods": list(self.METHODS),
            "feature_keys": [m["key"] for m in self.METHODS],
            "supports": [
                "gradcam",
                "class_activation_map",
                "vit_attention_rollout",
                "hydra_cam_attention",
                "hydra_native_cam_overlay",
                "hydra_demo_style_signed_cam",
                "hydra_pca_handoff",
                "diffusion_unet_cross_attention",
                "tsne_embedding_projection",
                "tag_region_overlay",
            ],
            "artifact_root": str(self.root),
            "note": "Hydra-style signed CAM overlays are supported when a compatible local Hydra model is available; otherwise the service falls back to a deterministic signed heatmap layer without changing the API.",
        }


    def artifact_path(self, name: str) -> Path:
        clean = Path(str(name or "")).name
        path = (self.root / clean).resolve()
        root = self.root.resolve()
        if root not in path.parents and path != root:
            raise ValueError("Invalid attention visualization artifact path.")
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(clean)
        return path

    def artifact_url(self, path: str | None) -> str | None:
        if not path:
            return None
        return f"/api/attention-visualization/artifact/{Path(path).name}"

    def plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        method = str(payload.get("method") or "classifier_gradcam").strip()
        if method not in {m["key"] for m in self.METHODS}:
            raise ValueError(f"Unknown attention visualization method: {method}")
        tag = str(payload.get("tag") or payload.get("prompt") or "").strip()
        model_name = str(payload.get("model_name") or "").strip()
        try:
            cam_depth = int(payload.get("cam_depth") or 1)
        except Exception:
            cam_depth = 1
        cam_depth = max(1, min(27, cam_depth))
        media_ids = [int(x) for x in (payload.get("media_ids") or []) if str(x).strip().isdigit()]
        row = next(m for m in self.METHODS if m["key"] == method)
        steps: list[dict[str, Any]] = [
            {"id": "resolve_media", "label": "Resolve selected image(s)", "required": True},
            {"id": "normalize_tag", "label": "Normalize selected tag/prompt/token to the active tag text mode", "required": bool(tag)},
        ]
        if row.get("requires_loaded_model"):
            steps.append({"id": "load_or_select_model", "label": "Use a loaded compatible model or queue model load", "required": True, "model_name": model_name or None})
        if method == "diffusion_unet_cross_attention":
            steps.append({"id": "capture_cross_attention", "label": "Capture token attention tensors from diffusion U-Net/transformer hooks", "required": True})
        elif method == "tsne_embedding_map":
            steps.append({"id": "embed_and_project", "label": "Embed selected images/tags and project to t-SNE/UMAP-like review coordinates", "required": True})
        elif method == "hydra_cam_attention":
            steps.append({"id": "compute_hydra_signed_cam", "label": "Compute Hydra demo-style signed CAM when a local Hydra runtime is available", "required": True, "cam_depth": cam_depth})
        else:
            steps.append({"id": "compute_heatmap", "label": "Compute Grad-CAM/CAM/attention rollout or use fallback signed region overlay", "required": True})
        steps.append({"id": "write_artifacts", "label": "Write overlay image and manifest under outputs/attention_visualizations", "required": True})
        return {
            "ok": True,
            "method": method,
            "label": row.get("label"),
            "tag": tag,
            "model_name": model_name,
            "cam_depth": cam_depth,
            "media_ids": media_ids,
            "steps": steps,
            "warnings": [] if media_ids else ["No media selected; execution will require media_ids or image_path."],
        }

    def run(self, payload: dict[str, Any], progress=None) -> dict[str, Any]:
        plan = self.plan(payload)
        if progress:
            progress(0.05, "Planning attention visualization")
        image_path = str(payload.get("image_path") or "").strip()
        media_ids = plan.get("media_ids") or []
        if not image_path and media_ids and self.media:
            try:
                if hasattr(self.media, "get_media"):
                    item = self.media.get_media(int(media_ids[0]))
                else:
                    item = self.media.get(int(media_ids[0]))
                image_path = str((getattr(item, "path", "") if item is not None else "") or (item.get("path") if isinstance(item, dict) else ""))
            except Exception:
                image_path = ""
        if not image_path:
            # No image path is still useful for t-SNE/global planning; write a manifest only.
            return self._write_manifest(plan, payload, overlay_path=None, progress=progress)
        if progress:
            progress(0.35, "Creating heatmap overlay artifact")
        image_path_obj = Path(image_path)
        created = self._try_model_specific_overlay(image_path_obj, plan, payload)
        if created is None:
            created = self._create_fallback_overlay(image_path_obj, plan, payload)
        if isinstance(created, dict):
            overlay_path = created.get("overlay_path")
            heatmap_path = created.get("heatmap_path")
            if created.get("attention_source"):
                payload["attention_source"] = created.get("attention_source")
        else:
            overlay_path = created
            heatmap_path = None
        return self._write_manifest(plan, payload, overlay_path=overlay_path, heatmap_path=heatmap_path, progress=progress)

    def _artifact_stem(self, plan: dict[str, Any], payload: dict[str, Any]) -> str:
        raw = json.dumps({"plan": plan, "payload": payload, "at": _now()}, sort_keys=True, ensure_ascii=False)
        return f"attention_{plan.get('method','viz')}_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:12]}"

    @contextmanager
    def _temporary_sys_path(self, path: Path):
        text = str(path)
        inserted = False
        if text not in sys.path:
            sys.path.insert(0, text)
            inserted = True
        prior_cwd = Path.cwd()
        try:
            os.chdir(text)
            yield
        finally:
            try:
                os.chdir(prior_cwd)
            except Exception:
                pass
            if inserted:
                try:
                    sys.path.remove(text)
                except ValueError:
                    pass

    def _selected_hydra_repo_path(self, model_name: str) -> Path | None:
        if not self.models or not hasattr(self.models, "registry"):
            return None
        registry = self.models.registry
        name = model_name or "redrocket-hydra-3-5"
        loaded = getattr(registry, "_loaded", {}) if registry is not None else {}
        adapter = loaded.get(name) or loaded.get("redrocket-hydra-3-5")
        repo_path = getattr(adapter, "repo_path", None)
        if repo_path:
            path = Path(str(repo_path)).expanduser()
            if path.exists():
                return path
        try:
            record = registry.get_record(name)
            local = record.complete_local_dir(registry.model_root, registry.external_model_roots)
            if local and Path(local).exists():
                return Path(local)
        except Exception:
            pass
        return None

    def _try_model_specific_overlay(self, image_path: Path, plan: dict[str, Any], payload: dict[str, Any]) -> dict[str, str] | None:
        method = str(plan.get("method") or payload.get("method") or "")
        model_name = str(plan.get("model_name") or payload.get("model_name") or "")
        if method == "hydra_cam_attention" or model_name == "redrocket-hydra-3-5":
            return self._try_hydra_cam_overlay(image_path, plan, payload)
        return None

    def _try_hydra_cam_overlay(self, image_path: Path, plan: dict[str, Any], payload: dict[str, Any]) -> dict[str, str] | None:
        tag = str(plan.get("tag") or payload.get("tag") or payload.get("prompt") or "").strip()
        if not tag:
            return None
        repo = self._selected_hydra_repo_path(str(plan.get("model_name") or payload.get("model_name") or "redrocket-hydra-3-5"))
        if not repo:
            return None
        model_file = repo / "models" / "hydra-3.5.safetensors"
        data_dir = repo / "data"
        if not model_file.exists() or not data_dir.exists():
            return None
        try:
            import numpy as np
            import torch
            with self._temporary_sys_path(repo):
                from hydra.image import patchify, unfold
                from hydra.model import load_model
            cache_key = f"hydra:{repo}:{payload.get('device') or 'auto'}"
            cached = self._native_attention_cache.get(cache_key)
            if cached is None:
                device = str(payload.get("device") or "auto")
                if device == "auto":
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                with self._temporary_sys_path(repo):
                    hydra_model = load_model(str(model_file), legacy_metadata_dir=str(data_dir))
                hydra_model.requires_grad_(False)
                hydra_model.to(device=device)
                cached = {"model": hydra_model, "device": device}
                self._native_attention_cache[cache_key] = cached
            hydra_model = cached["model"]
            cam_depth = int(plan.get("cam_depth") or payload.get("cam_depth") or 1)
            cam_depth = max(1, min(27, cam_depth))
            image_np = np.asarray(hydra_model.open_image(str(image_path)))
            prepared = hydra_model.from_srgb(patchify(image_np, 16), inplace=False)
            features = hydra_model.forward_features(
                prepared,
                intermediates=range(27 - cam_depth, 27),
                norm_intermediates=True,
            )
            intermediates = list(features.get("intermediates") or [])
            if not intermediates:
                return None
            try:
                hydra_model.select_labels(tag)
                hydra_model.head.logit = True  # type: ignore[attr-defined]
                with torch.enable_grad():
                    for intermediate in intermediates[-cam_depth:]:
                        intermediate.requires_grad_(True).retain_grad()
                        hydra_model.forward_head(intermediate, None)[0, 0].backward()
            finally:
                try:
                    hydra_model.select_labels(None)
                except Exception:
                    pass
                try:
                    hydra_model.head.logit = False  # type: ignore[attr-defined]
                except Exception:
                    pass
            cam_1d = None
            for intermediate in intermediates[-cam_depth:]:
                if intermediate.grad is None:
                    continue
                patch_grad = (intermediate.grad.float() * intermediate.sign()).sum(dim=(0, 2))
                intermediate.grad = None
                cam_1d = patch_grad if cam_1d is None else cam_1d.add(patch_grad)
            if cam_1d is None:
                return None
            cam_2d = unfold(cam_1d, (image_np.shape[0] // 16, image_np.shape[1] // 16)).detach().cpu().numpy()
            return self._write_signed_cam_layers(Path(image_path), cam_2d, plan, payload, source="native_hydra_demo_cam")
        except Exception as exc:
            payload.setdefault("attention_warnings", []).append(f"Hydra native CAM unavailable; using fallback overlay: {exc}")
            return None

    def _normalize_cam_array(self, cam: Any, width: int, height: int):
        import numpy as np
        arr = np.asarray(cam, dtype=np.float32)
        if arr.ndim > 2:
            arr = arr.squeeze()
        if arr.ndim != 2 or arr.size == 0:
            arr = np.zeros((max(1, height // 16), max(1, width // 16)), dtype=np.float32)
        finite = np.isfinite(arr)
        if not finite.all():
            arr = np.where(finite, arr, 0.0)
        max_abs = float(np.max(np.abs(arr))) if arr.size else 0.0
        if max_abs > 1e-8:
            arr = arr / max_abs
        return arr

    def _write_signed_cam_layers(self, image_path: Path, cam: Any, plan: dict[str, Any], payload: dict[str, Any], *, source: str = "signed_cam") -> dict[str, str] | None:
        try:
            import numpy as np
            from PIL import Image, ImageDraw, ImageFilter
        except Exception:
            return None
        if not image_path.exists():
            return None
        stem = self._artifact_stem(plan, payload)
        overlay_path = self.root / f"{stem}_overlay.png"
        heatmap_path = self.root / f"{stem}_heatmap.png"
        img = Image.open(image_path).convert("RGBA")
        w, h = img.size
        long_side = max(w, h)
        if long_side > 1800:
            scale = 1800 / long_side
            img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
            w, h = img.size
        arr = self._normalize_cam_array(cam, w, h)
        # Resize low-resolution patch CAMs with nearest-neighbor first to keep
        # the patch grid legible, then blur slightly like the Hydra demo overlay.
        heat_l = Image.fromarray(np.uint8(np.clip((arr + 1.0) * 127.5, 0, 255)), "L").resize((w, h), Image.Resampling.NEAREST)
        signed = (np.asarray(heat_l, dtype=np.float32) / 127.5) - 1.0
        mag = np.clip(np.abs(signed), 0, 1)
        alpha_scale = float(payload.get("alpha_scale") or 0.58)
        alpha = np.uint8(np.clip(mag ** 0.78 * 255 * max(0.05, min(1.0, alpha_scale)), 0, 255))
        red = np.uint8(np.clip((-signed) * 255, 0, 255))
        green = np.uint8(np.clip(signed * 255, 0, 255))
        rgba = np.dstack([red, green, np.zeros_like(red, dtype=np.uint8), alpha])
        heat = Image.fromarray(rgba, "RGBA").filter(ImageFilter.GaussianBlur(max(1, min(w, h) // 220)))
        # Hydra demo blends the base image toward grayscale so signed red/green
        # CAM polarity remains readable over busy images.
        gray_base = Image.blend(img, img.convert("L").convert("RGBA"), 0.33)
        overlay = Image.alpha_composite(gray_base, heat)
        if source:
            try:
                draw = ImageDraw.Draw(overlay)
                draw.text((w - 8, h - 8), source.replace("_", " "), anchor="rd", fill=(180, 215, 255, 210))
            except Exception:
                pass
        heat.save(heatmap_path)
        overlay.save(overlay_path)
        return {"overlay_path": str(overlay_path), "heatmap_path": str(heatmap_path), "attention_source": source}

    def _create_fallback_overlay(self, image_path: Path, plan: dict[str, Any], payload: dict[str, Any]) -> dict[str, str] | None:
        try:
            import numpy as np
        except Exception:
            return None
        if not image_path.exists():
            return None
        from PIL import Image
        with Image.open(image_path) as img_probe:
            w, h = img_probe.size
        tag = str(plan.get("tag") or payload.get("tag") or payload.get("prompt") or "attention")
        seed = int(hashlib.sha1(tag.encode("utf-8", "ignore")).hexdigest()[:8], 16)
        grid_w = max(8, min(96, w // 16 or 8))
        grid_h = max(8, min(96, h // 16 or 8))
        yy, xx = np.mgrid[0:grid_h, 0:grid_w].astype(np.float32)
        cam = np.zeros((grid_h, grid_w), dtype=np.float32)
        for i in range(7):
            angle = (seed % 360 + i * 71) * math.pi / 180.0
            cx = (0.50 + 0.32 * math.cos(angle + i * 0.21)) * (grid_w - 1)
            cy = (0.50 + 0.30 * math.sin(angle * 1.27 + i * 0.33)) * (grid_h - 1)
            sigma = max(1.4, min(grid_w, grid_h) * (0.13 + ((seed >> (i % 12)) & 3) * 0.018))
            sign = 1.0 if i % 2 == 0 else -0.62
            cam += sign * np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2.0 * sigma ** 2)))
        return self._write_signed_cam_layers(image_path, cam, plan, payload, source="fallback_signed_cam")

    def _write_manifest(self, plan: dict[str, Any], payload: dict[str, Any], overlay_path: str | None, heatmap_path: str | None = None, progress=None) -> dict[str, Any]:
        if progress:
            progress(0.85, "Writing attention visualization manifest")
        stem = Path(overlay_path).stem if overlay_path else self._artifact_stem(plan, payload)
        manifest_path = self.root / f"{stem}.json"
        row = {
            "ok": True,
            "created_at": _now(),
            "plan": plan,
            "payload": payload,
            "overlay_path": overlay_path,
            "overlay_url": self.artifact_url(overlay_path),
            "heatmap_path": heatmap_path,
            "heatmap_url": self.artifact_url(heatmap_path),
            "manifest_path": str(manifest_path),
            "manifest_url": self.artifact_url(str(manifest_path)),
            "status": "artifact_created" if overlay_path else "manifest_created",
            "fallback": not bool((payload.get("attention_source") or "").startswith("native")) if isinstance(payload, dict) else True,
            "attention_source": payload.get("attention_source") if isinstance(payload, dict) else None,
            "attention_warnings": payload.get("attention_warnings", []) if isinstance(payload, dict) else [],
            "note": "Hydra-style signed CAM overlays use green for positive evidence and red for negative evidence when native tensors are available; otherwise a deterministic signed fallback heatmap is used.",
        }
        manifest_path.write_text(json.dumps(row, indent=2, ensure_ascii=False), encoding="utf-8")
        if progress:
            progress(1.0, "Attention visualization complete")
        return row
