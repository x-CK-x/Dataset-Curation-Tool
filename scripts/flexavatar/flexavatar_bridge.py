#!/usr/bin/env python
"""Subprocess bridge between the Data Curation Tool and FlexAvatar.

This script is executed *inside* the isolated dct-flexavatar Conda environment.
It deliberately contains no FastAPI/application imports, which keeps the
upstream CUDA stack separated from the main process.
"""
from __future__ import print_function

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

import numpy as np


def progress(value, message):
    value = max(0.0, min(1.0, float(value)))
    print("DCT_PROGRESS %.6f %s" % (value, str(message).replace("\n", " ")), flush=True)


def write_json(path, payload):
    if not path:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_manifest(path):
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    if not manifest.get("items"):
        raise ValueError("Manifest contains no staged input items: %s" % path)
    return manifest


def source_root():
    configured = os.environ.get("DCT_FLEXAVATAR_SOURCE")
    if configured:
        return Path(configured).resolve()
    return Path(__file__).resolve().parents[2] / "integrations" / "flexavatar" / "source"


def workspace_root():
    configured = os.environ.get("DCT_FLEXAVATAR_WORKSPACE")
    if configured:
        return Path(configured).resolve()
    return Path.cwd() / "runtime" / "flexavatar"


def command_validate(args):
    progress(0.05, "Importing FlexAvatar runtime")
    import torch
    import flexavatar
    # Import the complete inference/fitting surface, not only the lightweight
    # package namespace. This catches missing perceptual-loss and matting
    # dependencies before the user starts a long avatar job.
    from dino_loss import DinoV2Loss  # noqa: F401
    from sam_loss import SAMLoss  # noqa: F401
    from visage.matting.modnet import MODNetMatter  # noqa: F401
    from flexavatar.model.inversion import FittingManager  # noqa: F401
    from flexavatar.model_manager.flexavatar_model_manager import FlexAvatarModelManager
    manager = FlexAvatarModelManager("FLEX-1")
    checkpoint = Path(os.environ["FLEXAVATAR_MODELS_PATH"]) / "FLEX-1" / "checkpoints" / "ckpt-900k.pt"
    loaded = False
    parameter_count = None
    if args.load_checkpoint:
        if not checkpoint.exists():
            raise FileNotFoundError("FLEX-1 checkpoint was not found: %s" % checkpoint)
        device = torch.device(args.device)
        if device.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA is not available inside the dct-flexavatar environment.")
        progress(0.35, "Loading FLEX-1 checkpoint for a real runtime test")
        model = manager.load_checkpoint(900)
        model.to(device)
        model.eval()
        parameter_count = int(sum(parameter.numel() for parameter in model.parameters()))
        loaded = True
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    payload = {
        "python": sys.executable,
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_count": torch.cuda.device_count(),
        "checkpoint": str(checkpoint),
        "checkpoint_exists": checkpoint.exists(),
        "flexavatar_module": str(Path(flexavatar.__file__).resolve()),
        "model_config_exists": Path(manager.get_model_config_path()).exists() if hasattr(manager, "get_model_config_path") else True,
        "checkpoint_load_tested": loaded,
        "parameter_count": parameter_count,
        "fitting_imports_ready": True,
        "device": args.device,
    }
    progress(1.0, "FlexAvatar runtime validated")
    write_json(args.result_json, payload)
    print(json.dumps(payload, indent=2))


