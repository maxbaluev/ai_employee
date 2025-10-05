# Agent & Control Plane Architecture

**Status:** Implemented (single ADK agent + FastAPI wrapper) · In progress (guardrails,
multi-employee) · Planned (Supabase persistence, Outbox)

## What Exists Today

- `agent/agent.py` declares `proverbs_agent`, a `google.adk.agents.LlmAgent` with:
  - Shared state initialised in `on_before_agent`
  - Prompt enrichment in `before_model_modifier`
  - A demo `set_proverbs` tool and stubbed `get_weather` tool
- `ADKAgent` from `ag_ui_adk` exposes the agent via FastAPI (`app = FastAPI(...)`).
- `scripts/run-agent.sh` activates the virtualenv and launches the app.

This is intentionally simple: it proves the CopilotKit ↔ ADK bridge without taking
dependencies on Supabase or Composio yet.

## Immediate Next Steps

1. **Modularise the agent** – split `agent/agent.py` into packages:
   - `agents/proverbs.py` (demo)
   - `agents/control_plane.py` (future real agent)
   - `services/state.py`, `services/tools.py`, etc. for reuse
2. **Introduce configuration** – use `pydantic-settings` to load environment variables
   (already listed in `pyproject.toml`).
3. **Guardrails & approvals** – implement callbacks that enforce quiet hours, trust
   thresholds, and audit logging as described in `docs/governance/security-and-guardrails.md`.

## Roadmap Components (design contracts)

| Component | Responsibility | Notes |
|-----------|----------------|-------|
| **Supabase/Postgres** | Persist objectives, tasks, audit log, and tool catalog. | Dependencies already declared; schema to be defined in `docs/architecture/data-roadmap.md`. |
| **APScheduler jobs** | Warm scan + trickle refresh (read-only tasks using Composio). | Build as FastAPI background tasks until a dedicated worker exists. |
| **Outbox worker** | Execute approved envelopes via Composio with Tenacity retries and DLQ. | Run as a separate process exposed via `pyproject.toml` entry point `worker.outbox:main`. |
| **Structlog-based logging** | Structured logs with request IDs and tenant context. | Start by wrapping FastAPI loggers. |

## Testing Expectations

- Unit tests around callbacks and state transitions once they exist.
- Contract tests that mock Composio to validate schema-driven execution (see
  `docs/implementation/composio-tooling.md`).
- Smoke tests that spin up the FastAPI app and ensure `/` returns AGUI metadata.

Update this page as you break the monolith into composable modules.
