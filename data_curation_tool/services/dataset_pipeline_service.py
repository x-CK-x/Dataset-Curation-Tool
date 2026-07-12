from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..paths import AppPaths
from ..utils import read_text_if_exists, save_json, tag_string
from .global_dataset_service import GlobalDatasetService

SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_name(value: str, fallback: str = "item") -> str:
    clean = SAFE_NAME_RE.sub("_", str(value or "").strip()).strip("._-")
    return clean or fallback


def _split_tags(value: str | list[str] | tuple[str, ...] | None) -> list[str]:
    if isinstance(value, (list, tuple)):
        raw = [str(x) for x in value]
    else:
        raw = re.split(r"[,\n]+", str(value or ""))
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        tag = str(item or "").strip()
        if not tag:
            continue
        key = tag.lower()
        if key not in seen:
            seen.add(key)
            out.append(tag)
    return out


def _token_count(value: str) -> int:
    return len([x for x in re.split(r"[\s,]+", str(value or "")) if x.strip()])


DIFFUSION_TARGETS: list[dict[str, Any]] = [
    {
        "key": "sdxl",
        "label": "SDXL / Pony / SDXL-derived",
        "media": ["image"],
        "caption_style": "danbooru_tags_or_short_caption",
        "default_resolution": "1024px bucketed",
        "strengths": ["general image LoRA", "style", "character", "concept", "ControlNet conditioning"],
        "notes": "Keep trigger token first, then stable subject/style tags, then mutable scene tags. Works best with concise but complete captions.",
    },
    {
        "key": "illustrious",
        "label": "Illustrious / Illustrious-derived anime models",
        "media": ["image"],
        "caption_style": "ordered_danbooru_tags",
        "default_resolution": "1024px bucketed",
        "strengths": ["anime character", "style", "concept"],
        "notes": "Prefer canonical booru tags and preserve character/body/pose attributes that should transfer to generation.",
    },
    {
        "key": "noobai",
        "label": "NoobAI / NoobAI-derived anime models",
        "media": ["image"],
        "caption_style": "ordered_danbooru_tags",
        "default_resolution": "1024px bucketed",
        "strengths": ["anime character", "style", "concept"],
        "notes": "Use stable tag ordering and avoid overly verbose natural-language captions unless the trainer specifically expects them.",
    },
    {
        "key": "anima",
        "label": "Anima / anime diffusion derivatives",
        "media": ["image"],
        "caption_style": "ordered_tags_plus_optional_caption",
        "default_resolution": "768-1024px bucketed",
        "strengths": ["anime style", "character identity", "concept"],
        "notes": "Use booru tags for visual tokens and optional plain caption only where a target trainer supports dual caption fields.",
    },
    {
        "key": "seaart",
        "label": "SeaArt-style / hosted diffusion workflow target",
        "media": ["image"],
        "caption_style": "service_compatible_tags",
        "default_resolution": "service preset",
        "strengths": ["hosted dataset workflow", "style", "character"],
        "notes": "Treat as an external service target. Export sidecars and manifests; final training execution should happen through the service/tool interface.",
    },
    {
        "key": "krea2",
        "label": "Krea 2 / K2 image model target",
        "media": ["image"],
        "caption_style": "style_forward_caption_plus_references",
        "default_resolution": "provider/model preset",
        "strengths": ["style control", "moodboard/reference-driven outputs", "aesthetic direction"],
        "notes": "Prioritize style vocabulary, mood, medium, lighting, palette, composition, and reference-set consistency.",
    },
    {
        "key": "ideogram4",
        "label": "Ideogram 4 / Ideogram API target",
        "media": ["image"],
        "caption_style": "structured_json_or_precise_plain_caption",
        "default_resolution": "provider/model preset",
        "strengths": ["prompt fidelity", "text-in-image", "graphic design"],
        "notes": "Preserve text, typography, layout, object placement, and negative-space descriptors; structured captions are preferred for this target.",
    },
    {
        "key": "flux1_dev",
        "label": "FLUX.1 Dev",
        "media": ["image"],
        "caption_style": "natural_language_plus_key_tags",
        "default_resolution": "1024px bucketed",
        "strengths": ["prompt-faithful LoRA", "style", "character", "concept", "workflow handoff"],
        "notes": "Use natural-language captions plus stable trigger/key tags. Keep identity/style/concept-defining descriptors explicit and consistent across the branch.",
    },
    {
        "key": "flux1_schnell",
        "label": "FLUX.1 Schnell",
        "media": ["image"],
        "caption_style": "compact_natural_language_plus_key_tags",
        "default_resolution": "1024px bucketed",
        "strengths": ["fast target compatibility", "style/concept LoRA", "workflow handoff"],
        "notes": "Keep captions compact and prompt-portable; avoid long noisy tag lists when preparing fast-generation variants.",
    },
    {
        "key": "flux1_kontext_dev",
        "label": "FLUX.1 Kontext Dev",
        "media": ["image", "reference-image"],
        "caption_style": "instruction_caption_plus_reference_tags",
        "default_resolution": "reference-paired buckets",
        "strengths": ["image editing", "reference-conditioned adaptation", "IC-LoRA handoff"],
        "notes": "Describe reference input, target output, and transformation instruction for every example.",
    },
    {
        "key": "flux1_fill_dev",
        "label": "FLUX.1 Fill Dev",
        "media": ["image", "mask"],
        "caption_style": "masked_region_caption_plus_context",
        "default_resolution": "mask-paired buckets",
        "strengths": ["inpaint", "outpaint", "masked edits"],
        "notes": "Track mask/region paths and separate context from the intended filled region.",
    },
    {
        "key": "flux1_depth_dev",
        "label": "FLUX.1 Depth Dev",
        "media": ["image", "depth-map"],
        "caption_style": "caption_plus_depth_condition",
        "default_resolution": "condition-paired buckets",
        "strengths": ["depth conditioning", "ControlNet-style prep", "structure preservation"],
        "notes": "Reject items where depth condition and target image do not align.",
    },
    {
        "key": "flux1_canny_dev",
        "label": "FLUX.1 Canny Dev",
        "media": ["image", "edge-map"],
        "caption_style": "caption_plus_edge_condition",
        "default_resolution": "condition-paired buckets",
        "strengths": ["edge conditioning", "line/structure control"],
        "notes": "Store edge-map lineage and caption visible target semantics, not only the edge shape.",
    },
    {
        "key": "flux1_redux_dev",
        "label": "FLUX.1 Redux Dev",
        "media": ["image", "reference-image"],
        "caption_style": "reference_similarity_caption",
        "default_resolution": "reference-paired buckets",
        "strengths": ["image variation", "reference similarity", "style/reference consistency"],
        "notes": "Record which traits must be preserved from the reference and which traits are allowed to vary.",
    },
    {
        "key": "chroma_flux",
        "label": "Chroma / FLUX-tuned target",
        "media": ["image"],
        "caption_style": "natural_language_plus_booru_compatible_tags",
        "default_resolution": "1024px bucketed",
        "strengths": ["illustration/anime FLUX workflows", "style", "character", "concept"],
        "notes": "Use FLUX-style natural language while preserving booru-compatible descriptors for visual specificity and cross-dataset consistency.",
    },
    {
        "key": "wan2_2",
        "label": "Wan 2.2 video diffusion target",
        "media": ["image", "video"],
        "caption_style": "shot_caption_plus_motion_tags",
        "default_resolution": "video buckets / trainer preset",
        "strengths": ["text-to-video", "image-to-video", "video-to-video", "motion/style LoRA"],
        "notes": "Include shot type, camera motion, temporal action, subject continuity, frame quality, and duration/fps metadata.",
    },
    {
        "key": "ltx2_3",
        "label": "LTX 2.3 / LTX-2 LoRA + IC-LoRA target",
        "media": ["image", "video", "audio-video"],
        "caption_style": "clip_caption_plus_task_prompt",
        "default_resolution": "trainer preset",
        "strengths": ["video LoRA", "IC-LoRA", "audio-video relationship", "reference-driven transforms"],
        "notes": "For IC-LoRA, captions must describe the relationship between condition/reference input and target output, not just the visible target frame.",
    },
]