def _track_one(name):
    from shutil import copy, rmtree
    from elias.util import ensure_directory_exists_for_file, load_img, save_img
    from flexavatar.data_adapter.in_the_wild_data_adapter import InTheWildDataAdapter
    from flexavatar.env import FLEXAVATAR_PIXEL3DMM_PROCESSING_PATH
    from pixel3dmm.scripts.run_pixel3dmm import main as run_pixel3dmm

    adapter = InTheWildDataAdapter(name)
    image_path = adapter.get_image_path(name)
    if not Path(image_path).exists():
        raise FileNotFoundError("Staged FlexAvatar input was not found: %s" % image_path)
    tracking_path = Path(FLEXAVATAR_PIXEL3DMM_PROCESSING_PATH) / "tracking" / "itw" / name / "tracking_nV1_noPho_uv2000.0_n1000.0" / "result.mp4"
    if tracking_path.exists():
        return {"name": name, "status": "already_tracked", "tracking": str(tracking_path)}
    processing_input = Path(FLEXAVATAR_PIXEL3DMM_PROCESSING_PATH) / "processing" / "input" / "itw" / name
    if str(image_path).lower().endswith(".mp4"):
        target = processing_input / (name + ".mp4")
        ensure_directory_exists_for_file(str(target))
        copy(image_path, target)
    else:
        target = processing_input / (name + ".jpg")
        ensure_directory_exists_for_file(str(target))
        image = load_img(image_path)
        save_img(image[..., :3], str(target))
    run_pixel3dmm(
        str(target),
        str(Path(FLEXAVATAR_PIXEL3DMM_PROCESSING_PATH) / "processing" / "itw"),
        str(Path(FLEXAVATAR_PIXEL3DMM_PROCESSING_PATH) / "tracking" / "itw"),
        cleanup=True,
    )
    if processing_input.is_dir():
        rmtree(processing_input)
    return {"name": name, "status": "tracked", "tracking": str(tracking_path)}


def command_track(args):
    manifest = load_manifest(args.manifest)
    results = []
    items = manifest.get("items") or []
    for index, item in enumerate(items):
        name = str(item["name"])
        progress(index / max(1, len(items)), "Tracking %s with Pixel3DMM" % name)
        results.append(_track_one(name))
    payload = {"manifest": str(Path(args.manifest).resolve()), "tracked": results}
    progress(1.0, "Pixel3DMM tracking complete")
    write_json(args.result_json, payload)


def _neutral_expression(torch, device):
    neutral = torch.zeros(135, dtype=torch.float32, device=device)
    identity_6d = torch.tensor([1, 0, 0, 0, 1, 0], dtype=torch.float32, device=device)
    neutral[100:106] = identity_6d
    neutral[106:112] = identity_6d
    neutral[114:120] = identity_6d
    neutral[120:126] = identity_6d
    neutral[126:132] = identity_6d
    return neutral


