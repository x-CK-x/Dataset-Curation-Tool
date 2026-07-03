# v5.30 Validation Record

## Automated checks

- Pytest collection: 120 tests across 38 files.
- All 120 collected tests passed when executed in grouped runs.
- New v5.30 pose, 3D Studio, Blender bridge, and SAM point-prompt suites: 11 passed.
- `python -m compileall -q data_curation_tool scripts integrations`: passed.
- `node --check data_curation_tool/static/app.js`: passed.
- `bash -n install_pose_models.sh install_sam_runtime.sh`: passed.
- Blender add-on ZIP integrity and source parity: passed.

The repository's complete pytest set is executed in groups because one monolithic invocation exceeds the validation sandbox's command-duration limit; no grouped invocation reported a failure.

## Runtime boundaries

The adapters use real provider contracts and do not manufacture pose, mesh, or mask results when inference fails. Large external checkpoints, provider repositories, cloud accounts, CUDA extension builds, and Blender itself are not bundled with this application package. Their actual inference/render execution therefore depends on the user's installed runtime, hardware, credentials, and accepted upstream licenses.