ADAPTER_TYPES: list[dict[str, Any]] = [
    {
        "key": "lora",
        "label": "LoRA / low-rank adapter",
        "purpose": "Lightweight adaptation of a base diffusion model.",
        "dataset_shape": "single image/video item -> caption/tag sidecar",
        "critical_fields": ["trigger token", "stable identity/style/concept descriptors", "editable scene descriptors"],
    },
    {
        "key": "ic_lora",
        "label": "IC-LoRA / in-context LoRA",
        "purpose": "Reference/condition-driven adaptation where input-output relationships matter.",
        "dataset_shape": "condition/reference item(s) + target item + task prompt/caption",
        "critical_fields": ["condition description", "target description", "relationship/task instruction", "identity preservation policy"],
    },
    {
        "key": "controlnet",
        "label": "ControlNet / conditioning model",
        "purpose": "Train a model to respond to an external conditioning image/map.",
        "dataset_shape": "image + conditioning_image + caption",
        "critical_fields": ["conditioning type", "conditioning path", "image path", "caption"],
    },
    {
        "key": "embedding",
        "label": "Embedding / textual inversion",
        "purpose": "Learn a compact token embedding from a small concept/style/subject set.",
        "dataset_shape": "small curated item set + special token + captions that exclude what the token should learn",
        "critical_fields": ["special token", "initialization text", "caption policy", "regularization/negative examples"],
    },
]

DATASET_GOALS: list[dict[str, Any]] = [
    {
        "key": "style",
        "label": "Style",
        "objective": "Teach visual treatment without binding it to one subject identity.",
        "keep_tags": ["medium", "line quality", "rendering style", "color palette", "lighting", "composition", "texture", "camera/lens", "era/genre"],
        "downweight_or_remove": ["unique character names", "overly specific one-off props", "single-image accidents"],
        "caption_rule": "The trigger token should represent the style. Captions should still describe subjects and scene contents so the style is not forced to memorize them.",
        "selection_rule": "Use diverse subjects, poses, backgrounds, and compositions that share the same style signal.",
    },
    {
        "key": "character",
        "label": "Character",
        "objective": "Teach identity, body structure, recurring outfit/markings, and recognizable features while allowing flexible scenes.",
        "keep_tags": ["species/body type", "face shape", "hair/fur/skin details", "eyes", "markings", "recurring clothing/accessories", "proportions", "signature colors"],
        "downweight_or_remove": ["background-only details", "unwanted style artifacts", "random one-off lighting unless desired"],
        "caption_rule": "Place the trigger token early. Preserve tags for identity-critical anatomy/outfit/markings even when they feel repetitive; remove tags for features that should be learned implicitly only if every image has them and they reduce prompt control.",
        "selection_rule": "Prefer clean, varied angles and poses with enough close-ups/full-body views to define identity.",
    },
    {
        "key": "character_style",
        "label": "Character in Specific Style / OC + Style",
        "objective": "Teach both identity and a specific visual treatment while protecting the character's body structure.",
        "keep_tags": ["character trigger", "style trigger", "body/proportion descriptors", "signature design elements", "medium/rendering", "palette", "line/render traits"],
        "downweight_or_remove": ["scene-specific noise", "conflicting style descriptors", "extra characters unless intentionally trained"],
        "caption_rule": "Use two explicit anchors: one token for the character and one token for the style. Keep body-structure tags because the goal is not only face/outfit recognition; it is the character as rendered in that style.",
        "selection_rule": "Use examples where both identity and style are visible. Avoid mixing unrelated styles unless the style token is meant to be broad.",
    },
    {
        "key": "concept",
        "label": "Concept",
        "objective": "Teach an object, scene idea, action, effect, material, pose family, or visual relationship.",
        "keep_tags": ["concept trigger", "object/action/effect descriptors", "scale", "materials", "interaction", "environment relationship", "viewpoint"],
        "downweight_or_remove": ["identity-specific tags unless required", "style tags unless style is part of the concept"],
        "caption_rule": "Make the concept explicit and separate from surrounding subjects/style. If the concept is a relation or action, describe both entities and the relation consistently.",
        "selection_rule": "Use enough variation to isolate the concept from one specific subject/background/style.",
    },
]