def _build_observation_batch(manifest, max_observations, device):
    import torch
    from dreifus.camera import PoseType
    from dreifus.matrix import Pose
    from visage.matting.modnet import MODNetMatter
    from flexavatar.config.dataset_config import FlexAvatarBatch, SampleMetadata
    from flexavatar.data_adapter.in_the_wild_data_adapter import InTheWildDataAdapter

    matter = MODNetMatter()
    image_tensors = []
    sample_metadatas = []
    cam2worlds = []
    intrinsics_list = []
    expression_codes = []

    manifest_mode = str(manifest.get("mode") or "single")
    observations = []
    for item in manifest.get("items") or []:
        name = str(item["name"])
        adapter = InTheWildDataAdapter(name)
        timesteps = adapter.list_timesteps()
        if manifest_mode == "monocular" and len(timesteps) > max_observations:
            selected = np.linspace(0, len(timesteps) - 1, max_observations).round().astype(np.int64).tolist()
        else:
            selected = timesteps[:max_observations]
        for timestep in selected:
            observations.append((name, adapter, int(timestep)))
            if len(observations) >= max_observations:
                break
        if len(observations) >= max_observations:
            break
    if not observations:
        raise RuntimeError("No observations could be built from the staged input manifest.")

    for index, (name, adapter, timestep) in enumerate(observations):
        progress(0.03 + 0.18 * index / max(1, len(observations)), "Loading observation %d/%d" % (index + 1, len(observations)))
        metadata = SampleMetadata(name, None, timestep, None)
        image = adapter.load_image(metadata)
        image_torch = torch.tensor(image / 255.0, dtype=torch.float32).permute(2, 0, 1)[None]
        with torch.no_grad():
            alpha = matter.parse(image_torch).cpu()
        image_torch = image_torch * alpha[:, None] + 1 - alpha[:, None]
        canonical_flame_to_world, _ = adapter.load_head_pose(metadata)
        input_cam2world, input_intrinsics = adapter.load_camera_params(metadata)
        input_flame2world = Pose(
            canonical_flame_to_world.invert().numpy() @ input_cam2world,
            pose_type=PoseType.CAM_2_WORLD,
        )
        input_intrinsics = input_intrinsics.rescale(1 / 512)
        expression = torch.tensor(adapter.load_expression_code(metadata), dtype=torch.float32)[None, None]
        image_tensors.append(image_torch)
        sample_metadatas.append(metadata)
        cam2worlds.append(input_flame2world)
        intrinsics_list.append(input_intrinsics)
        expression_codes.append(expression)

    images = torch.stack([tensor[0] for tensor in image_tensors], dim=0)[None]
    expressions = torch.cat(expression_codes, dim=1)
    batch = FlexAvatarBatch(
        input_images=images,
        input_sample_metadatas=[sample_metadatas],
        input_cam2worlds=[cam2worlds],
        input_intrinsics=[intrinsics_list],
        input_view_mask=torch.ones((1, len(observations)), dtype=torch.float32),
        render_cam2world_poses=None,
        render_intrinsics=None,
        render_resolution=None,
        render_bg_color=None,
        target_images=None,
        input_expression_codes=expressions,
        dataset_ids=torch.ones((1, 1), dtype=torch.long),
    )
    return batch.to(device), observations


def _driver_expression_codes(args, source_batch, device):
    import torch
    from flexavatar.config.dataset_config import SampleMetadata
    from flexavatar.data_adapter.in_the_wild_data_adapter import InTheWildDataAdapter
    from flexavatar.data_adapter.nersemble_data_adapter import NeRSembleDataAdapter

    mode = str(args.driver_mode or "builtin")
    if mode == "neutral":
        count = args.frame_limit if args.render_360 else 1
        neutral = _neutral_expression(torch, device)
        return [neutral[None, None] for _ in range(max(1, count))], {"mode": mode, "frames": max(1, count)}
    if mode == "source":
        source_codes = source_batch.input_expression_codes[0]
        codes = [code[None, None] for code in source_codes]
        return codes[: args.frame_limit], {"mode": mode, "frames": min(len(codes), args.frame_limit)}
    if mode == "custom":
        if not args.driver_manifest:
            raise ValueError("driver_mode=custom requires --driver-manifest")
        driver_manifest = load_manifest(args.driver_manifest)
        item = driver_manifest["items"][0]
        adapter = InTheWildDataAdapter(str(item["name"]))
    elif mode == "builtin":
        adapter = NeRSembleDataAdapter(240, str(args.driver_sequence))
    else:
        raise ValueError("Unknown driver mode: %s" % mode)
    timesteps = adapter.list_timesteps()
    if len(timesteps) > args.frame_limit:
        timesteps = np.linspace(0, len(timesteps) - 1, args.frame_limit).round().astype(np.int64).tolist()
    codes = [
        torch.tensor(adapter.load_expression_code(SampleMetadata(None, None, int(timestep), None)), dtype=torch.float32, device=device)[None, None]
        for timestep in timesteps
    ]
    return codes, {"mode": mode, "sequence": str(args.driver_sequence), "frames": len(codes)}


