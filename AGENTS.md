# AGENTS.md · AI Employee Control Plane (Ready to Run)

Status: Updated October 6, 2025 · Composio-only · One executor (Outbox) · Supabase-only ops

This file is a quick, agent‑focused guide to build, run, test, and extend the app.
For product docs and architecture, start with:
- `docs/prd/universal-ai-employee-prd.md` (canonical PRD & Architecture)
- `docs/architecture/universal-action-envelope.md` (only write contract)
- `docs/architecture/overview.md` (system diagram and invariants)

## Setup Commands
- Install toolchain and deps
  - `mise install` (Node 22, Python 3.13)
  - `pnpm install` (runs `uv sync --extra test`)
- Configure env: `cp .env.example .env` then fill keys (at minimum `GOOGLE_API_KEY` and `COMPOSIO_API_KEY`; add Supabase to run the worker/analytics)
- Start dev: `pnpm dev` (Next.js UI + FastAPI agent)

## Run & Operate
- UI only: `pnpm run dev:ui`
- Agent only: `pnpm run dev:agent` (FastAPI at http://localhost:8000)
- Health check: `curl http://localhost:8000/healthz`
- Outbox worker (requires Supabase):
  - `uv run python -m worker.outbox start`
  - `uv run python -m worker.outbox status --tenant <TENANT_ID>`
  - `uv run python -m worker.outbox drain --tenant <TENANT_ID> --limit 20`
  - `uv run python -m worker.outbox retry-dlq --tenant <TENANT_ID> --envelope <ENV_ID>`
- Analytics endpoints (Supabase‑backed, no external telemetry):
  - `GET /analytics/outbox/status?tenant=<id>` → queue + DLQ counts
  - `GET /analytics/guardrails/recent?tenant=<id>&limit=20` → latest guardrail events
  - `GET /analytics/cron/jobs?limit=20` → cron runs

## Testing & Linting
- JS tests: `pnpm test`
- Python tests: `uv run python -m pytest`
- Lint: `pnpm lint` (Next.js ESLint rules)

## Code Style
- TypeScript: strict mode; Next.js ESLint config; Prettier (single quotes, trailing commas)
- Python: pydantic models + pure guardrail modules; avoid side effects in callbacks/services
- Logging: `structlog`; scrub secrets before logging

## Project Map
- Agent runtime
  - `agent/app.py` – FastAPI app; mounts ADK agent (typed roles); healthz/readyz; analytics router
  - `agent/agents/` – `control_plane.py` factory + `coordinator.py` multipliers
  - `agent/callbacks/` – before/after modifiers; guardrail glue
  - `agent/guardrails/` – quiet hours, trust, scopes, evidence (pure `check(...)` before model call)
  - `agent/services/` – settings, catalog, outbox, objectives, audit, state helpers
  - `agent/schemas/envelope.py` – envelope DTO + shared‑state helpers
- Worker
  - `worker/outbox.py` – Supabase‑backed queue executor with retries/DLQ
- Frontend (five surfaces)
  - `src/app/(workspace)/desk/page.tsx` – Plan of Day (approve/edit/skip; approve low-risk)
  - `src/app/(workspace)/approvals/page.tsx` – schema‑driven approvals (from Composio JSON Schemas)
  - `src/app/(workspace)/activity/page.tsx` – outbox timeline, DLQ, guardrail banners
  - `src/app/(workspace)/integrations/page.tsx` – Composio connect, Allowed Writes, JIT Scope
  - `src/app/(workspace)/hire/page.tsx` – hire/roster & assignments drawer
- Docs
  - `docs/prd/universal-ai-employee-prd.md` – PRD & Architecture (Composio-only)
  - `docs/architecture/universal-action-envelope.md` – only write contract
  - `docs/architecture/data-model.md` – minimal RLS schema
  - `docs/architecture/*` – control plane, frontend, data roadmap
  - `docs/operations/*` – runbooks + Supabase dashboards
  - `docs/use_cases/*` – operator workflows

## Guardrails & Safety
- All guardrails are pure functions (`check(...) -> GuardrailResult`) and run in
  `build_before_model_modifier` prior to model calls.
- On block: short‑circuit with a refusal, log via audit service, and set
  `callback_context.end_invocation = True`.
- Shared state mutations (desk/approvals/guardrails/outbox) reassign top‑level keys so
  AGUI emits JSON Patch deltas; UI updates in real time.
- Observability for Phase 5 stays inside Supabase (no Prometheus). Use analytics routes
  and saved SQL/dashboard widgets in Supabase for ops.

## Invariants (do not violate)
- One universal write (`mcp.exec` Action Envelope); agents never write directly.
- One executor (Outbox). Idempotency enforced via `actions.external_id`.
- Schema-driven UI (JSON Schemas from Composio) – no per-tool React forms.
- Strict RLS on all tables; browser never sees secrets.

## Environment Keys (excerpt)
- `GOOGLE_API_KEY` – model access for ADK agent
- `COMPOSIO_API_KEY` – required; enables all Composio MCP tools. No other Composio env vars are needed for default (hosted) auth.
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY` – required for worker/analytics (optional for UI‑only demos)
- `COMPOSIO_DEFAULT_TOOLKITS` – optional; leave empty to fetch ALL toolkits via MCP (set to restrict, e.g., `GITHUB,SLACK`).
- `COMPOSIO_DEFAULT_SCOPES` – optional; tenant‑wide baseline scopes appended to proposals.

## PR Guidelines (for agents)
- Keep changes surgical and aligned with the structure above
- Update tests/docs with behaviour changes; run `pnpm test` and `pytest` before finishing
- Don’t introduce new external telemetry; Phase 5 uses Supabase‑only analytics

## Troubleshooting
- UI connected but no state: verify `NEXT_PUBLIC_COPILOTKIT_URL=/api/copilotkit` and that
  the agent is serving on port 8000
- Empty catalog: ensure `COMPOSIO_API_KEY` is set. If you intentionally restricted
  discovery, set `COMPOSIO_DEFAULT_TOOLKITS` accordingly or leave it blank to load all.
- Worker idle: verify Supabase keys and that `outbox` has `status='pending'` rows

For deeper context, start with `docs/prd/universal-ai-employee-prd.md`,
`docs/getting-started/core-concepts.md`, and `docs/architecture/agent-control-plane.md`.
