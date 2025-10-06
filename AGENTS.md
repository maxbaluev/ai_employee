# Agent Control Plane Playbook

**Status:** Updated October 6, 2025 · Control plane (FastAPI + Supabase integrations) is live · Multi-employee orchestration in progress

This file is the agent-facing control tower for the repository. Pair it with `README.md`
(human onboarding) and `docs/README.md` (documentation map) so code, docs, and
guardrails move together.

---

## Setup Commands
- `mise install` – install pinned runtimes (Node 22, Python 3.13)
- `pnpm install` – installs JS deps **and** runs `uv sync --extra test`
- `pnpm dev` – runs Next.js UI (`dev:ui`) + agent (`dev:agent`) concurrently
- `pnpm run dev:agent` / `uv run python -m agent` – FastAPI + ADK in isolation
- `pnpm run dev:ui` – Next.js shell only (Turbopack)
- `pnpm lint` · `pnpm test` – lint + contract/unit tests before any PR
- `pnpm build && pnpm start` – production build smoke

## Code Style & Tooling
- **TypeScript**: strict mode (`tsconfig.json`); lint with Next.js config (`eslint.config.mjs`);
  Prettier defaults favour single quotes and trailing commas.
- **Python**: compose pure functions + pydantic models; keep guardrails side-effect free
  and covered by pytest (`tests/guardrails/`).
- Use `structlog` for agent logging; redact secrets before logging.
- Scripts under `scripts/` and `mise run` are uv-aware—avoid invoking the interpreter directly.

## Testing Checklist
- `pnpm test` – shared Jest/Vitest suites
- `pnpm lint` – Next.js ESLint rules (strict)
- `uv run python -m pytest` – targeted Python suites (`tests/`)
- `pnpm test --filter agent` – run only agent-specific checks when needed
- Playwright smoke patterns live in `libs_docs/copilotkit_examples/tests`
- Re-run migrations after schema tweaks: `pnpm install:agent` → `uv run python -m agent`

## Key Docs & Directories
- `docs/getting-started/core-concepts.md` – end-to-end flow (UI ↔ agent ↔ Composio)
- `docs/architecture/*` – component diagrams, data roadmap, frontend layout
- `docs/implementation/*` – guardrails, callbacks, shared state, UI surfaces
- `docs/operations/*` – deployment, observability, runbooks
- `docs/governance/*` – security, approvals, doc ownership
- `docs/todo.md` – layered backlog mirroring the phases below

## Current Implementation Snapshot
- `agent/app.py` exposes FastAPI via `ag_ui_adk.add_adk_fastapi_endpoint` for AGUI streams → CopilotKit (`src/app/api/copilotkit/route.ts`).
- `agent/agents/control_plane.py` composes `google.adk.agents.LlmAgent`, desk blueprint, guardrails, Supabase-backed services, and Composio tooling (dependency injection keeps in-memory doubles viable).
- `agent/services/settings.py` (pydantic-settings) feeds guardrails, Composio, and Supabase configs with env parity across environments.
- In-memory fallbacks exist for catalog/objectives/outbox; Supabase implementations land in Phases 2 and 4.
- Worker skeleton (`worker/outbox.py`) and shared JSON schemas (`docs/schemas/*`) are committed.

## Target Architecture
```
FastAPI (ag_ui_adk)
 ├─ / (AGUI stream)            ↔ CopilotKit runtime (`src/app/api/copilotkit/route.ts`)
 ├─ /healthz                   ↔ Deployment probes
 └─ (roadmap) /metrics         ↔ Observability stack

Agent Package (`agent/`)
 ├─ agents/
 │   ├─ control_plane.py       # live orchestration
 │   └─ coordinator.py         # multi-employee orchestration (roadmap)
 ├─ callbacks/
 │   ├─ before.py              # prompt & guardrail synthesis
 │   └─ after.py               # plan execution + summaries
 ├─ guardrails/
 │   ├─ quiet_hours.py
 │   ├─ trust.py
 │   └─ scopes.py
 ├─ services/
 │   ├─ catalog.py             # Supabase-backed metadata (Phase 2)
 │   ├─ objectives.py
 │   ├─ outbox.py              # enqueue envelopes (Phase 4 persistence)
 │   └─ audit.py               # structlog + Supabase writes
 └─ schemas/
     └─ envelope.py            # shared with UI + workers

Worker (roadmap)
 └─ worker/outbox.py           # executes envelopes via Composio (Tenacity retries)
```

## Multi-Phase Delivery Plan
Each phase references the authoritative items in `docs/todo.md`. Legend: ✅ done · 🔄 in progress · 📋 planned.

### Phase 0 · Foundation & Documentation Review ✅ (complete)
- Tooling bootstrap documented (`docs/getting-started/setup.md`).
- System overview synchronised (`docs/getting-started/core-concepts.md`, `docs/architecture/overview.md`).
- Supabase schema + seeds landed (`db/migrations/001_init.sql`, `db/seeds/000_demo_tenant.sql`).
- Shared-state schemas published (`docs/schemas/*`, `docs/implementation/frontend-shared-state.md`).
- Observability contracts defined (`docs/operations/run-and-observe.md`, `docs/references/observability.md`).

