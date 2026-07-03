from __future__ import annotations

import importlib.util
import sys

REQUIRED = [
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("pydantic", "pydantic"),
    ("PIL", "pillow"),
    ("numpy", "numpy"),
    ("requests", "requests"),
    ("orjson", "orjson"),
    ("pyarrow", "pyarrow"),
    ("yaml", "PyYAML"),
    ("huggingface_hub", "huggingface_hub"),
    ("selenium", "selenium"),
]

missing = [package for module, package in REQUIRED if importlib.util.find_spec(module) is None]
if missing:
    print("Missing required dependencies: " + ", ".join(missing))
    sys.exit(1)
print("Core dependencies OK.")
