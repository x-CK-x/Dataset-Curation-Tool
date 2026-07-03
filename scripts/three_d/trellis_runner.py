#!/usr/bin/env python3
"""Small stable CLI wrapper around the official TRELLIS pipeline APIs."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--image", default="")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--simplify", type=float, default=0.95)
    parser.add_argument("--texture-size", type=int, default=1024)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo = Path(args.repo).expanduser().resolve()
    if not repo.is_dir():
        raise FileNotFoundError(repo)
    sys.path.insert(0, str(repo))
    os.environ.setdefault("SPCONV_ALGO", "native")

    from trellis.utils import postprocessing_utils  # type: ignore

    if args.image:
        from PIL import Image
        from trellis.pipelines import TrellisImageTo3DPipeline  # type: ignore

        pipeline = TrellisImageTo3DPipeline.from_pretrained("microsoft/TRELLIS-image-large")
        pipeline.cuda()
        source = Image.open(args.image).convert("RGBA")
        outputs = pipeline.run(source, seed=args.seed)
    elif args.prompt:
        from trellis.pipelines import TrellisTextTo3DPipeline  # type: ignore

        pipeline = TrellisTextTo3DPipeline.from_pretrained("microsoft/TRELLIS-text-xlarge")
        pipeline.cuda()
        outputs = pipeline.run(args.prompt, seed=args.seed)
    else:
        raise ValueError("Provide --image or --prompt.")

    glb = postprocessing_utils.to_glb(
        outputs["gaussian"][0],
        outputs["mesh"][0],
        simplify=max(0.0, min(1.0, args.simplify)),
        texture_size=max(128, args.texture_size),
    )
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    glb.export(str(output))


if __name__ == "__main__":
    main()