TRAINING_TOOL_INTERFACES: list[dict[str, Any]] = [
    {
        "key": "kohya_ss",
        "label": "Kohya SS / sd-scripts",
        "kind": "external_training_tool",
        "mcp_name": "dct-kohya-ss",
        "supports": ["SD1.x", "SDXL", "LoRA", "LyCORIS", "DreamBooth-style folder exports"],
        "export_formats": ["folder_with_caption_sidecars", "toml_config", "json_manifest"],
        "manual_steps": ["Install kohya_ss separately.", "Point the export folder or generated config at the branch export produced by this tool."],
    },
    {
        "key": "onetrainer",
        "label": "OneTrainer",
        "kind": "external_training_tool",
        "mcp_name": "dct-onetrainer",
        "supports": ["SDXL", "Flux-like workflows", "LoRA", "embedding", "ControlNet-style configs"],
        "export_formats": ["folder_with_caption_sidecars", "json_manifest"],
        "manual_steps": ["Install OneTrainer separately.", "Import or point the project config at the branch export folder."],
    },
    {
        "key": "diffusers_scripts",
        "label": "Hugging Face Diffusers training scripts",
        "kind": "script_interface",
        "mcp_name": "dct-diffusers-trainer",
        "supports": ["ControlNet", "Textual Inversion", "LoRA", "custom script entrypoints"],
        "export_formats": ["metadata_jsonl", "image_condition_caption_manifest", "accelerate_config_stub"],
        "manual_steps": ["Install the target diffusers trainer environment separately.", "Use the generated manifest/config as the dataset input."],
    },
    {
        "key": "ltx_trainer",
        "label": "LTX Trainer / LTX-2.x LoRA + IC-LoRA",
        "kind": "video_training_tool",
        "mcp_name": "dct-ltx-trainer",
        "supports": ["LTX-2.3", "video LoRA", "IC-LoRA", "audio-video datasets"],
        "export_formats": ["video_clip_manifest", "condition_target_pair_manifest", "task_prompt_jsonl"],
        "manual_steps": ["Install the official or compatible LTX trainer separately.", "Ensure clips are trimmed, captioned, and paired before training."],
    },
    {
        "key": "comfyui_training_nodes",
        "label": "ComfyUI training/custom-node bridge",
        "kind": "mcp_or_workflow_interface",
        "mcp_name": "dct-comfyui-training",
        "supports": ["workflow-driven preprocessing", "captioning", "upscaling", "some third-party training nodes"],
        "export_formats": ["workflow_input_manifest", "folder_with_sidecars"],
        "manual_steps": ["Install ComfyUI and any third-party training/preprocessing nodes manually.", "Queue workflows through the ComfyUI bridge."],
    },
    {
        "key": "cloud_training_service",
        "label": "Generic cloud/API training provider",
        "kind": "cloud_api_contract",
        "mcp_name": "dct-cloud-trainer",
        "supports": ["hosted LoRA training", "service-specific datasets", "artifact upload"],
        "export_formats": ["zip_bundle", "json_manifest", "provider_upload_plan"],
        "manual_steps": ["Configure provider API key/token profile.", "Review provider terms and dataset safety requirements before upload."],
    },
]

PIPELINE_STAGES: list[dict[str, Any]] = [
    {"key": "download", "label": "Download / source sync", "description": "Use downloader presets, logic filters, source tag dictionaries, and global dedupe."},
    {"key": "initial_label", "label": "Initial labeling", "description": "Use tag dictionary autocomplete, VLM/caption models, metadata import, and rule presets."},
    {"key": "quality_filter", "label": "Quality filtering", "description": "Cull duplicates, bad crops, low resolution, wrong subject, watermark-heavy, and off-goal data."},
    {"key": "augment_upscale", "label": "Augment + upscale", "description": "Queue augmentation/upscaling tools; register outputs as variants in the branch layer."},
    {"key": "secondary_label", "label": "Additional labeling", "description": "Re-label augmented outputs and preserve original/variant lineage."},
    {"key": "final_select", "label": "Final training selection", "description": "Freeze a branch manifest, sidecars, and export plan for an external trainer."},
]

REQUIRED_EXPLICIT_DESCRIPTOR_SETS: dict[str, list[str]] = {
    "identity": ["eye color", "hair/fur color", "body type", "species", "markings", "signature clothing", "proportions"],
    "style": ["medium", "line art", "rendering", "palette", "lighting", "texture", "composition"],
    "concept": ["trigger object/action", "material", "scale", "interaction", "viewpoint", "environment"],
    "video": ["shot type", "camera motion", "subject action", "temporal continuity", "duration/fps", "scene transition"],
    "control": ["conditioning type", "conditioning image/map", "target image", "caption alignment"],
}


