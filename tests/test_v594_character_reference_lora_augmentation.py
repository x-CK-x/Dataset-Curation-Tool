from __future__ import annotations

from pathlib import Path

from PIL import Image

from data_curation_tool import __version__
from data_curation_tool.config import AppSettings
from data_curation_tool.database import Database
from data_curation_tool.models.registry import ModelRegistry
from data_curation_tool.paths import AppPaths
from data_curation_tool.services.character_reference_service import CharacterReferenceService
from data_curation_tool.services.global_dataset_service import GlobalDatasetService
from data_curation_tool.services.media_service import MediaService
from data_curation_tool.services.pipeline_prep_service import PipelinePrepService


def make_paths(tmp_path: Path) -> AppPaths:
    return AppPaths.create(runtime=tmp_path / "runtime", models=tmp_path / "models", outputs=tmp_path / "outputs")


def make_image(path: Path, color: tuple[int, int, int], *, accent: tuple[int, int, int] | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGB", (128, 128), color)
    if accent:
        for x in range(42, 86):
            for y in range(18, 72):
                im.putpixel((x, y), accent)
    im.save(path)
    return path


def test_release_version_is_5_8_2() -> None:
    assert __version__ == "5.8.48"


def test_character_reference_profile_rank_prune_and_active_memory(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    db = Database(paths.database)
    settings = AppSettings(global_dataset_root=str(tmp_path / "global"))
    media = MediaService(db, paths)
    global_dataset = GlobalDatasetService(db, paths, settings)
    svc = CharacterReferenceService(db, paths, media, global_dataset)

    ref = make_image(tmp_path / "refs" / "target_ref.png", (22, 140, 220), accent=(255, 232, 70))
    match = make_image(tmp_path / "candidates" / "target_match.png", (24, 142, 218), accent=(255, 230, 72))
    reject = make_image(tmp_path / "candidates" / "not_target.png", (210, 60, 45), accent=(40, 20, 10))

    profile = svc.upsert_profile({"target_name": "sonic_like_character", "reference_paths": [str(ref)], "threshold": 0.45})
    assert profile["target_name"] == "sonic_like_character"
    assert profile["metadata"]["positive_image_count"] == 1

    ranked = svc.rank({"target_name": "sonic_like_character", "folder": str(tmp_path / "candidates"), "threshold": 0.45, "return_limit": 10})
    assert ranked["scored_count"] == 2
    by_path = {Path(row["path"]).name: row for row in ranked["items"]}
    assert by_path["target_match.png"]["score"] > by_path["not_target.png"]["score"]

    plan = svc.prune_plan({"run_id": ranked["run_id"], "threshold": 0.45})
    assert plan["counts"]["keep"] >= 1
    assert any(Path(row["path"]).name == "target_match.png" for row in plan["keep"])

    rebuilt = svc.rebuild_profile_from_run("sonic_like_character", run_id=ranked["run_id"], accept_threshold=0.45, reject_threshold=0.20)
    assert str(match) in rebuilt["positive_paths"]


def test_character_reference_can_prune_global_dataset_branch(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    db = Database(paths.database)
    settings = AppSettings(global_dataset_root=str(tmp_path / "global"))
    media = MediaService(db, paths)
    global_dataset = GlobalDatasetService(db, paths, settings)
    svc = CharacterReferenceService(db, paths, media, global_dataset)

    ref = make_image(tmp_path / "refs" / "character.png", (10, 80, 210), accent=(255, 240, 80))
    keep_path = make_image(tmp_path / "src" / "keep.png", (11, 82, 212), accent=(255, 242, 82))
    reject_path = make_image(tmp_path / "src" / "reject.png", (200, 35, 35), accent=(25, 20, 20))

    keep_asset = global_dataset.register_file(keep_path, tags=["character_anchor"], caption="target")
    reject_asset = global_dataset.register_file(reject_path, tags=["other_character"], caption="reject")
    branch = global_dataset.ensure_branch("char-reference-branch")
    global_dataset.link_assets(branch_id=branch["id"], asset_ids=[keep_asset["id"], reject_asset["id"]], copy_sidecars=True)

    svc.upsert_profile({"target_name": "target_character", "reference_paths": [str(ref)], "threshold": 0.45})
    ranked = svc.rank({"target_name": "target_character", "branch_id": branch["id"], "threshold": 0.45})
    assert ranked["scored_count"] == 2
    applied = svc.apply_prune_to_branch({"branch_id": branch["id"], "run_id": ranked["run_id"], "mode": "exclude_rejects"})
    assert applied["changed"] >= 1
    rows = global_dataset.branch_items(branch["id"])["items"]
    assert any(row["include"] in (0, False) for row in rows)


def test_lora_augmentation_plan_regularization_and_branch_variants(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    db = Database(paths.database)
    settings = AppSettings(global_dataset_root=str(tmp_path / "global"))
    global_dataset = GlobalDatasetService(db, paths, settings)
    svc = PipelinePrepService(db, paths, settings, global_dataset)

    img = make_image(tmp_path / "src" / "identity.png", (30, 120, 200), accent=(250, 245, 90))
    asset = global_dataset.register_file(img, tags=["solo", "blue eyes", "character token"], caption="character token, solo")
    branch = global_dataset.ensure_branch("character-lora")
    global_dataset.link_assets(branch_id=branch["id"], asset_ids=[asset["id"]], copy_sidecars=True)

    rules = svc.rule_presets("sdxl", "lora", "character")
    recommended = rules["rules"]["augmentation_policy"]["recommended"]
    assert "headshot_top_crop" in recommended or "headshot_proxy" in str(rules)
    assert rules["rules"]["regularization_policy"]

    plan = svc.augmentation_plan({"branch_id": branch["id"], "target_model": "sdxl", "adapter_family": "lora", "dataset_goal": "character"})
    assert plan["ok"] is True
    assert plan["recommended_augmentations"]
    assert plan["regularization"]

    dry = svc.generate_augmented_variants({"branch_id": branch["id"], "target_model": "sdxl", "adapter_family": "lora", "dataset_goal": "character", "selected_augmentations": ["headshot_top_crop"], "dry_run": True})
    assert dry["dry_run"] is True
    assert dry["created_count"] >= 1
    assert dry["variants"]

    created = svc.generate_augmented_variants({"branch_id": branch["id"], "target_model": "sdxl", "adapter_family": "lora", "dataset_goal": "character", "selected_augmentations": ["headshot_top_crop"], "dry_run": False})
    assert created["created_count"] >= 1
    assert any(Path(row["path"]).exists() for row in created["variants"] if row.get("path"))

    reg = svc.regularization_plan({"branch_id": branch["id"], "target_model": "sdxl", "adapter_family": "lora", "dataset_goal": "character", "class_name": "anthro character"})
    assert reg["dataset_goal"] == "character"
    assert reg["policy"]
    assert "prior" in reg["warning"].lower()


def test_registry_and_frontend_expose_character_reference_and_lora_automation(tmp_path: Path) -> None:
    registry = ModelRegistry(make_paths(tmp_path).models)
    names = {row["name"] for row in registry.list()}
    assert "character-reference-dinov2-base" in names
    assert "character-reference-clip-vit-b32" in names
    assert "character-reference-siglip-base" in names

    text = Path("data_curation_tool/static/app.js").read_text(encoding="utf-8")
    assert "Character Reference" in text
    assert "/api/character-reference/rank-now" in text
    assert "/api/pipeline-prep/augmentation-plan" in text
    assert "Regularization Plan" in text
