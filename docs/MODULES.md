# Modules Overview

| Path | Responsibility | Notes |
| ---- | -------------- | ----- |
| `src/app` | Next.js UI using CopilotKit components and hooks. Hosts Desk, Approvals, Integrations surfaces. | Requires alignment with `docs/ux.md`; future folder-level SUMMARY recommended. |
| `src/app/api/copilotkit` | API route instantiating `CopilotRuntime` and bridging to the ADK agent via `HttpAgent`. | Key entrypoint for AGUI events; update when adding service adapters. |
| `agent/` | FastAPI service exposing Google ADK LlmAgent through `ag_ui_adk`. Contains agent callbacks, tool definitions, and session state. | Replace demo tools with Composio FunctionTools per `docs/todo.md`. |
| `worker/` (planned) | Outbox executor dispatching approved envelopes through Composio. | Currently placeholder via `pyproject` script; implementation pending. |
| `docs/` | Product, architecture, UX, and operational references (this folder). | Keep ADRs and roadmap current. |
| `libs_docs/` | Vendor documentation snapshots for ADK, Composio, CopilotKit. | Treat as read-only reference. |
| `scripts/` | Dev tooling (`run-agent`, `setup-agent`). | Should be mirrored in Makefile/codex.yml once added. |
| `public/` | Static assets for Next.js. | Ensure no secrets or dynamic config stored here. |
| `agent/requirements.txt` | Python dependencies for ADK agent. | Keep in sync with `pyproject.toml` dependencies. |
| `package.json` | Next.js app metadata, scripts, dependencies. | Updated to reflect AI employee platform naming. |

## Known Gaps

- Need SUMMARY.md files for `src/app`, `agent/`, `worker/` once structure stabilizes.
- `worker/` directory not yet created; plan in `docs/roadmap.md` to implement Outbox module.
