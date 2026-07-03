from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from ..database import Database
from ..schemas import AugmentRequest, ExternalImageToolRequest
from ..utils import average_hash, classify_media, image_size, sha256_file
from .media_service import MediaService
from .external_app_service import ExternalAppService


class AugmentationService:
    def __init__(self, db: Database, media: MediaService, external_apps: ExternalAppService | None = None):
        self.db = db
        self.media = media
        self.external_apps = external_apps

    def _target_media_ids(self, request: AugmentRequest) -> list[int]:
        if request.media_ids:
            return request.media_ids
        if request.dataset_id:
            rows = self.db.query(
                "SELECT id FROM media WHERE dataset_id=? AND active=1 AND media_type IN ('image','animation')",
                (request.dataset_id,),
            )
            return [row["id"] for row in rows]
        return []

    def _apply(self, im: Image.Image, op: str, value: Any) -> Image.Image:
        op = (op or "").strip().lower()
        if op in {"flip_horizontal", "hflip", "mirror"} and value:
            return ImageOps.mirror(im)
        if op in {"flip_vertical", "vflip"} and value:
            return ImageOps.flip(im)
        if op in {"rotate", "rotate_degrees"} and value:
            return im.rotate(float(value), expand=True)
        if op == "brightness" and value is not None and value != "":
            return ImageEnhance.Brightness(im).enhance(float(value))
        if op == "contrast" and value is not None and value != "":
            return ImageEnhance.Contrast(im).enhance(float(value))
        if op == "saturation" and value is not None and value != "":
            return ImageEnhance.Color(im).enhance(float(value))
        if op == "sharpness" and value is not None and value != "":
            return ImageEnhance.Sharpness(im).enhance(float(value))
        if op in {"sharpen", "unsharp"} and value:
            radius = 2 if value is True else max(0.1, float(value))
            return im.filter(ImageFilter.UnsharpMask(radius=radius, percent=160, threshold=3))
        if op == "denoise" and value:
            size = 3 if value is True else max(3, int(value) | 1)
            return im.filter(ImageFilter.MedianFilter(size=size))
        if op in {"grayscale", "greyscale"} and value:
            return ImageOps.grayscale(im).convert("RGB")
        if op == "autocontrast" and value:
            return ImageOps.autocontrast(im)
        if op == "equalize" and value:
            return ImageOps.equalize(im)
        if op == "invert" and value:
            return ImageOps.invert(im)
        if op == "crop_square" and value:
            side = min(im.width, im.height)
            left = (im.width - side) // 2
            top = (im.height - side) // 2
            return im.crop((left, top, left + side, top + side))
        if op == "crop_rect" and value:
            rect = value if isinstance(value, dict) else {}
            x = int(rect.get("x", 0)); y = int(rect.get("y", 0)); w = int(rect.get("w", im.width)); h = int(rect.get("h", im.height))
            return im.crop((max(0, x), max(0, y), min(im.width, x + w), min(im.height, y + h)))
        if op in {"resize_long_side", "long_side"} and value:
            target = int(value)
            if target > 0:
                scale = target / max(im.width, im.height)
                return im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.Resampling.LANCZOS)
        if op in {"upscale_lanczos", "pil_upscale"} and value:
            factor = float(value)
            if factor > 0 and factor != 1.0:
                return im.resize((max(1, int(im.width * factor)), max(1, int(im.height * factor))), Image.Resampling.LANCZOS)
        if op == "pad_square" and value:
            side = max(im.width, im.height)
            bg = Image.new("RGB", (side, side), (255, 255, 255))
            bg.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
            return bg
        return im

    def run(self, request: AugmentRequest, progress) -> dict[str, Any]:
        media_ids = self._target_media_ids(request)
        if not media_ids:
            return {"created": 0, "message": "No image media selected"}
        output_dir = Path(request.output_dir or "outputs/augmentations").expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        created: list[str] = []
        for idx, media_id in enumerate(media_ids, start=1):
            media = self.media.get(media_id)
            if not media or media.media_type not in {"image", "animation"}:
                continue
            source = Path(media.path)
            try:
                with Image.open(source) as im:
                    im = ImageOps.exif_transpose(im).convert("RGB")
                    out = im
                    suffix_bits = []
                    for op, value in request.operations.items():
                        before = out
                        out = self._apply(out, op, value)
                        if out is not before or value:
                            suffix_bits.append(op)
                    suffix = "_" + "_".join(suffix_bits) if suffix_bits else "_copy"
                    ext = (request.output_format or "jpg").lower().lstrip(".")
                    target = output_dir / f"{source.stem}{suffix}.{ext}"
                    save_kwargs = {"quality": int(request.quality or 95)} if ext in {"jpg", "jpeg", "webp"} else {}
                    if ext == "png":
                        save_kwargs = {"compress_level": 0}
                    out.save(target, **save_kwargs)
                    created.append(str(target))
                    if request.attach_to_dataset and request.dataset_id:
                        width, height = image_size(target)
                        self.db.upsert_media(
                            {
                                "dataset_id": request.dataset_id,
                                "path": str(target),
                                "relative_path": target.name,
                                "media_type": classify_media(target),
                                "ext": target.suffix.lower().lstrip("."),
                                "width": width,
                                "height": height,
                                "size_bytes": target.stat().st_size,
                                "sha256": sha256_file(target),
                                "phash": average_hash(target),
                                "tag_path": str(target.with_suffix(".txt")),
                                "caption_path": str(target.with_suffix(".caption")),
                            }
                        )
            except Exception as exc:
                created.append(f"ERROR:{source}:{exc}")
            progress(idx / len(media_ids), f"Augmented {idx}/{len(media_ids)}")
        return {"created": len([x for x in created if not x.startswith("ERROR:")]), "outputs": created}

    def run_external_tool(self, request: ExternalImageToolRequest, progress) -> dict[str, Any]:
        if self.external_apps is None:
            raise RuntimeError("External application service is not configured.")
        return self.external_apps.launch(request, progress)
