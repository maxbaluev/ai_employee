# Build Log & To-Do — AI Employee Platform (Final)

Follow this sequence to implement the platform quickly while keeping Codex fully informed. Each step cites relevant docs.

---

## 0. Environment Baseline

- [ ] Confirm toolchain: `node -v (>=18)`, `pnpm --version`, `python3 --version (>=3.11)`.
- [ ] Install JS deps (`pnpm install`) and Python agent deps (`npm run install:agent`).
- [ ] Copy `.env.example` → `.env`, fill `GOOGLE_API_KEY`, `COMPOSIO_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` (once available).
- [ ] Run `npm run dev` (UI + agent). Verify:
  - `http://localhost:3000` renders CopilotKit sidebar with sample agent.
  - `http://localhost:8000/` returns AGUI metadata (check via curl; should stream events on run).

---

## 1. Replace Demo Tools with Composio (docs/arch.md §4.3, docs/requirements.md FR-023)

1. In `agent/agent.py`:
   - [ ] Initialize `Composio(provider=GoogleAdkProvider())` (see `libs_docs/composio_next/python/providers/google_adk/google_adk_demo.py`).
   - [ ] Fetch initial toolkits (`GMAIL`, `SLACK`, `HUBSPOT`, etc.) via `composio.tools.get(user_id, toolkits=...)`.
   - [ ] Replace `set_proverbs`/`get_weather` with Composio FunctionTools (use ADK helper to wrap, preserving callbacks/state scaffolding).
2. Add `.env.example` entry for `COMPOSIO_API_KEY`; update README Quickstart.
3. Smoke test: run agent manually (`uvicorn agent.agent:app --reload`), send request via CopilotKit to verify `ToolCallStartEvent` references Composio slug.

---

## 2. Tool Catalog & Connected Accounts (docs/arch.md §4.4, docs/requirements.md FR-003/FR-020)

- [ ] Create persistence layer (start with JSON/YAML stub; later Postgres) storing tool metadata: `slug`, `app`, `json_schema`, `scopes`, `risk_default`, `rate_bucket`, `write_allowed`.
- [ ] Implement sync command (`scripts/sync_tools.py`) pulling from `composio.tools.get` and writing catalog.
- [ ] Build connected account manager using `composio.connected_accounts.*` APIs; expose `/composio/connect`, `/composio/accounts` endpoints.
- [ ] Update Integrations UI to read from catalog and list tools/status.

---

## 3. Data Layer & APIs (docs/arch.md §4.5, docs/requirements.md §4)

- [ ] Define database schema (SQL or migrations) for tenants, objectives, employees, guardrails, signals, tasks, actions, outbox, audit.
- [ ] Implement FastAPI endpoints:
  - Objectives (`POST/GET/PUT /objectives`).
  - Guardrails (`PUT /guardrails`).
  - Plan run trigger (`POST /plan/run` returning AGUI session info).
  - Approvals (`POST /approvals`, `POST /approvals/bulk`).
  - Activity (`GET /activity`, `GET /audit`).
  - Tools (`GET /tools`, `PATCH /tools/{slug}`).
- [ ] Integrate Supabase RLS policies or SQLAlchemy filters to enforce tenant isolation.

---

## 4. Evidence Pipeline (docs/arch.md §4.4, docs/requirements.md FR-010/FR-011)

- [ ] Define reader kernel DSL (YAML) with fields: `tool_slug`, `args`, `jsonpath_select`, `features`, `examples`.
- [ ] Implement kernel executor using `composio.tools.execute` and `jsonpath-ng` to compute Signals.
- [ ] Add APScheduler jobs for warm_scan (post-connect) and trickle_refresh (every 30–60m). Respect rate buckets.
- [ ] Persist Signals + Evidence cards; expose to ADK agent via state injection and REST.

---

## 5. Planner Enhancements (docs/arch.md §5, `agent/agent.py`)

- [ ] Update ADK agent prompt to include objectives, guardrails, and signals.
- [ ] Emit structured state updates (plan cards, evidence references) via `callback_context.state` so CopilotKit UI can consume via `useCoAgent`.
- [ ] Add compliance checks in `before_model_callback` (e.g., quiet hours) to prune invalid proposals pre-approval.

---

## 6. Schema-Driven UI (docs/ux.md §§4–6)

- [ ] Build Desk, Approvals, Integrations, Activity & Safety, Hire/Roster pages.
- [ ] Use generic card/table components; fetch data via REST + CopilotKit state.
- [ ] Integrate `react-jsonschema-form` (or lightweight alternative) for editing action arguments. Validate before approval.
- [ ] Implement JIT scope modal & flows tied to `/composio/connect` endpoints.
- [ ] Add drag-and-drop (e.g., `@dnd-kit`) for Global Desk reassignment.

---

## 7. Outbox Worker (docs/arch.md §4.4, docs/requirements.md FR-022)

- [ ] Create `worker/outbox.py` script invoked via `python -m worker.outbox`.
- [ ] Implement queue polling with DB locking or message queue placeholder.
- [ ] Execute actions via `composio.tools.execute`, passing `connected_account_id`, `external_id`, `arguments`.
- [ ] Handle retries, DLQ, quiet hours, rate buckets. Update audit and Activity timeline.
- [ ] Emit metrics (`outbox_delivery_seconds`, `outbox_failures_total`).

---

## 8. Trust & Autonomy (docs/requirements.md FR-032, docs/ux.md §7)

- [ ] Build trust ledger computations (daily job).
- [ ] Auto-approve low-risk actions when trust > threshold; mark in audit.
- [ ] Surfacing trust chip/trend in UI.

---

## 9. Observability & Compliance (docs/observability.md, docs/threat-model.md)

- [ ] Instrument CopilotRuntime and Outbox with OpenTelemetry metrics/traces.
- [ ] Implement structured logging guidelines (hash PII).
- [ ] Set up basic dashboards/alerts (temporary with console or hosted service).
- [ ] Draft runbooks (Composio outage, Outbox DLQ) in `runbooks/`.

---

## 10. Testing & Hardening (docs/requirements.md §8, docs/nfr.md)

- [ ] Pytest suites for planner, guardrails, Outbox (mock Composio).
- [ ] Playwright E2E: connect flow (mock), warm scan injection, approval, JIT scope, Outbox completion.
- [ ] Security tests for RLS, quiet hours, logging hygiene.
- [ ] Load test Outbox throughput (simulate 100 queued actions) using Locust or custom script.

---

## 11. Launch Checklist

- [ ] README + Makefile (or Taskfile) updated with commands (`make dev`, `make test`, `make outbox`).
- [ ] `codex.yml` created with run/test commands, entrypoints, no-touch paths.
- [ ] Production env provisioning plan (Supabase, deployment target) documented in `infra/` (future).
- [ ] Handoff deck summarizing architecture, UX, runbooks.

Keep this list synchronized with progress; update docs + ADRs when decisions shift. Codex should reference this file at task kickoff to avoid redundant planning.
