from __future__ import annotations

from pathlib import Path

from data_curation_tool.models.registry import ModelRegistry, safe_model_dir

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class DummyAdapter:
    def __init__(self):
        self.kwargs = None
        self.device = None

    def is_available(self) -> bool:
        return True

    def load(self, device: str = "auto", **kwargs):
        self.device = device
        self.kwargs = dict(kwargs)


def _minimal_hf_snapshot(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "config.json").write_text('{"architecture":"vit_base_patch16_224","num_classes":1}', encoding="utf-8")
    (path / "model.safetensors").write_bytes(b"not-a-real-weight-but-nonzero")
    (path / "selected_tags.csv").write_text("tag_id,name,category\n0,test_tag,0\n", encoding="utf-8")


def test_version_bumped_to_v5832():
    import data_curation_tool

    assert data_curation_tool.__version__ == "5.8.48"
    assert 'version = "5.8.48"' in read("pyproject.toml")


def test_registry_finds_migrated_alias_folders_and_loads_local_only(tmp_path: Path):
    model_root = tmp_path / "models"
    registry = ModelRegistry(model_root)
    record = registry.get_record("wd-vit-tagger")
    dummy = DummyAdapter()
    record.adapter = dummy

    # Older/manual migrations may have stored a row by catalog name instead of
    # the current repo-safe SmilingWolf--wd-vit-tagger-v3 path.
    legacy_alias = model_root / "hf" / "wd-vit-tagger"
    _minimal_hf_snapshot(legacy_alias)

    candidates = record.candidate_local_dirs(model_root, [])
    assert legacy_alias in candidates
    assert record.is_downloaded(model_root, []) is True
    assert record.complete_local_dir(model_root, []) == legacy_alias

    result = registry.load_model("wd-vit-tagger", device="cpu")
    assert result["loaded"] is True
    assert dummy.kwargs is not None
    assert dummy.kwargs["model_id"] == str(legacy_alias)
    assert dummy.kwargs["local_files_only"] is True
    assert dummy.kwargs["repo_id"] == "SmilingWolf/wd-vit-tagger-v3"


def test_registry_prefers_hf_cache_snapshot_child_over_cache_parent(tmp_path: Path):
    model_root = tmp_path / "models"
    registry = ModelRegistry(model_root)
    record = registry.get_record("wd-vit-tagger")

    cache_parent = model_root / "hf" / "models--SmilingWolf--wd-vit-tagger-v3"
    snapshot = cache_parent / "snapshots" / "abc123"
    _minimal_hf_snapshot(snapshot)
    (cache_parent / "refs").mkdir(parents=True)
    (cache_parent / "refs" / "main").write_text("abc123", encoding="utf-8")

    assert record.complete_local_dir(model_root, []) == snapshot
    assert registry.resolve_model_path(record) == str(snapshot)


def test_registry_finds_migrated_huggingface_hub_snapshot_layout(tmp_path: Path):
    model_root = tmp_path / "models"
    registry = ModelRegistry(model_root)
    record = registry.get_record("wd-eva02-large-tagger-v3")

    cache_parent = model_root / "huggingface" / "hub" / "models--SmilingWolf--wd-eva02-large-tagger-v3"
    snapshot = cache_parent / "snapshots" / "def456"
    _minimal_hf_snapshot(snapshot)

    assert cache_parent in record.candidate_local_dirs(model_root, [])
    assert record.complete_local_dir(model_root, []) == snapshot
    row = record.to_dict(model_root, [])
    assert row["downloaded"] is True
    assert row["local_path"] == str(snapshot)


def test_load_does_not_fall_back_to_huggingface_repo_when_local_missing(tmp_path: Path):
    registry = ModelRegistry(tmp_path / "models")
    record = registry.get_record("wd-vit-tagger")
    record.adapter = DummyAdapter()

    try:
        registry.load_model("wd-vit-tagger", device="cpu")
    except RuntimeError as exc:
        msg = str(exc)
        assert "Load button will not auto-download model weights" in msg
        assert "not resolved to a local model folder" in msg
    else:  # pragma: no cover
        raise AssertionError("load_model should refuse remote auto-download for missing downloadable local rows")


def test_frontend_disables_load_for_missing_downloads_and_backend_enforces_local_first():
    app = read("data_curation_tool/static/app.js")
    registry = read("data_curation_tool/models/registry.py")
    adapters = read("data_curation_tool/models/adapters.py")
    migration_router = read("data_curation_tool/routers/migration.py")
    model_service = read("data_curation_tool/services/model_service.py")
    app_py = read("data_curation_tool/app.py")

    assert "missingDownloadForLoad" in app
    assert "Load will not auto-download weights" in app
    assert "local_files_only" in registry
    assert "HF_HUB_OFFLINE" in registry and "TRANSFORMERS_OFFLINE" in registry
    assert "dct_resolved_local_model_path" in registry
    assert "_repo_slug_candidates" in registry
    assert "models--" in registry
    assert "Load is running in local-files-only mode after migration" in adapters
    assert "Local WD/PixAI tagger file not found" in adapters
    assert "local_files_only: bool = False" in adapters
    assert "prevent_automatic_download" in model_service
    assert "Load is local-only by default" in model_service
    assert "model_cache_dir" in app_py and "external_roots.append(str(cache_path))" in app_py
    assert "c.models.invalidate_model_catalog_cache()" in migration_router
