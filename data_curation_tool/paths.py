from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AppPaths:
    root: Path
    runtime: Path
    models: Path
    outputs: Path
    database: Path
    settings: Path
    thumbnails: Path
    presets: Path
    downloads: Path
    exports: Path

    @classmethod
    def create(cls, runtime: str | Path = "runtime", models: str | Path = "models", outputs: str | Path = "outputs") -> "AppPaths":
        root = Path.cwd().resolve()
        runtime_path = Path(runtime).expanduser().resolve()
        models_path = Path(models).expanduser().resolve()
        outputs_path = Path(outputs).expanduser().resolve()
        paths = cls(
            root=root,
            runtime=runtime_path,
            models=models_path,
            outputs=outputs_path,
            database=runtime_path / "app.db",
            settings=runtime_path / "settings.json",
            thumbnails=runtime_path / "thumbnails",
            presets=runtime_path / "presets",
            downloads=runtime_path / "downloads",
            exports=runtime_path / "exports",
        )
        paths.ensure()
        return paths

    def ensure(self) -> None:
        for path in (
            self.runtime,
            self.models,
            self.outputs,
            self.thumbnails,
            self.presets,
            self.downloads,
            self.exports,
        ):
            path.mkdir(parents=True, exist_ok=True)