def command_render(args):
    import mediapy
    import torch
    from dreifus.matrix import Intrinsics
    from dreifus.trajectory import circle_around_axis
    from dreifus.vector import Vec3
    from elias.util import ensure_directory_exists_for_file
    from gaussian_splatting.arguments import PipelineParams2
    from gaussian_splatting.gaussian_renderer import render_distwar
    from gaussian_splatting.scene.cameras import pose_to_rendercam
    from flexavatar.model.flexavatar_preprocessor import FlexAvatarPreprocessor
    from flexavatar.model.inversion import FittingConfig, FittingManager
    from flexavatar.model_manager.avatar_code_manager import AvatarCodeManager
    from flexavatar.model_manager.flexavatar_model_manager import FlexAvatarModelManager

    started = time.time()
    manifest = load_manifest(args.manifest)
    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available inside the dct-flexavatar environment.")
    progress(0.01, "Building tracked input observations")
    batch, observations = _build_observation_batch(manifest, args.max_observations, device)
    progress(0.22, "Loading DINO features")
    model_manager = FlexAvatarModelManager("FLEX-1")
    dataset_config = model_manager.load_dataset_config()
    preprocessor = FlexAvatarPreprocessor(dataset_config)
    batch = preprocessor.process(batch)

    progress(0.30, "Loading FLEX-1 checkpoint")
    model = model_manager.load_checkpoint(900)
    model.to(device)
    model.eval()
    code_manager = AvatarCodeManager()
    avatar_code = None
    fitting_history = []
    losses = []
    if args.load_avatar_code:
        if not code_manager.has_avatar_code(args.avatar_name):
            raise FileNotFoundError("Saved avatar code was not found for %s" % args.avatar_name)
        avatar_code = code_manager.load_avatar_code(args.avatar_name).to(device)
        progress(0.43, "Loaded saved avatar code")
    elif args.run_fitting and args.fitting_steps > 0:
        progress(0.34, "Optimizing avatar code against %d observation(s)" % len(observations))
        fitting = FittingManager(
            model,
            FittingConfig(
                steps=args.fitting_steps,
                lr=args.fitting_lr,
                lambda_sam_loss=args.lambda_sam,
                lambda_dino_loss=args.lambda_dino,
                lambda_latent_reg=args.lambda_latent,
            ),
        )
        avatar_code, fitting_history, losses = fitting.run_inversion(batch)
        progress(0.62, "Avatar fitting complete")
    else:
        progress(0.40, "Creating feed-forward avatar code")
        with torch.no_grad():
            output = model.forward(batch, only_internal_representations=True)
        avatar_code = output.gaussian_models_output.internal_representations

    code_manager.save_avatar_code(avatar_code, args.avatar_name)
    code_path = Path(code_manager.get_avatar_code_path(args.avatar_name)).resolve()
    output_folder = Path(os.environ["FLEXAVATAR_RENDERINGS_PATH"])
    output_folder.mkdir(parents=True, exist_ok=True)
    fitting_path = None
    if args.save_fitting_history and fitting_history:
        fitting_path = output_folder / ("fitting_history_%s.mp4" % args.avatar_name)
        mediapy.write_video(str(fitting_path), fitting_history, fps=min(30, max(1, args.fps)))

    progress(0.66, "Preparing expression driver and camera path")
    expression_codes, driver_info = _driver_expression_codes(args, batch, device)
    if not expression_codes:
        raise RuntimeError("The selected driver produced no expression codes.")
    if args.render_360:
        poses = circle_around_axis(
            len(expression_codes), axis=Vec3(0, 1, 0), up=Vec3(0, 1, 0),
            move=Vec3(0, 0, -0.05), look_at=Vec3(0, 0, -0.05), distance=1,
        )
    else:
        poses = circle_around_axis(len(expression_codes), up=Vec3(0, 1, 0), move=Vec3(0, 0, 1), distance=0.3)
    intrinsics = Intrinsics(1500 * args.resolution / 512, 1500 * args.resolution / 512, args.resolution / 2, args.resolution / 2)

    frames = []
    with torch.no_grad():
        for index, (expression, pose) in enumerate(zip(expression_codes, poses)):
            progress(0.67 + 0.31 * index / max(1, len(expression_codes)), "Rendering frame %d/%d" % (index + 1, len(expression_codes)))
            output = model.create_gaussian_models(
                batch.input_images,
                batch.features,
                batch.input_cam2worlds,
                batch.input_intrinsics,
                expression_codes=expression,
                dataset_ids=batch.dataset_ids,
                cached_internal_representations=avatar_code,
            )
            render_cam = pose_to_rendercam(pose, intrinsics, args.resolution, args.resolution)
            rendering = render_distwar(render_cam, output.gaussian_models[0][0], PipelineParams2(), torch.ones((3,), device=device))
            frames.append(rendering["render"].permute(1, 2, 0).detach().cpu().numpy())

    name = "rendering_p%s" % args.avatar_name
    if args.driver_mode == "custom":
        name += "_custom_driver"
    elif args.driver_mode == "builtin" and args.driver_sequence != "EMO-1-shout+laugh":
        name += "_dr%s" % re_safe(args.driver_sequence)
    if args.render_360:
        name += "_360"
    output_path = output_folder / (name + ".mp4")
    ensure_directory_exists_for_file(str(output_path))
    mediapy.write_video(str(output_path), frames, fps=args.fps)
    payload = {
        "avatar_name": args.avatar_name,
        "mode": manifest.get("mode"),
        "observations": len(observations),
        "avatar_code": str(code_path),
        "rendering": str(output_path.resolve()),
        "fitting_history": str(fitting_path.resolve()) if fitting_path else None,
        "fitting_steps": args.fitting_steps if args.run_fitting else 0,
        "final_fitting_loss": float(losses[-1]) if losses else None,
        "driver": driver_info,
        "render_360": bool(args.render_360),
        "resolution": args.resolution,
        "fps": args.fps,
        "elapsed_seconds": round(time.time() - started, 3),
    }
    progress(1.0, "FlexAvatar rendering complete")
    write_json(args.result_json, payload)
    print(json.dumps(payload, indent=2))


