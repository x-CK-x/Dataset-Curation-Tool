# Data Curation Tool ComfyUI Bridge Nodes

<!-- DCT_VISUAL_START -->
![MCP and ComfyUI integration overview](../../docs/wiki/assets/images/metadata_media_mcp_tools.png)
<!-- DCT_VISUAL_END -->


This optional ComfyUI custom-node package lets ComfyUI exchange images, videos, masks, tag strings, captions, LoRA metadata, and normalized generation metadata with Data Curation Tool.

Install by copying this folder into:

```text
ComfyUI/custom_nodes/data_curation_tool_comfyui_nodes/
```

Restart ComfyUI, then use nodes under **Data Curation Tool / Bridge**.

The default API base is:

```text
http://127.0.0.1:7865/api/comfy
```

Nodes included:

- DCT Health Check
- DCT Send Media
- DCT Receive Media Package
- DCT Metadata Extractor
- DCT Metadata Field
- DCT Send Metadata
- DCT Text Preview
