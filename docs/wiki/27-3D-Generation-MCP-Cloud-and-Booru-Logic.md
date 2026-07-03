# 3D Generation, MCP Tools, Cloud Runtime Defaults, and Booru Logic Gates

<!-- DCT_VISUAL_START -->
![3D generation, MCP tools, cloud runtime, and booru logic visual guide](assets/images/v578_3d_cloud_mcp_logic_overview.png)
<!-- DCT_VISUAL_END -->


This page covers the v5.78 additions for 3D generation providers, external creative-app MCP bridges, cloud model runtime defaults, and advanced booru/e621 download logic.

## 1. Expanded 3D generation provider types

Open **3D Studio** to use the generation providers. The provider catalog now separates the input shape required by each workflow:

| Input type | Typical use | Examples in the catalog |
| --- | --- | --- |
| Text-to-3D | Create a draft asset from a prompt only. | Hunyuan3D text adapter, Meshy text API, Tripo text API, Rodin text API, generic text-to-3D API. |
| Image-to-3D | Reconstruct or generate from one reference image. | TRELLIS, TRELLIS.2, Hunyuan3D, Stable Fast 3D, TripoSR, Meshy image API, Tripo image API. |
| Multi-image-to-3D | Use several views or concept references. | Meshy multi-image API, Tripo multi-image API, Rodin multi-image API, generic multi-image API. |
| Video-to-3D | Reconstruct from a turntable/video capture or hand off to local reconstruction tools. | Nerfstudio-style local workflow, generic video-to-3D API, ComfyUI 3D workflow endpoint. |
| Workflow graph | Queue a graph/workflow that may combine image/video/3D nodes. | ComfyUI 3D workflow API. |

The 3D Studio form includes fields for:

- prompt
- negative prompt
- single media item
- multi-image paths
- video path
- endpoint/API URL
- API key or token profile
- provider/model ID
- context shrinker model
- provider route JSON
- target output formats
- dry-run validation

Use **dry run** first when setting up a new provider. Dry run writes the planned command or HTTP request without running the external generator.

## 2. Blender handoff and refinement

Generated or imported 3D assets remain in the tool's asset library. After generation, use the existing 3D asset and Blender-oriented workflows to:

- open an asset in Blender
- inspect or refine the mesh
- run Blender Python through an MCP-approved bridge
- export GLB/FBX/OBJ/USD-style formats depending on the provider
- run later rigging or pose workflows

The MCP bridge does not bypass user approval. Blender Python execution can modify scenes and files, so destructive actions should remain gated by the external MCP client or assistant approval flow.

## 3. MCP Tools tab

Open **MCP Tools** to see local creative tools and bridge status.

The current tool set is:

- Blender
- Krita
- Audacity
- OBS Studio
- ComfyUI

Each row shows:

- installed/detected status
- enabled status
- executable path or endpoint
- supported action categories
- missing setup instructions
- MCP bridge/client config status

Installed tools are enabled by default. Missing tools stay disabled and show manual setup instructions.

### Install MCP support

On Windows:

```bat
install_mcp_tools.bat
```

On Linux:

```bash
chmod +x install_mcp_tools.sh
./install_mcp_tools.sh
```

The installer creates `.venv-mcp`, installs `requirements-mcp-tools.txt`, checks MCP tool status, and writes:

```text
runtime/mcp_servers/dct_mcp_client_config.json
```

Copy the generated `mcpServers` block into the external MCP client you want to use.

## 4. Tool-specific manual notes

### Blender

Install Blender first. The bridge can expose file-opening and Python execution hooks, but scene-changing actions should be treated as privileged.

### Krita

Install Krita and enable scripting/plugin support as required by your Krita MCP/plugin stack.

### Audacity

Install Audacity. If your Audacity MCP server uses `mod-script-pipe`, enable Audacity scripting in Audacity preferences before expecting automation to control a project.

### OBS Studio

Install OBS Studio. Most automation requires OBS WebSocket support or a compatible MCP bridge process.

### ComfyUI

Install and run ComfyUI before using endpoint-based workflow execution. Set the endpoint in Settings if it is not running on the default local address.

## 5. Cloud model runtime defaults

Open **Models** and find **Cloud model runtime defaults**. This JSON block stores provider-level runtime defaults.

The OpenRouter profile is initialized for a DeepSeek V4 Pro-style model route:

```json
{
  "openrouter": {
    "model": "deepseek/deepseek-v4-pro",
    "context_shrinker_model": "deepseek/deepseek-v4-flash",
    "transforms": ["middle-out"],
    "provider_route": {}
  }
}
```

You can add provider routing, fallback models, token-profile names, or provider-specific parameters. The cloud adapter merges these defaults with the options passed by a specific chat/orchestrator call.

## 6. Booru/e621 logic gates

The Downloads tab and Presets tab now accept logic queries in addition to positive and negative tags.

### Default mode: Boolean expand

Use Boolean expand for portable booru behavior:

```text
wolf AND (solo OR duo) AND NOT sketch
```

This expands to two source queries:

```text
wolf solo -sketch
wolf duo -sketch
```

The downloader then deduplicates results across expanded queries.

### Supported syntax

```text
AND OR NOT
&& || !
-tag
(parentheses)
comma as AND
implicit AND between adjacent tags
```

Examples:

```text
cat && (rating:s || rating:q) && -animated
fox (portrait OR full_body) NOT sketch
character_a, (solo OR duo), NOT comic
```

### Preview before downloading

Use **Preview logic expansion** before running the download. The preview calls:

```text
GET /api/downloads/logic/preview?query=...&max_clauses=64
```

`max_clauses` prevents accidental huge OR expansions.

### Raw append mode

Use Raw append only for endpoints that natively understand the expression syntax you type. In raw mode, the tool appends the expression directly to the source tags parameter.

## 7. Preset text import

Preset text imports can now include logic fields:

```text
name: example
source: e621
positive: female
negative: comic
logic: wolf AND (solo OR duo) AND NOT sketch
;;;
name: second
source: danbooru
boolean: fox OR wolf
```

The preset table includes a Logic column so you can confirm which presets use Boolean expansion.