class DatasetPipelineService:
    """Dataset automation planning, rule presets, readiness checks, and trainer handoff.

    This service does not train models.  It turns the global dataset/branch layer
    into reproducible branch exports, LLM-readable rule packets, and external
    training-tool manifests so training can happen in Kohya/OneTrainer/Diffusers/
    LTX/ComfyUI/cloud tools without mutating global originals.
    """

    def __init__(self, paths: AppPaths, global_dataset: GlobalDatasetService):
        self.paths = paths
        self.global_dataset = global_dataset
        self.root = paths.outputs / "dataset_pipeline"
        self.exports_root = self.root / "exports"
        self.rules_root = self.root / "rules"
        self.print_root = self.root / "3d_print"
        for folder in (self.root, self.exports_root, self.rules_root, self.print_root):
            folder.mkdir(parents=True, exist_ok=True)

    def catalog(self) -> dict[str, Any]:
        return {
            "targets": DIFFUSION_TARGETS,
            "adapter_types": ADAPTER_TYPES,
            "dataset_goals": DATASET_GOALS,
            "training_tool_interfaces": TRAINING_TOOL_INTERFACES,
            "pipeline_stages": PIPELINE_STAGES,
            "explicit_descriptor_sets": REQUIRED_EXPLICIT_DESCRIPTOR_SETS,
        }

    def build_rules(self, payload: Any) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        target_key = str(data.get("target_model") or "sdxl").strip().lower()
        adapter_key = str(data.get("adapter_type") or "lora").strip().lower()
        goal_key = str(data.get("dataset_goal") or "character").strip().lower()
        trigger = str(data.get("trigger_token") or "<trigger_token>").strip() or "<trigger_token>"
        style_trigger = str(data.get("style_trigger_token") or "<style_trigger>").strip() or "<style_trigger>"
        include_explicit = bool(data.get("include_explicit_descriptor_policy", True))
        additional_notes = str(data.get("additional_notes") or "").strip()
        target = self._lookup(DIFFUSION_TARGETS, target_key, "sdxl")
        adapter = self._lookup(ADAPTER_TYPES, adapter_key, "lora")
        goal = self._lookup(DATASET_GOALS, goal_key, "character")
        rules = self._compose_rules(target, adapter, goal, trigger, style_trigger, include_explicit, additional_notes)
        packet = {
            "created_at": now_iso(),
            "target_model": target,
            "adapter_type": adapter,
            "dataset_goal": goal,
            "trigger_token": trigger,
            "style_trigger_token": style_trigger if goal_key == "character_style" else "",
            "rules": rules,
            "llm_instruction": self._llm_instruction(target, adapter, goal, trigger, style_trigger, rules),
            "output_schema": {
                "media_id": "integer or source asset id",
                "keep": "boolean",
                "quality_score": "0.0-1.0",
                "caption": "final training caption or comma-separated tags",
                "tags": ["ordered", "training", "tags"],
                "warnings": ["missing trigger token", "ambiguous identity", "caption too long"],
                "required_manual_review": "boolean",
            },
        }
        name = f"{safe_name(target_key)}_{safe_name(adapter_key)}_{safe_name(goal_key)}_{safe_name(trigger)}.json"
        save_json(self.rules_root / name, packet)
        packet["rules_path"] = str((self.rules_root / name).resolve())
        return packet

    def _lookup(self, rows: list[dict[str, Any]], key: str, fallback: str) -> dict[str, Any]:
        for row in rows:
            if row.get("key") == key:
                return dict(row)
        for row in rows:
            if row.get("key") == fallback:
                return dict(row)
        return dict(rows[0]) if rows else {}

    def _compose_rules(self, target: dict[str, Any], adapter: dict[str, Any], goal: dict[str, Any], trigger: str, style_trigger: str, include_explicit: bool, additional_notes: str) -> list[dict[str, Any]]:
        goal_key = goal.get("key") or "character"
        rules: list[dict[str, Any]] = [
            {"id": "trigger-first", "severity": "required", "text": f"Place `{trigger}` at or near the beginning of every kept caption unless the export target uses a separate trigger-token field."},
            {"id": "no-original-mutation", "severity": "required", "text": "Never edit global original media. Write only branch sidecars, branch manifests, or variant outputs."},
            {"id": "consistent-tag-order", "severity": "required", "text": "Use deterministic tag order: trigger(s), subject/identity, style/medium, pose/action, clothing/accessories, scene/background, technical/quality, rating/safety if used."},
            {"id": "cross-file-uniformity", "severity": "required", "text": "When a visual trait appears consistently and is relevant to the target, keep the same descriptor vocabulary across all matching items."},
            {"id": "negative-learning-avoidance", "severity": "required", "text": "Remove or downweight one-off artifacts that should not be learned: compression damage, watermarks, accidental crops, random background debris, wrong characters, and inconsistent style noise."},
            {"id": "branch-reference-check", "severity": "recommended", "text": "Before final export, cross-reference related branch captions/tags for the same original asset or character/style family and reconcile terminology."},
        ]
        if goal_key == "style":
            rules.extend([
                {"id": "style-diversity", "severity": "required", "text": "Preserve subject diversity so the adapter learns style rather than memorizing a single subject."},
                {"id": "style-token-scope", "severity": "required", "text": "Use the trigger token for the style itself. Continue describing subjects/scenes normally so prompt control remains available."},
            ])
        elif goal_key == "character":
            rules.extend([
                {"id": "identity-critical-tags", "severity": "required", "text": "Keep identity-critical tags even when repetitive: species/body type, proportions, face/eye/hair/fur/skin details, markings, recurring outfit/accessories, and signature colors."},
                {"id": "identity-flexibility", "severity": "recommended", "text": "Keep pose, camera, background, and expression tags editable unless they are part of the character identity being trained."},
            ])
        elif goal_key == "character_style":
            rules.extend([
                {"id": "dual-token-policy", "severity": "required", "text": f"Use both `{trigger}` for the character and `{style_trigger}` for the style. Do not collapse identity and style into one ambiguous token unless the user explicitly wants that."},
                {"id": "body-structure-preservation", "severity": "required", "text": "Preserve body structure/proportion descriptors because the goal is the character in the style, not only a face or costume token."},
            ])
        elif goal_key == "concept":
            rules.extend([
                {"id": "concept-isolation", "severity": "required", "text": "Make the concept explicit and separate it from incidental subject/style/background details."},
                {"id": "relationship-captions", "severity": "recommended", "text": "For actions, poses, interactions, materials, effects, or scene relationships, describe the relationship consistently rather than only listing objects."},
            ])
        adapter_key = adapter.get("key") or "lora"
        if adapter_key == "ic_lora":
            rules.append({"id": "ic-lora-pairing", "severity": "required", "text": "Each example must preserve condition/reference input, target output, and a task prompt that states the intended transformation or relationship."})
        elif adapter_key == "controlnet":
            rules.append({"id": "controlnet-triplet", "severity": "required", "text": "Each example must include image path, conditioning image/map path, and caption. Reject examples where conditioning does not align with the target image."})
        elif adapter_key == "embedding":
            rules.append({"id": "embedding-caption-boundary", "severity": "required", "text": "Captions should describe what the special token should not absorb; leave the special token to represent the core subject/style/concept."})
        if target.get("key") in {"wan2_2", "ltx2_3"}:
            rules.append({"id": "video-temporal-policy", "severity": "required", "text": "For video, include shot type, camera motion, subject action, continuity, clip length/fps if known, and whether audio is relevant."})
        if target.get("key") == "ideogram4":
            rules.append({"id": "ideogram-structured-caption", "severity": "recommended", "text": "Prefer structured captions when possible: subject, style, layout, text content, typography, spatial relations, and rendering constraints."})
        if target.get("key") == "krea2":
            rules.append({"id": "krea-style-reference", "severity": "recommended", "text": "Prioritize style/moodboard vocabulary: mood, medium, palette, lighting, material, composition, and reference-set consistency."})
        target_key = target.get("key")
        if target_key in {"flux1_dev", "flux1_schnell", "chroma_flux"}:
            rules.append({"id": "flux-caption-policy", "severity": "required", "text": "Use natural-language captions plus concise key tags. Keep trigger tokens stable, preserve important visual descriptors, and avoid purely booru-only captions unless the selected trainer requires them."})
        if target_key in {"flux1_kontext_dev", "flux1_fill_dev", "flux1_depth_dev", "flux1_canny_dev", "flux1_redux_dev"}:
            rules.append({"id": "flux-condition-reference-policy", "severity": "required", "text": "Each example must preserve reference/condition/mask file paths and caption the relationship between the input condition and target output."})
        if include_explicit:
            rules.append({"id": "explicit-descriptor-preservation", "severity": "required", "text": "Do not silently remove precise descriptors that are necessary to distinguish the visible scene, anatomy, pose, relation, material, rating, or identity. If a descriptor is sensitive but visually required for training correctness, keep it in the branch sidecar and flag for manual review rather than dropping it."})
        if additional_notes:
            rules.append({"id": "user-notes", "severity": "required", "text": additional_notes})
        return rules

    def _llm_instruction(self, target: dict[str, Any], adapter: dict[str, Any], goal: dict[str, Any], trigger: str, style_trigger: str, rules: list[dict[str, Any]]) -> str:
        bullets = "\n".join(f"- [{r['severity']}] {r['text']}" for r in rules)
        return (
            "You are preparing final training captions/tags for a diffusion dataset branch.\n"
            f"Target model family: {target.get('label')} ({target.get('key')}).\n"
            f"Adapter/training artifact: {adapter.get('label')} ({adapter.get('key')}).\n"
            f"Dataset goal: {goal.get('label')} ({goal.get('key')}).\n"
            f"Primary trigger token: {trigger}.\n"
            + (f"Style trigger token: {style_trigger}.\n" if goal.get("key") == "character_style" else "")
            + "Rules:\n"
            + bullets
            + "\nReturn strict JSON matching the provided output_schema. Keep captions consistent across the dataset and flag anything uncertain for manual review."
        )

    def plan_pipeline(self, payload: Any) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        branch_name = str(data.get("branch_name") or "default").strip() or "default"
        rules = self.build_rules(data)
        plan = {
            "created_at": now_iso(),
            "branch_name": branch_name,
            "target_model": rules["target_model"],
            "adapter_type": rules["adapter_type"],
            "dataset_goal": rules["dataset_goal"],
            "trigger_token": rules["trigger_token"],
            "rules_path": rules.get("rules_path"),
            "stages": self._stage_plan(branch_name, rules, data),
            "recommended_integrations": self._recommended_integrations(rules),
        }
        out = self.root / "plans" / f"{safe_name(branch_name)}_{safe_name(rules['target_model']['key'])}_{safe_name(rules['dataset_goal']['key'])}.json"
        save_json(out, plan)
        plan["plan_path"] = str(out.resolve())
        return plan

    def _stage_plan(self, branch_name: str, rules: dict[str, Any], data: dict[str, Any]) -> list[dict[str, Any]]:
        target = rules["target_model"].get("key")
        adapter = rules["adapter_type"].get("key")
        base = []
        for stage in PIPELINE_STAGES:
            row = dict(stage)
            row["branch_name"] = branch_name
            row["automatable_now"] = stage["key"] in {"download", "initial_label", "quality_filter", "final_select"}
            row["requires_external_tool"] = stage["key"] in {"augment_upscale", "secondary_label"}
            row["outputs"] = []
            base.append(row)
        base[0]["outputs"] = ["global original asset", "source mapping", "branch link"]
        base[1]["outputs"] = ["editable .txt/.caption sidecars", "LLM rule packet", "manual review flags"]
        base[2]["outputs"] = ["keep/exclude decisions", "quality score", "duplicate/near-duplicate notes"]
        base[3]["outputs"] = ["variant media", "variant manifest", "lineage to original asset"]
        base[4]["outputs"] = ["variant sidecars", "condition-target pairs" if adapter in {"ic_lora", "controlnet"} else "updated caption sidecars"]
        base[5]["outputs"] = ["frozen branch manifest", "trainer export bundle", "external training-tool handoff"]
        if target in {"wan2_2", "ltx2_3"}:
            for row in base:
                row.setdefault("video_notes", []).append("Preserve clip metadata, motion/action captions, and audio/video relationship when present.")
        return base

    def _recommended_integrations(self, rules: dict[str, Any]) -> list[str]:
        target = rules["target_model"].get("key")
        adapter = rules["adapter_type"].get("key")
        names = ["comfyui_training_nodes", "cloud_training_service"]
        if adapter in {"lora", "embedding"} and target in {"sdxl", "illustrious", "noobai", "anima"}:
            names.insert(0, "kohya_ss")
            names.insert(1, "onetrainer")
        if adapter == "controlnet":
            names.insert(0, "diffusers_scripts")
        if target in {"flux1_dev", "flux1_schnell", "flux1_kontext_dev", "flux1_fill_dev", "flux1_depth_dev", "flux1_canny_dev", "flux1_redux_dev", "chroma_flux"}:
            names.insert(0, "diffusers_scripts")
            names.insert(1, "onetrainer")
        if target in {"wan2_2", "ltx2_3"}:
            names.insert(0, "ltx_trainer")
        seen: set[str] = set(); out: list[str] = []
        for item in names:
            if item not in seen:
                seen.add(item); out.append(item)
        return out

    def evaluate_branch(self, payload: Any) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        branch_id = data.get("branch_id")
        branch_name = str(data.get("branch_name") or "").strip()
        target = str(data.get("target_model") or "sdxl").strip().lower()
        adapter = str(data.get("adapter_type") or "lora").strip().lower()
        goal = str(data.get("dataset_goal") or "character").strip().lower()
        trigger = str(data.get("trigger_token") or "").strip()
        branch = self._resolve_branch(branch_id=branch_id, branch_name=branch_name)
        if not branch:
            return {"ok": False, "error": "Branch not found", "items": [], "metrics": {}, "recommendations": ["Create or select a global dataset branch first."]}
        items_payload = self.global_dataset.branch_items(int(branch["id"]))
        items = items_payload.get("items") or []
        rows: list[dict[str, Any]] = []
        tag_freq: dict[str, int] = {}
        trigger_hits = 0
        missing_caption = 0
        review_count = 0
        for item in items:
            tag_text = read_text_if_exists(Path(item.get("tag_path") or "")) if item.get("tag_path") else ""
            caption_text = read_text_if_exists(Path(item.get("caption_path") or "")) if item.get("caption_path") else ""
            tags = _split_tags(tag_text)
            caption = caption_text.strip()
            for tag in tags:
                tag_freq[tag.lower()] = tag_freq.get(tag.lower(), 0) + 1
            combined = (tag_text + "\n" + caption).lower()
            has_trigger = bool(trigger and trigger.lower() in combined)
            if has_trigger:
                trigger_hits += 1
            if not tags and not caption:
                missing_caption += 1
            warnings = self._item_warnings(tags, caption, trigger, target, adapter, goal)
            review = bool(warnings)
            review_count += 1 if review else 0
            rows.append({
                "branch_item_id": item.get("id"),
                "global_asset_id": item.get("global_asset_id"),
                "original_filename": item.get("original_filename"),
                "source_site": item.get("source_site"),
                "source_post_id": item.get("source_post_id"),
                "tag_count": len(tags),
                "caption_tokens": _token_count(caption),
                "has_trigger": has_trigger,
                "warnings": warnings,
                "needs_review": review,
                "tag_path": item.get("tag_path"),
                "caption_path": item.get("caption_path"),
            })
        total = max(1, len(items))
        metrics = {
            "branch_id": int(branch["id"]),
            "branch_name": branch.get("name"),
            "item_count": len(items),
            "trigger_coverage": trigger_hits / total if trigger else None,
            "missing_caption_or_tags": missing_caption,
            "manual_review_count": review_count,
            "manual_review_rate": review_count / total,
            "unique_tag_count": len(tag_freq),
            "top_tags": sorted(tag_freq.items(), key=lambda kv: (-kv[1], kv[0]))[:50],
            "target_model": target,
            "adapter_type": adapter,
            "dataset_goal": goal,
        }
        recommendations = self._branch_recommendations(metrics, trigger)
        report = {"ok": True, "metrics": metrics, "items": rows[:1000], "recommendations": recommendations}
        out = self.root / "reports" / f"{safe_name(branch.get('name'))}_{safe_name(target)}_{safe_name(goal)}_readiness.json"
        save_json(out, report)
        report["report_path"] = str(out.resolve())
        return report

    def _resolve_branch(self, *, branch_id: Any = None, branch_name: str = "") -> dict[str, Any] | None:
        try:
            if branch_id:
                return self.global_dataset.branch_detail(int(branch_id))
        except Exception:
            pass
        if branch_name:
            for row in self.global_dataset.branches():
                if str(row.get("name") or "").lower() == branch_name.lower():
                    return row
        return None

    def _item_warnings(self, tags: list[str], caption: str, trigger: str, target: str, adapter: str, goal: str) -> list[str]:
        warnings: list[str] = []
        combined = (", ".join(tags) + " " + caption).strip().lower()
        if trigger and trigger.lower() not in combined:
            warnings.append("missing trigger token")
        if not tags and not caption:
            warnings.append("missing tags/caption")
        if adapter == "controlnet" and "conditioning" not in combined and "control" not in combined:
            warnings.append("controlnet example has no visible conditioning-map note")
        if adapter == "ic_lora" and not any(word in combined for word in ["reference", "condition", "target", "transform", "input"]):
            warnings.append("ic-lora example does not describe condition/target relationship")
        if target in {"wan2_2", "ltx2_3"} and not any(word in combined for word in ["motion", "camera", "shot", "clip", "video", "frame"]):
            warnings.append("video target caption lacks motion/shot/clip metadata")
        if goal == "style" and len(tags) < 5 and _token_count(caption) < 8:
            warnings.append("style example may be under-described")
        if goal in {"character", "character_style"} and not any(word in combined for word in ["eyes", "hair", "fur", "skin", "body", "markings", "outfit", "clothing", "species"]):
            warnings.append("character example may lack identity-critical descriptors")
        return warnings

    def _branch_recommendations(self, metrics: dict[str, Any], trigger: str) -> list[str]:
        recs: list[str] = []
        if metrics.get("item_count", 0) < 10:
            recs.append("Branch has very few items. Add more curated examples before training unless this is only a smoke-test dataset.")
        cov = metrics.get("trigger_coverage")
        if trigger and (cov is None or cov < 0.95):
            recs.append("Trigger token coverage is below 95%. Apply rules to sidecars before export.")
        if metrics.get("missing_caption_or_tags", 0):
            recs.append("Some items have no usable sidecar text. Run labeling/captioning before final export.")
        if metrics.get("manual_review_rate", 0) > 0.25:
            recs.append("More than 25% of items need review. Use the rule packet with a local/cloud VLM and then re-run readiness.")
        if not recs:
            recs.append("Branch looks structurally ready for a frozen export; still spot-check visual quality before training.")
        return recs

    def export_branch(self, payload: Any) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        branch_id = data.get("branch_id")
        branch_name = str(data.get("branch_name") or "").strip()
        tool = str(data.get("training_tool") or "generic").strip().lower()
        target = str(data.get("target_model") or "sdxl").strip().lower()
        adapter = str(data.get("adapter_type") or "lora").strip().lower()
        goal = str(data.get("dataset_goal") or "character").strip().lower()
        include_media = bool(data.get("include_media", False))
        link_mode = str(data.get("link_mode") or "reference").strip().lower()
        include_variants = bool(data.get("include_variants", True))
        branch = self._resolve_branch(branch_id=branch_id, branch_name=branch_name)
        if not branch:
            raise ValueError("Branch not found. Create/select a global dataset branch first.")
        items_payload = self.global_dataset.branch_items(int(branch["id"]))
        items = items_payload.get("items") or []
        export_dir = self.exports_root / safe_name(branch.get("name") or f"branch_{branch['id']}") / f"{safe_name(target)}_{safe_name(adapter)}_{safe_name(goal)}_{safe_name(tool)}"
        media_dir = export_dir / "media"
        sidecar_dir = export_dir / "sidecars"
        config_dir = export_dir / "configs"
        for folder in (export_dir, media_dir, sidecar_dir, config_dir):
            folder.mkdir(parents=True, exist_ok=True)
        manifest_items: list[dict[str, Any]] = []
        for item in items:
            original = Path(item.get("original_path") or "")
            asset_id = item.get("global_asset_id")
            filename = f"{safe_name(str(asset_id))}_{safe_name(item.get('original_filename') or original.name)}"
            export_media_path = None
            if include_media and original.exists():
                export_media_path = media_dir / filename
                self._materialize(original, export_media_path, link_mode)
            tag_text = read_text_if_exists(Path(item.get("tag_path") or "")) if item.get("tag_path") else ""
            caption_text = read_text_if_exists(Path(item.get("caption_path") or "")) if item.get("caption_path") else ""
            sidecar_tag_path = sidecar_dir / f"{Path(filename).stem}.txt"
            sidecar_caption_path = sidecar_dir / f"{Path(filename).stem}.caption"
            sidecar_tag_path.write_text(tag_text, encoding="utf-8")
            sidecar_caption_path.write_text(caption_text, encoding="utf-8")
            manifest_items.append({
                "global_asset_id": asset_id,
                "branch_item_id": item.get("id"),
                "source_site": item.get("source_site"),
                "source_post_id": item.get("source_post_id"),
                "original_path": item.get("original_path"),
                "media_path": str(export_media_path) if export_media_path else item.get("original_path"),
                "tag_path": str(sidecar_tag_path),
                "caption_path": str(sidecar_caption_path),
                "tags": _split_tags(tag_text),
                "caption": caption_text,
            })
        manifest = {
            "created_at": now_iso(),
            "branch": branch,
            "target_model": target,
            "adapter_type": adapter,
            "dataset_goal": goal,
            "training_tool": tool,
            "include_media": include_media,
            "link_mode": link_mode,
            "include_variants": include_variants,
            "item_count": len(manifest_items),
            "items": manifest_items,
            "tool_interface": self._lookup(TRAINING_TOOL_INTERFACES, tool, "cloud_training_service") if tool != "generic" else None,
        }
        manifest_path = config_dir / "training_export_manifest.json"
        save_json(manifest_path, manifest)
        rules = self.build_rules(data)
        save_json(config_dir / "caption_rules_packet.json", rules)
        if tool in {"kohya_ss", "sd_scripts"}:
            (config_dir / "kohya_dataset_config.toml").write_text(self._kohya_stub(export_dir, manifest), encoding="utf-8")
        elif tool == "diffusers_scripts":
            self._write_diffusers_jsonl(config_dir / "metadata.jsonl", manifest)
        elif tool == "ltx_trainer":
            save_json(config_dir / "ltx_dataset_stub.json", self._ltx_stub(manifest))
        return {
            "ok": True,
            "export_dir": str(export_dir.resolve()),
            "manifest_path": str(manifest_path.resolve()),
            "item_count": len(manifest_items),
            "include_media": include_media,
            "link_mode": link_mode,
            "training_tool": tool,
            "rules_path": rules.get("rules_path"),
        }

    def _materialize(self, src: Path, dst: Path, mode: str) -> None:
        if dst.exists():
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        if mode == "symlink":
            try:
                dst.symlink_to(src)
                return
            except Exception:
                pass
        if mode == "hardlink":
            try:
                dst.hardlink_to(src)
                return
            except Exception:
                pass
        if mode == "reference":
            return
        shutil.copy2(src, dst)

    def _kohya_stub(self, export_dir: Path, manifest: dict[str, Any]) -> str:
        media = (export_dir / "media").as_posix()
        return (
            "# Generated by Data Curation Tool. Review before training.\n"
            "[[datasets]]\n"
            f"resolution = 1024\n"
            "batch_size = 1\n"
            "keep_tokens = 1\n"
            "\n[[datasets.subsets]]\n"
            f"image_dir = \"{media}\"\n"
            "caption_extension = \".txt\"\n"
            "num_repeats = 1\n"
        )

    def _write_diffusers_jsonl(self, path: Path, manifest: dict[str, Any]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            for item in manifest.get("items") or []:
                handle.write(json.dumps({"file_name": item.get("media_path"), "text": item.get("caption") or tag_string(item.get("tags") or [])}, ensure_ascii=False) + "\n")

    def _ltx_stub(self, manifest: dict[str, Any]) -> dict[str, Any]:
        return {
            "format": "dct_ltx_dataset_stub_v1",
            "note": "Review paths and clip metadata before LTX training.",
            "items": [
                {
                    "media_path": item.get("media_path"),
                    "caption": item.get("caption") or tag_string(item.get("tags") or []),
                    "condition_path": None,
                    "target_path": item.get("media_path"),
                }
                for item in manifest.get("items") or []
            ],
        }

    def trainer_handoff(self, payload: Any) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        training_tool = str(data.get("training_tool") or "generic").strip().lower()
        export_dir = str(data.get("export_dir") or "").strip()
        interface = self._lookup(TRAINING_TOOL_INTERFACES, training_tool, "cloud_training_service")
        manifest = {
            "created_at": now_iso(),
            "training_tool": training_tool,
            "interface": interface,
            "export_dir": export_dir,
            "commands_are_templates_only": True,
            "approval_required": True,
            "suggested_next_steps": interface.get("manual_steps") or [],
            "mcp": {
                "name": interface.get("mcp_name"),
                "transport": "stdio_or_tool_specific",
                "purpose": "Open external trainer, import the exported branch dataset, and start training only after user approval.",
            },
        }
        path = self.root / "handoffs" / f"{safe_name(training_tool)}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        save_json(path, manifest)
        manifest["handoff_path"] = str(path.resolve())
        return manifest

    def three_d_print_tool_catalog(self) -> dict[str, Any]:
        tools = [
            {"key": "blender", "label": "Blender conversion/repair", "formats": ["stl", "obj", "ply", "glb", "fbx"], "mcp_name": "dct-blender", "notes": "Use for mesh cleanup, unit scaling, manifold checks, and export."},
            {"key": "zbrush", "label": "ZBrush sculpt/decimation handoff", "formats": ["obj", "stl", "fbx"], "mcp_name": "dct-zbrush", "notes": "Use for sculpt cleanup, decimation, and export before slicing."},
            {"key": "prusaslicer", "label": "PrusaSlicer / PrusaSlicer CLI", "formats": ["stl", "3mf", "obj", "gcode"], "mcp_name": "dct-prusaslicer", "notes": "Preferred open-source slicer handoff where installed; use generated CLI templates after printer/profile review."},
            {"key": "orcaslicer", "label": "OrcaSlicer", "formats": ["stl", "3mf", "obj", "gcode"], "mcp_name": "dct-orcaslicer", "notes": "Open-source slicer fork family; use handoff/CLI where installed."},
            {"key": "bambu_studio", "label": "Bambu Studio", "formats": ["3mf", "stl", "gcode"], "mcp_name": "dct-bambu-studio", "notes": "Use handoff for slicing/project packaging with user-approved profiles."},
            {"key": "curaengine", "label": "CuraEngine / Cura CLI", "formats": ["stl", "3mf", "gcode"], "mcp_name": "dct-curaengine", "notes": "CuraEngine can slice from command line when machine/material profiles are provided."},
            {"key": "slic3r", "label": "Slic3r CLI", "formats": ["stl", "obj", "amf", "3mf", "gcode"], "mcp_name": "dct-slic3r", "notes": "Open-source slicer CLI option for STL/OBJ/AMF/3MF/G-code export workflows."},
            {"key": "meshlab", "label": "MeshLab / mesh repair", "formats": ["stl", "obj", "ply"], "mcp_name": "dct-meshlab", "notes": "Useful for repair/decimation/conversion before slicer import."},
        ]
        return {"tools": tools, "recommended_formats": ["stl", "3mf", "obj"], "slicer_ready_formats": ["stl", "3mf"]}

    def create_3d_print_package(self, payload: Any) -> dict[str, Any]:
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
        asset_path = Path(str(data.get("asset_path") or "")).expanduser()
        if not asset_path.exists() or not asset_path.is_file():
            raise FileNotFoundError(f"3D asset not found: {asset_path}")
        target_formats = data.get("target_formats") or ["stl", "3mf"]
        target_formats = [str(x).lower().lstrip(".") for x in target_formats if str(x).strip()]
        slicer = str(data.get("slicer") or "prusaslicer").strip().lower()
        name = safe_name(data.get("package_name") or asset_path.stem)
        out_dir = self.print_root / name
        out_dir.mkdir(parents=True, exist_ok=True)
        src_copy = out_dir / asset_path.name
        if not src_copy.exists():
            shutil.copy2(asset_path, src_copy)
        output_targets = []
        for fmt in target_formats:
            output_targets.append({"format": fmt, "path": str((out_dir / f"{asset_path.stem}.{fmt}").resolve()), "created": False, "requires_external_conversion": asset_path.suffix.lower().lstrip(".") != fmt})
        manifest = {
            "created_at": now_iso(),
            "source_asset": str(asset_path.resolve()),
            "package_dir": str(out_dir.resolve()),
            "source_copy": str(src_copy.resolve()),
            "slicer": slicer,
            "target_formats": target_formats,
            "output_targets": output_targets,
            "unit_scale": data.get("unit_scale") or "millimeters",
            "repair_policy": data.get("repair_policy") or "make_manifold_if_needed",
            "approval_required": True,
            "mcp_handoff": {
                "preferred_first_tool": "blender" if asset_path.suffix.lower() not in {".stl", ".3mf"} else slicer,
                "slicer": slicer,
                "instructions": [
                    "Open source_copy in Blender/MeshLab/ZBrush for cleanup if needed.",
                    "Export an STL or 3MF into output_targets before opening the slicer.",
                    "Open the STL/3MF in the selected slicer and generate G-code only after user approval and printer/profile confirmation.",
                ],
            },
        }
        manifest_path = out_dir / "3d_print_package_manifest.json"
        save_json(manifest_path, manifest)
        manifest["manifest_path"] = str(manifest_path.resolve())
        return manifest