def re_safe(value):
    import re
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value)).strip("._-") or "driver"


def build_parser():
    parser = argparse.ArgumentParser(description="Data Curation Tool FlexAvatar subprocess bridge")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("--result-json", default="")
    validate.add_argument("--device", default="cuda:0")
    validate.add_argument("--load-checkpoint", action="store_true")
    validate.set_defaults(func=command_validate)

    track = sub.add_parser("track")
    track.add_argument("--manifest", required=True)
    track.add_argument("--result-json", default="")
    track.set_defaults(func=command_track)

    render = sub.add_parser("render")
    render.add_argument("--manifest", required=True)
    render.add_argument("--driver-manifest", default="")
    render.add_argument("--avatar-name", required=True)
    render.add_argument("--result-json", default="")
    render.add_argument("--device", default="cuda:0")
    render.add_argument("--run-fitting", action="store_true")
    render.add_argument("--fitting-steps", type=int, default=200)
    render.add_argument("--fitting-lr", type=float, default=1e-2)
    render.add_argument("--lambda-sam", type=float, default=1.0)
    render.add_argument("--lambda-dino", type=float, default=1.0)
    render.add_argument("--lambda-latent", type=float, default=0.0)
    render.add_argument("--max-observations", type=int, default=100)
    render.add_argument("--load-avatar-code", action="store_true")
    render.add_argument("--save-fitting-history", action="store_true")
    render.add_argument("--render-360", action="store_true")
    render.add_argument("--driver-mode", choices=["builtin", "custom", "neutral", "source"], default="builtin")
    render.add_argument("--driver-sequence", default="EMO-1-shout+laugh")
    render.add_argument("--frame-limit", type=int, default=240)
    render.add_argument("--fps", type=float, default=24.0)
    render.add_argument("--resolution", type=int, default=512)
    render.set_defaults(func=command_render)
    return parser


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