### Phase 1 · Control Plane Modularisation 🔄
Goals: harden callbacks/guardrails/services and prep the multi-employee coordinator.
- [x] Guardrail modules with pytest coverage (`agent/guardrails/*`, `tests/guardrails/`).
- [x] Callback builders for before/after hooks (`agent/callbacks/before.py`, `agent/callbacks/after.py`).
- [x] Service abstractions with in-memory defaults (`agent/services/*.py`).
- [ ] Replace Proverbs demo diagram with modular blueprint (`docs/architecture/agent-control-plane.md`).
- [ ] Scaffold `agent/agents/coordinator.py` for multi-employee orchestration.
See `docs/implementation/backend-callbacks.md` and `docs/governance/security-and-guardrails.md`.

### Phase 2 · Composio Integration & Catalog 📋
Goals: persist the tool catalog, manage OAuth, execute envelopes.
- [ ] Supabase-backed `CatalogService` replacing the shim (`agent/services/catalog.py`).
- [ ] Embed catalog → envelope → Outbox sequence diagram (`docs/architecture/composio-execution.md`).
- [ ] Wire Composio OAuth env vars + scope handling (`agent/services/settings.py`, `docs/implementation/composio-tooling.md`).
- [ ] Schedule nightly catalog sync with telemetry (Supabase Cron + Edge Functions + Tenacity for retries).
Depends on Phase 1 service boundaries.

### Phase 3 · Approvals & Frontend State 📋
Goals: schema-driven approval surfaces with CopilotKit parity.
- [ ] Document Desk/Approvals layout & state contracts (`docs/architecture/frontend.md`).
- [ ] Scaffold approval forms from JSON Schema (`docs/implementation/ui-surfaces.md`, `docs/schemas/approval-modal.json`).
- [ ] Emit `StateDeltaEvent`s for all agent mutations (`agent/callbacks/after.py`).
- [ ] Add Playwright coverage for sidebar boot, desk render, approval submit/cancel, guardrail banner (`libs_docs/copilotkit_examples/tests`).
Requires Phase 2 catalog persistence for schema hydration.

### Phase 4 · Data Persistence & Outbox Worker 🔄
Goals: replace in-memory services with Supabase + ship the Outbox executor.
- [x] Baseline migrations + seeds committed (`db/migrations/001_init.sql`, `db/seeds/000_demo_tenant.sql`).
- [ ] Implement Supabase-backed Outbox service + retry semantics (`agent/services/outbox.py`, `worker/outbox.py`).
- [ ] Document DLQ replay flow end-to-end (`docs/operations/runbooks/outbox-recovery.md`).
- [ ] Add ERD + migration conventions (`docs/architecture/data-roadmap.md`).
Depends on Phase 2 envelope contracts.

### Phase 5 · Observability & Operations 📋
Goals: production telemetry, alerts, and runbooks.
- [ ] Expose `/metrics` FastAPI route + integrate collectors (`docs/operations/run-and-observe.md`).
- [ ] Fill observability dashboard placeholders with PromQL queries (`docs/references/observability.md`).
- [ ] Expand incident runbooks with real postmortems + comms templates (`docs/operations/runbooks/`).
Requires Phase 4 worker telemetry to be emitting.

### Phase 6 · Governance & Documentation Hygiene ✅ (ongoing)
Goals: keep docs evergreen and guardrails enforced.
- [x] Doc ownership matrix + audit cadence defined (`docs/governance/ownership-and-evergreen.md`).
- [x] Guardrail PR checklist published (`docs/governance/security-and-guardrails.md`).
- [ ] Extend CONTRIBUTING/PR templates with TODO references once those files exist.
Runs alongside every phase; audit quarterly.

---

## Operational Guardrails & Safety
- Guardrail modules stay pure; inject via `before_model`/`after_model` callbacks. Cover quiet hours, trust, scopes, evidence requirements.
- Approval flows emit structured audit events + shared-state deltas (`docs/implementation/frontend-shared-state.md`).
- Use `structlog` for tenant + envelope logging; scrub secrets; persist audit breadcrumbs in Supabase.
- Short-circuit demo runs with `callback_context.end_invocation = True` (per ADK quickstarts).

## Handy References
- `docs/todo.md` – single source of remaining work mapped to the phases above.
- `libs_docs/adk/full_llm_docs.txt` – callback + multi-agent patterns.
- `libs_docs/composio_next/python/providers/google_adk/google_adk_demo.py` – Composio tool bridging reference.
- `libs_docs/copilotkit_docs/adk/` – shared state + human-in-the-loop flows for UI parity.

Keep this playbook current: update it whenever behaviour changes ship or documentation status flips.
