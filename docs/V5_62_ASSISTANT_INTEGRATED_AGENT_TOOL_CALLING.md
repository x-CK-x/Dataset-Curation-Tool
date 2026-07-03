# v5.62 Assistant-Integrated Agent Tool Calling

This release extends the human-approved Agent Tools runtime into the assistant surfaces used across the application.

## New behavior

Agent/tool planning is now available from:

- Tag Editor LLM/VLM/Assistant Tag Selection
- Compare LLM/VLM/Assistant Tag Selection
- Batch Tags assistant card
- Assistant tab
- Code Assistant tab
- full Agent Tools tab

Each inline panel can generate a tool-use plan from the current tab context, including selected media IDs, current tags, captions, selected tag chips, current tab, active tag profile, and selected model.

## Function-calling style tool definitions

The backend now exposes structured tool schemas:

```text
GET /api/agent-tools/definitions
```

Available tools include:

- `run_shell_command`
- `run_python_script`
- `list_path`
- `read_file`
- `write_file`
- `fetch_url_text`
- `open_browser`

The model is prompted with these schemas and asked to return JSON tool plans. The app can parse tool calls from JSON responses and display them as reviewable action cards.

## Execution pipeline

The v5.62 pipeline is:

1. **Tool Definition** — the backend gives the model JSON schemas for available tools.
2. **Intent Matching / Planning** — the selected assistant/orchestrator model proposes a structured plan/tool call.
3. **Human Approval** — each local action requires a visible approval checkbox.
4. **Execution** — the selected tool runs as a normal app job.
5. **Result Relay** — the job result can be relayed back into the selected assistant conversation for summarization and next-step planning.

## New APIs

```text
GET  /api/agent-tools/status
GET  /api/agent-tools/definitions
POST /api/agent-tools/risk
POST /api/agent-tools/parse-tool-calls
POST /api/agent-tools/plan
POST /api/agent-tools/command
POST /api/agent-tools/python
POST /api/agent-tools/execute-tool-call
POST /api/agent-tools/relay-result
POST /api/agent-tools/files/list
POST /api/agent-tools/files/read
POST /api/agent-tools/files/write
POST /api/agent-tools/fetch-url
POST /api/agent-tools/browser/open
```

## Sandbox modes

Settings now include an Agent Tools runtime card with:

- `workspace` mode — default; actions start in the configured workspace and are path-scoped unless any-path mode is enabled.
- `local` mode — local execution with approval and path controls.
- `docker` mode — optional Docker-backed Python/shell sandbox when Docker is installed.

Docker mode is optional and uses the configured image, defaulting to:

```text
python:3.11-slim
```

## Safety defaults

Local action execution remains human-approved by default. High-risk commands require the confirmation text:

```text
RUN HIGH RISK ACTION
```

Existing Firefox profile use remains disabled by default because it can expose active browser sessions and cookies to automation.
