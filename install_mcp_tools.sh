#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "=============================================================="
echo "Data Curation Tool - External Creative Tool MCP Installer"
echo "Blender, Krita, Audacity, OBS Studio, ComfyUI"
echo "=============================================================="
PYTHON_BIN="${PYTHON_BIN:-python3}"
if [ ! -d ".venv-mcp" ]; then
  "$PYTHON_BIN" -m venv .venv-mcp
fi
. .venv-mcp/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-mcp-tools.txt
mkdir -p runtime/mcp_servers
python integrations/mcp_servers/dct_mcp_tool_bridge.py --tool blender --status > runtime/mcp_servers/mcp_bridge_smoke_test.json
python - <<'PY'
from data_curation_tool.paths import AppPaths
from data_curation_tool.config import AppSettings
from data_curation_tool.services.mcp_tools_service import MCPToolsService
p = AppPaths.create()
s = AppSettings.load(p.settings)
r = MCPToolsService(p, s).write_client_config()
print('Wrote', r.get('written'))
print('Installed', r.get('installed_count'), 'Enabled', r.get('enabled_count'))
PY
cat <<'TXT'

Manual follow-up:
  1. Open runtime/mcp_servers/dct_mcp_client_config.json.
  2. Copy the mcpServers entries into your MCP client config if you use an external MCP client.
  3. For Audacity, enable mod-script-pipe in Audacity and restart Audacity.
  4. For OBS, enable/configure OBS WebSocket and set the endpoint/password before control.
  5. For ComfyUI, start ComfyUI at http://127.0.0.1:8188 or set a custom endpoint.
==============================================================
TXT
