# v5.78 3D Generation, MCP Tool Bridges, Cloud Runtime Defaults, and Booru Logic Gates

This build extends the previous progress-indicator and model-management work without replacing the existing application architecture. The additions are wired through the existing Models, 3D Studio, Downloads, Presets, Settings, and API layers.

## Main changes

### Expanded 3D generation catalog

The Models catalog and 3D Studio provider list now distinguish the major generation shapes instead of treating every 3D provider as a single image-to-3D path.

Supported provider/input categories now include:

- **Text-to-3D**: prompt-only generation providers and configurable cloud/local adapters.
- **Image-to-3D**: single reference image reconstruction and generation.
- **Multi-image-to-3D**: front/side/back or arbitrary multi-view reference workflows.
- **Video-to-3D**: configurable local/cloud video reconstruction workflows for later NeRF/Gaussian/mesh refinement.
- **ComfyUI 3D workflow handoff**: a workflow-oriented adapter that can queue 3D generation graphs through ComfyUI-compatible endpoints.
- **Blender refinement overlap**: generated assets are recorded as normal 3D assets so they can be imported, viewed, rigged, refined, or opened in Blender-oriented workflows.

New catalog/provider rows include TRELLIS/TRELLIS.2-style workflows, Hunyuan3D 2.1/2.x adapters, Meshy, Tripo, Hyper3D/Rodin, Unique3D/Wonder3D/InstantMesh-style local entries, generic configurable endpoints, and video reconstruction placeholders for installed local stacks.

### Cloud runtime defaults

Settings now include a `cloud_model_runtime_defaults` block. The Models tab exposes an editor for provider-level defaults so cloud model calls can carry the same provider-specific runtime information every time.

The default OpenRouter profile includes:

- `model`: `deepseek/deepseek-v4-pro`
- `context_shrinker_model`: `deepseek/deepseek-v4-flash`
- `transforms`: `middle-out`
- optional `provider_route` settings for provider selection/routing

The OpenRouter adapter merges these defaults with per-call options, including `provider`, `provider_route`, `transforms`, fallback model IDs, and context-shrinker metadata.

### MCP Tools tab and bridge server

A new **MCP Tools** tab lists the external creative tools that the assistant/orchestrator can hand off to when they exist locally:

- Blender
- Krita
- Audacity
- OBS Studio
- ComfyUI

The tab reports whether each tool is detected, whether it is enabled, which executable/endpoint is configured, and which manual steps remain. Installed tools are treated as enabled by default unless the user disables them in settings.

New files:

- `data_curation_tool/services/mcp_tools_service.py`
- `data_curation_tool/routers/mcp_tools.py`
- `integrations/mcp_servers/dct_mcp_tool_bridge.py`
- `install_mcp_tools.bat`
- `install_mcp_tools.sh`
- `requirements-mcp-tools.txt`

New endpoints:

- `GET /api/mcp-tools/status`
- `GET /api/mcp-tools/client-config`
- `POST /api/mcp-tools/write-client-config`
- `PUT /api/mcp-tools/settings`

The installer scripts create a separate MCP helper virtual environment, install the bridge requirements, smoke-test the tool status endpoint, and write `runtime/mcp_servers/dct_mcp_client_config.json` for external MCP clients.

### Downloader Boolean logic gates

The Downloads and Presets tabs now support booru/e621-style Boolean query logic in addition to positive and negative tag boxes.

Supported syntax:

```text
wolf AND (solo OR duo) AND NOT sketch
cat && (rating:s || rating:q) && -animated
character_a, (portrait OR full_body), NOT sketch
```

The default mode is **Boolean expand**:

- `AND` remains a normal booru tag conjunction.
- `NOT` becomes negative tags.
- `OR` expands into multiple source queries.
- Expanded queries are deduplicated through the existing cross-preset dedupe path.

For engines or endpoints that support native Boolean syntax, the alternative **Raw append** mode sends the expression directly to the source tags parameter.

New preview endpoint:

- `GET /api/downloads/logic/preview?query=...&max_clauses=64`

### Preset import/export updates

Download presets now persist:

- `logic_query`
- `logic_mode`
- `logic_max_clauses`

Text imports can include:

```text
logic: wolf AND (solo OR duo) AND NOT sketch
boolean: fox OR wolf
query: character_a AND portrait
```

### Wiki updates

A new wiki page was added:

- `docs/wiki/27-3D-Generation-MCP-Cloud-and-Booru-Logic.md`

`Home.md` and `_Sidebar.md` were updated so GitHub wiki exports include the new page.

## Validation

Targeted validation commands used for this build:

```bash
python -m py_compile data_curation_tool/config.py data_curation_tool/app.py data_curation_tool/context.py data_curation_tool/routers/downloads.py data_curation_tool/routers/mcp_tools.py data_curation_tool/routers/three_d.py data_curation_tool/services/downloader_service.py data_curation_tool/services/model_service.py data_curation_tool/services/preset_service.py data_curation_tool/services/three_d_service.py data_curation_tool/services/mcp_tools_service.py data_curation_tool/models/adapters.py data_curation_tool/models/registry.py integrations/mcp_servers/dct_mcp_tool_bridge.py tests/test_v578_3d_mcp_booru_logic.py
node --check data_curation_tool/static/app.js
python -m pytest -q tests/test_v530_pose_3d_studio.py tests/test_v536_downloader_all_posts_dedupe.py tests/test_v548_custom_models_modern_cv_migration.py tests/test_v578_3d_mcp_booru_logic.py
```

Result: all selected tests passed.

## Notes and limitations

- Generic cloud 3D providers are intentionally configurable contracts. They expose the UI/API plumbing, but the final response parsing or file download behavior may need provider-specific endpoint and response-path settings.
- MCP bridges are conservative. Destructive external-tool actions should remain approval-gated in the MCP client/assistant layer.
- Audacity control depends on local Audacity scripting support being enabled before any external automation can manipulate a running project.
- OBS and ComfyUI workflows may require local WebSocket/API plugins or endpoints depending on the user's installation.
