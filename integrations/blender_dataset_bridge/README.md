# Data Curation Tool Blender Bridge 0.3

<!-- DCT_VISUAL_START -->
![MCP and external creative tools overview](../../docs/wiki/assets/images/metadata_media_mcp_tools.png)
<!-- DCT_VISUAL_END -->


This Blender add-on connects Blender to the running Data Curation Tool for editable pose round-trips, generated-asset import, 3D generation job submission, and automatic rigging job submission.

## Install

1. Start the Data Curation Tool and leave it running. The default URL is `http://127.0.0.1:7865`.
2. In Blender, open **Edit > Preferences > Add-ons**.
3. Select **Install from Disk** and choose `integrations/blender_dataset_bridge.zip` from the application folder.
4. Enable **Data Curation Tool Blender Bridge**.
5. In the 3D Viewport, open the right sidebar with **N**, then choose **DCT Bridge**.

## Pose round-trip

- Set the DCT **Media ID** and, optionally, an **Annotation ID**.
- Use **Create Armature from DCT Pose** to import a saved 3D pose as a Blender armature.
- Edit the armature in Blender.
- Select the armature and use **Send Selected Armature Pose** to save its joints and bones back to DCT.

## Generated and rigged assets

- **Import 3D Asset Path** imports a local GLB/GLTF, FBX, OBJ, PLY, STL, USD, or USDZ file.
- **Import Latest DCT Asset** asks the running application for its newest managed generated/rigged asset and imports it.

## Queue 3D generation

Select a provider, source image or text prompt, and the provider-specific repository path or API endpoint. For cloud providers, enter the API key. **Queue 3D Generation in DCT** sends the job to the application's Jobs queue; the add-on does not block Blender while the model runs.

## Queue automatic rigging

Select the asset and either:

- **UniRig local**: set the UniRig repository path. On Windows, set the shell/WSL executable when required by your installation.
- **Blender pose-driven rig**: set the Blender executable and a DCT media/annotation containing the editable 3D pose. The bridge builds an armature from the pose and requests Blender automatic weights.

The provider runtime, model checkpoints, API credentials, and Blender executable are not bundled with the add-on. Use the DCT **Help & Workflows** and **3D Studio** panels for provider setup and diagnostics.
