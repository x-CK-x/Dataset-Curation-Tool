# Krita Dataset Bridge

<!-- DCT_VISUAL_START -->
![Krita and MCP integration overview](../../docs/wiki/assets/images/metadata_media_mcp_tools.png)
<!-- DCT_VISUAL_END -->


Optional Krita Python plugin for sending the active document back to the local Data Curation Tool.

Install by copying `krita_dataset_bridge.desktop` and the `krita_dataset_bridge/` folder into Krita's Python plugin directory, then enable **Dataset Bridge** in Krita's Python Plugin Manager.

The plugin exports the active document as PNG and posts it to `http://127.0.0.1:7865/api/krita/import-image` by default. It can also pass optional tags, caption, and dataset id.
