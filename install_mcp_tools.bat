@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
echo ==============================================================
echo Data Curation Tool - External Creative Tool MCP Installer
echo Blender, Krita, Audacity, OBS Studio, ComfyUI
echo ==============================================================
if not exist ".venv-mcp" (
  py -3 -m venv .venv-mcp
  if errorlevel 1 (
    python -m venv .venv-mcp
  )
)
if not exist ".venv-mcp\Scripts\python.exe" (
  echo [ERROR] Could not create .venv-mcp. Install Python 3.10+ and rerun.
  pause
  exit /b 1
)
".venv-mcp\Scripts\python.exe" -m pip install --upgrade pip
".venv-mcp\Scripts\python.exe" -m pip install -r requirements-mcp-tools.txt
if not exist runtime\mcp_servers mkdir runtime\mcp_servers
".venv-mcp\Scripts\python.exe" integrations\mcp_servers\dct_mcp_tool_bridge.py --tool blender --status > runtime\mcp_servers\mcp_bridge_smoke_test.json
".venv-mcp\Scripts\python.exe" -c "from data_curation_tool.paths import AppPaths; from data_curation_tool.config import AppSettings; from data_curation_tool.services.mcp_tools_service import MCPToolsService; p=AppPaths.create(); s=AppSettings.load(p.settings); r=MCPToolsService(p,s).write_client_config(); print('Wrote', r.get('written')); print('Installed', r.get('installed_count'), 'Enabled', r.get('enabled_count'))"
echo.
echo Manual follow-up:
echo   1. Open runtime\mcp_servers\dct_mcp_client_config.json.
echo   2. Copy the mcpServers entries into your MCP client config if you use an external MCP client.
echo   3. For Audacity, enable mod-script-pipe in Audacity and restart Audacity.
echo   4. For OBS, enable/configure OBS WebSocket and set the endpoint/password before control.
echo   5. For ComfyUI, start ComfyUI at http://127.0.0.1:8188 or set a custom endpoint.
echo ==============================================================
pause
