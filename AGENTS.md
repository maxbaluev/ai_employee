# Agent Control Plane Playbook

**Status:** In progress · Demo Proverbs agent is deliberately temporary; production flow
tracks the roadmap captured in `docs/`

## What Exists Today

- `agent/app.py` exposes a FastAPI surface using `ag_ui_adk.add_adk_fastapi_endpoint`,
  streaming AGUI events that CopilotKit consumes (`docs/architecture/overview.md`).
- `agent/agents/proverbs.py` wires a single `google.adk.agents.LlmAgent` with placeholder
  tools. Treat it as scaffolding only; new work should focus on the modular structure
  described below (`docs/implementation/backend-callbacks.md`).
- Settings already flow through `pydantic-settings` (`agent/services/settings.py`), so
  guardrails and Composio integration can inherit that contract.

Imports mirror the upstream samples in `libs_docs/copilotkit_docs/adk/`: we import
`CallbackContext`/`LlmResponse` directly and raise if `google-adk` is missing so errors
surface immediately rather than being swallowed by optional typing fallbacks.

> The Proverbs tool logic does **not** need to stay feature-complete. Prioritise the
> modular architecture and safety controls that unlock the production agent.

## Target Architecture

```
FastAPI (ag_ui_adk)
 ├─ / (AGUI stream)            ↔ CopilotKit runtime (`src/app/api/copilotkit/route.ts`)
 ├─ /healthz                   ↔ Deployment probes
 └─ (future) /metrics          ↔ Observability stack

Agent Package (`agent/`)
 ├─ agents/
 │   ├─ coordinator.py         # multi-employee orchestration (planned)
 │   └─ blueprints/desk.py     # per-surface specialisations
 ├─ callbacks/
 │   ├─ before.py              # prompt & guardrail synthesis
 │   └─ after.py               # plan execution + summaries
 ├─ guardrails/
 │   ├─ quiet_hours.py         # refs `docs/governance/security-and-guardrails.md`
 │   ├─ trust.py
 │   └─ scopes.py
 ├─ services/
 │   ├─ catalog.py             # Supabase-backed Composio metadata
 │   ├─ objectives.py          # tenant objectives (FR-001)
 │   ├─ outbox.py              # enqueue envelopes
 │   └─ audit.py               # structlog + Supabase writes
 └─ schemas/
     └─ envelope.py            # JSON structure shared with UI + workers

Workers (planned)
 └─ worker/outbox.py           # executes envelopes via Composio (Tenacity retries)
```

Use the vendor samples in `libs_docs/` as implementation references:

- `libs_docs/adk/full_llm_docs.txt` – ADK callbacks, agents, and multi-agent patterns.
- `libs_docs/composio_next/python/providers/google_adk/google_adk_demo.py` – bridging
  Composio tool schemas into ADK `FunctionTool`s.
- `libs_docs/copilotkit_docs/adk/` – shared state, human-in-the-loop, and generative UI
  flows expected by the frontend.
- `libs_docs/copilotkit_examples/` – Playwright and shared state examples for UI parity.

## Roadmap by Layer

| Layer | Goals | Source docs |
|-------|-------|-------------|
| **Control Plane** | Modularise the agent, split callbacks/guardrails/services, add configuration & session management. | `docs/architecture/agent-control-plane.md`, `docs/implementation/backend-callbacks.md` |
| **Composio** | Persist catalog, manage connected accounts, execute envelopes with retries/telemetry. | `docs/architecture/composio-execution.md`, `docs/implementation/composio-tooling.md` |
| **Data Plane** | Implement Supabase schema (tenants, objectives, guardrails, catalog, outbox, audit log) with RLS. | `docs/architecture/data-roadmap.md` |
| **Outbox Worker** | Respect autonomy thresholds, quiet hours, evidence requirements, and record audit events. | `docs/operations/runbooks/outbox-recovery.md`, `docs/governance/security-and-guardrails.md` |
| **Frontend Contract** | Keep shared state serialisable, emit `StateDeltaEvent`s, and document state schemas. | `docs/architecture/frontend.md`, `docs/implementation/frontend-shared-state.md`, `docs/implementation/ui-surfaces.md`, `docs/schemas/*` |
| **Observability** | Structlog, metrics, tracing, health checks, and alerting. | `docs/operations/run-and-observe.md`, `docs/references/observability.md` |

## Infrastructure & Tooling

- **mise** – `.mise.toml` pins Node 22 & Python 3.13 and exposes task shortcuts. Run
  `mise install` once per clone, then `mise run <task>` for scripts.
- **uv** – Package resolution and execution for the Python control plane. `pnpm
  install` triggers `uv sync --extra test`; manual usage:
  - `uv sync --extra test` – recreate `.venv` using `pyproject.toml`.
  - `uv run python -m agent` – launch the FastAPI app (mirrored in
    `scripts/run-agent.*`).
- **pnpm** – All frontend and orchestration scripts run via pnpm. Key commands are in
  `package.json` and mirrored as mise tasks.

### Local Loop Checklist

1. `mise install && pnpm install`
2. Populate `.env` (see `docs/getting-started/setup.md`).
3. `pnpm dev` (or `mise run dev`).
4. Validate: sidebar loads, `curl http://localhost:8000/healthz` returns `{"status":"ok"}`.

## Guardrails, Approvals & Safety

- Guardrail modules must stay pure where possible; inject them into `before_model` and
  `after_model` callbacks. Cover quiet hours, trust thresholds, scope enforcement, and
  evidence requirements (`docs/governance/security-and-guardrails.md`).
- Approval flows should emit structured audit events and shared state updates that the
  UI can render without bespoke logic (`docs/implementation/ui-surfaces.md`).
- Align all schema rendering with the JSON definitions stored in the catalog service—do
  not handcraft forms.

## Testing Expectations

- Unit tests: pure guardrail functions, callback pipelines, and catalog/outbox services
  (mock Composio via fixtures in `libs_docs/composio_next/python/`).
- Contract tests: spin up the FastAPI app with fake Supabase + Composio clients to
  assert AGUI event sequencing.
- Smoke tests: `uv run python -m agent` + `pnpm dev:ui` end-to-end validation, mirrored
  by Playwright coverage in the frontend (see `libs_docs/copilotkit_examples/tests`).
  Follow the smoke checklist in `docs/implementation/frontend-shared-state.md` (sidebar
  boot, desk render, approval submit/cancel, guardrail banner, state delta replay).

When you need to short-circuit a run (demo agents do this after the first tool call), set
`callback_context.end_invocation = True`—match the ADK quickstart examples instead of
touching private attributes.

## Observability & Operations

- Emit structured logs via `structlog` with tenant IDs and envelope IDs. Scrub secrets
  before logging (`docs/governance/security-and-guardrails.md`).
- Publish metrics described in `docs/operations/run-and-observe.md` and mirrored in
  `docs/references/observability.md` (requests, execution latency, queue size, scheduler
  health).
- Keep incident response playbooks (`docs/operations/runbooks/`) current as guardrails
  and the Outbox worker come online.

## Further Reading

- `docs/getting-started/core-concepts.md` – how UI, agent, and Composio layers interact.
- `docs/architecture/composio-execution.md` – catalog + envelope contracts.
- `docs/architecture/data-roadmap.md` – persistence model and worker expectations.
- `docs/implementation/backend-callbacks.md` – recommended package layout and tests.
- `docs/implementation/composio-tooling.md` – tool discovery/execution recipes.
- `docs/implementation/ui-surfaces.md` – schema-driven UI/UX patterns.
- `docs/todo.md` – layered backlog with next actions per area.
