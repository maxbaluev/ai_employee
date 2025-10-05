# Build Log & To-Do — AI Employee Platform

This log sequences the work required to turn the validated architecture/UX into a production-grade Composio-only AI employee. Each item references the relevant code or documentation so Codex can execute tasks incrementally. Cross-reference with `docs/prd.md`, `docs/requirements.md`, and `docs/roadmap.md` before claiming tasks.

---

## 0. Environment Baseline

- [ ] Verify Node/PNPM toolchain (`node >= 18`, `pnpm --version`).
- [ ] Install UI deps (`pnpm install` or `npm install`).
- [ ] Provision Python venv in `agent/` (`scripts/setup-agent.sh`).
- [ ] Export required keys: `GOOGLE_API_KEY`, `COMPOSIO_API_KEY`, optional `OPENAI_API_KEY`.
- [ ] Run `npm run dev` and confirm:
  - Next.js app on `http://localhost:3000` renders Copilot sidebar.
  - FastAPI agent (`http://localhost:8000/`) answers health (AGUI handshake).

---

## 1. Replace Demo Tools with Composio

1. Read `docs/arch.md` §4.4 for Composio integration strategy.
2. In `agent/agent.py`:
   - [ ] Instantiate `Composio(provider=GoogleAdkProvider())` (see `libs_docs/composio_next/python/providers/google_adk/google_adk_demo.py`).
   - [ ] Fetch toolkits relevant to first objective (e.g., Gmail, HubSpot) via `tools.get`.
   - [ ] Replace hard-coded `set_proverbs` / `get_weather` tools with Composio-provided `FunctionTool`s, keeping state callbacks intact for shared state demos.
3. Persist the fetched tool schema to disk or database stub so UI can render forms later.
4. Update `.env.example` with Composio credentials expectations.
5. Add smoke test: run `runner.run` once and assert Composio tool slug appears in AGUI `ToolCallStartEvent`.

---

## 2. Tool Catalog & Policy Storage

1. Introduce backend storage (temporary JSON file or Postgres) for tool metadata described in `docs/arch.md` §4.5.
2. Schema should include: `tool_slug`, `app`, `json_schema`, `scopes`, `risk_default`, `rate_bucket`, `write_enabled`.
3. Build sync job:
   - [ ] Cron or manual command to refresh catalog from Composio (`composio.tools.get` / search filters).
   - [ ] Compare hashes to detect schema drift.
4. Expose REST endpoints:
   - `GET /tools` (filter by risk/app).
   - `PATCH /tools/{slug}` (toggle write permission, overrides risk/approval).
5. Seed catalog with initial objectives (e.g., Gmail send, HubSpot update).

---

## 3. Action Envelopes & Outbox Worker

1. Define database tables (see `docs/arch.md` §4.5 + §5) or temporary persistence for:
   - `actions` (drafted envelopes from ADK planner).
   - `outbox` (delivery queue + retry metadata).
   - `audit_log`.
2. Implement Python module `worker/outbox.py` (placeholder script referenced in `pyproject.toml`):
   - [ ] Poll pending actions.
   - [ ] Execute via Composio’s execution API (`composio.actions.run` or equivalent).
   - [ ] Handle idempotency with `external_id`.
   - [ ] Emit AGUI completion/exception events back to Runtime (HTTP callback or state update).
3. Add retry/backoff using `tenacity` with rate-bucket awareness.
4. Extend FastAPI service with endpoints:
   - `POST /actions` (enqueue from UI).
   - `POST /actions/{id}/approve|reject` (update approval state, push to Outbox).
5. Unit tests for Outbox (simulate success/error, ensure audit log entry created).

---

## 4. Evidence Generation Pipeline

1. Design Reader Kernel DSL (JSON/YAML) per `docs/arch.md` §6.
2. Implement scheduler (APScheduler) tasks:
   - `warm_scan` (run once post-connect).
   - `trickle_refresh` (every 30–60 min, respects `rate_bucket`).
3. Map kernel config → Composio read tool call.
4. Store results in `signals` table with lean payloads.
5. Update ADK agent prompt to inject signals → proposals.
6. Build UI component to surface Evidence cards (counts/exemplars).

---

## 5. UI Enhancements

1. **Desk page**:
   - [ ] Replace placeholder content with `PlanCard` list generated from shared state.
   - [ ] Implement `Approve all low-risk` button (calls backend batch API).
   - [ ] Add drag-and-drop using `@dnd-kit/core` or similar (update assignee via API).
2. **Approvals**:
   - [ ] Create table view with filters.
   - [ ] Wire edit modal to JSON schema from tool catalog (use `react-jsonschema-form` or custom renderer).
3. **Integrations**:
   - [ ] Connect to backend `/tools` endpoint to list toolkits, toggles, statuses.
   - [ ] Implement JIT scope modal; POST to backend to trigger Composio scope upgrade.
4. **Activity & Safety**:
   - [ ] Timeline fed by Outbox statuses.
   - [ ] Rate limit gauge (pull from stored metrics).
   - [ ] Pause/Undo buttons hooking to backend.
5. **Roster**:
   - [ ] Display employees, trust score, capacity.
   - [ ] Slide-over assignments editor.
6. Ensure CopilotKit Sidecar renders AGUI event stream with mapping in `docs/ux.md` §5.

---

## 6. Trust, Guardrails, and Analytics

1. Implement trust score service (daily roll-up of approvals/edits/errors).
2. Enforce guardrails before Outbox dispatch (quiet hours, DNC list, write toggles).
3. Instrument telemetry (per `docs/ux.md` §10) using either PostHog, Segment, or custom DB tables.
4. Surface trust chip + autop-run badges in UI.
5. Add audit endpoints for security persona (filter by employee/tool/date).

---

## 7. Testing & Quality Gates

- [ ] Python: Pytest suites for agent callbacks, Outbox, Composio sync, rate-limit scheduling.
- [ ] JS/TS: Component tests for PlanCard, schema form, sidecar store; E2E smoke using Playwright.
- [ ] Accessibility audit (axe, keyboard navigation).
- [ ] Load test Outbox throughput (simulate burst of actions).
- [ ] Disaster drills: Composio outage fallback (degrade to read-only), Outbox stuck scenario.

---

## 8. Deployment Checklist

- Containerize FastAPI + Outbox worker; ensure `COMPOSIO_API_KEY` and `GOOGLE_API_KEY` mount securely.
- Next.js deployed to Vercel/Edge with rewrites for `/api/copilotkit`.
- Provision Postgres with RLS (Supabase or Cloud SQL), run migrations for actions/signals/audit tables.
- Configure logging sinks (e.g., GCP Log Router, Datadog) fed by CopilotRuntime middleware + Outbox.
- Set up alerting for run errors, Outbox DLQ backlog, Composio token expiry.

---

## 9. Documentation Follow-ups

- Update README with architecture diagram (from `docs/arch.md`).
- Produce operator guide referencing `docs/ux.md` flows.
- Record Loom walkthrough once Desk + Approvals surfaces are interactive.
- Maintain changelog per sprint with links to relevant sections in `docs/arch.md`/`docs/ux.md`.

This checklist should let Codex (or any contributor) work feature-by-feature while staying aligned with the validated architecture and UX.
