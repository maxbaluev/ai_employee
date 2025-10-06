# Core Concepts (Universal)

**Status:** Implemented (Next.js UI + FastAPI control plane + Supabase/Composio services + coordinator + approvals scaffolds) ·
In progress (integrations UX)

The platform is Composio-only with one universal write (Action Envelope) executed only by
the Outbox worker. It leans on CopilotKit (UI), Google ADK (agents), and Supabase (RLS
data/ops). Use this page to orient yourself before diving into detailed docs.

Key terms (see `docs/references/glossary.md`): Value Objective, Capability Graph,
Signals, Evidence Card, Proposed Action, Action Envelope, Outbox, Trust Score.

## 1. User Experience Layer (Next.js + CopilotKit)

- `src/app/api/copilotkit/route.ts` instantiates a `CopilotRuntime` and proxies AGUI
  streaming traffic to the Python agent with `HttpAgent` from `@ag-ui/client`.
- `src/app/(workspace)/*` hosts the desk, approvals, and overview pages. Each subscribes
  to the agent via `useCoAgent`, renders schema-driven UI, and reacts to
  `useCopilotAction` signals (highlighting, optimistic updates, etc.).
- `docs/implementation/frontend-shared-state.md` documents the state contracts while the
  CopilotKit vendor samples in `libs_docs/copilotkit_docs/` and
  `libs_docs/copilotkit_examples/` show how `StateDeltaEvent`s, predictive updates, and
  action handlers combine for richer UX.
- Planned: expand the Desk into the Approvals and Integrations surfaces once the
  multi-employee coordinator lands.

## 2. Agent Runtime (FastAPI + Google ADK)

- `agent/app.py` boots FastAPI, mounts the ADK bridge with
  `ag_ui_adk.add_adk_fastapi_endpoint`, and exposes `/` plus `/healthz`.
- `agent/agents/control_plane.py` composes the production agent:
  `DeskBlueprint`, `enqueue_envelope` tool, Composio-aware catalog/outbox services, and
  dedicated before/after callbacks. Guardrails run inside `agent/guardrails/` to enforce
  quiet hours, trust, scope, and evidence policies.
- Callback structure mirrors the ADK patterns captured in
  `libs_docs/adk/full_llm_docs.txt`, including safe early termination with
  `ctx.end_invocation = True`.
- Settings (`agent/services/settings.py`) provide a typed facade over environment
  variables so the runtime flips between in-memory doubles and Supabase-backed services
  without code changes.
- `agent/agents/coordinator.py` orchestrates multi-employee flows on top of the same
  callback + service contracts, keeping surface-specific wiring light, while the
  callbacks now emit `StateDeltaEvent`s for desk queues, approvals, guardrails, and
  outbox metadata.

## 3. Composio Execution Layer (only source of tools)

- `agent/services/catalog.py` ships `ComposioCatalogService` for live SDK discovery,
  `InMemoryCatalogService` for tests, and `SupabaseCatalogService` for persistence. When
  Supabase credentials are present, the control plane syncs toolkit metadata straight
  into Postgres before serving requests.
- `agent/services/outbox.py` and `worker/outbox.py` provide a Supabase-backed queue,
  Tenacity-powered retries, and DLQ management. The worker hydrates a Composio client via
  `GoogleAdkProvider` (see `libs_docs/composio_next/python/providers/google_adk/`).
- Allowed Tools & policy are stored per tool (risk_default, approval_default,
  write_allowed, rate_bucket). JIT connect/scope upgrades unblock approved actions with
  minimal scopes and auto-execute once granted.
- Vendor references in `libs_docs/composio_next/` and `libs_docs/adk/` are mirrored in our
  services so you can trace behaviour back to upstream examples when debugging.

## 4. Data Plane & Supabase Services (minimal RLS schema)

- Baseline schema + demo data live in `db/migrations/001_init.sql` and
  `db/seeds/000_demo_tenant.sql`. The control plane defaults to Supabase implementations
  whenever `supabase_url` and `supabase_service_key` are configured.
- `agent/services/supabase.py` exposes a cached client factory, while
  `agent/services/audit.py`, `objectives.py`, and `state.py` provide concrete adapters for
  audit trails, shared objectives, and shared state respectively.
- Supabase Cron is the authoritative scheduler for catalog sync and telemetry jobs—see
  `docs/operations/run-and-observe.md` for the managed list. Reference patterns in
  `libs_docs/supabase/llms_docs.txt` (cron scheduling, Edge Functions, vector search) when
  adding new jobs or AI-backed workflows.
- Planned: hydrate vector embeddings (`evidence_embeddings`), edge functions for
  webhooks, and connected-account lifecycle automation.

## 5. Observability & Safety

- Structlog-backed audit trails (`agent/services/audit.py`) capture guardrail outcomes,
  queue transitions, and worker attempts today. Prometheus metrics and OTEL tracing are
  next on the roadmap (see `docs/operations/run-and-observe.md`).
- Guardrail expectations, refusal copy, and escalation paths are defined in
  `docs/governance/security-and-guardrails.md`. Shared-state deltas emitted by
  `agent/callbacks/after.py` keep the UI consistent with gate decisions.

Keep this mental model handy—the rest of the documentation assumes you understand how
the runtime, data plane, and vendor SDKs align.
