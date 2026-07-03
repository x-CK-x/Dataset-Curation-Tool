from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass
class Prediction:
    kind: str
    tags: list[tuple[str, float]] = field(default_factory=list)
    caption: str | None = None
    classes: list[tuple[str, float]] = field(default_factory=list)
    embedding: list[float] | None = None
    masks: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


class ModelAdapter(Protocol):
    name: str
    kind: str
    label: str

    def is_available(self) -> bool: ...

    def load(self, device: str = "auto", **kwargs: Any) -> None: ...

    def predict(self, image_path: Path, **kwargs: Any) -> Prediction: ...
