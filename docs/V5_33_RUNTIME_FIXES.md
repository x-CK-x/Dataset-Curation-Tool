# v5.33 Runtime Fixes

This build fixes four runtime usability issues reported from v5.32.

## Blender / 3D Viewport

Use the real `blender.exe`, not `blender-launcher.exe`, for background conversion jobs. The application now detects launcher paths and resolves the sibling `blender.exe` automatically when possible. It also strips pasted quotes and writes full Blender stdout/stderr logs for failed viewport conversions.

Recommended Windows path:

```text
C:\Program Files\Blender Foundation\Blender 5.0\blender.exe
```

## Pose Runtime Installation

The default pose installer is now `basic`, which installs the reliable runtimes first:

- Ultralytics YOLO pose
- MediaPipe pose

MMPose/OpenMMLab is now opt-in because its CUDA/MMCV wheels are version-sensitive and can take a long time to resolve. Use `install_pose_models.bat mmpose` only when you specifically need MMPose-backed models.

## JTP-3

JTP-3 now has a dedicated runtime dependency installer:

```bat
install_jtp3_runtime.bat
```

The adapter now parses JTP-3's wide CSV stdout format and stores full command/error details in job logs.

## Page State and Job Logs

Model runs no longer force the user away from the Tag Editor or other active pages. A top-bar button opens the latest queued job when needed. Job rows now expose a full-log view instead of truncating errors to a single short table cell.
