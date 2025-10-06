# AI Employee Platform — PRD & Architecture

Status: Updated October 6, 2025 · Composio‑only · Universal MCP · Value‑Iterative

Audiences: Product · Engineering · Security · Design

Stack: React (CopilotKit + AG‑UI) · FastAPI · Supabase (RLS) · ADK Agents · LiveKit · Composio MCP (only)

> One‑line promise: Connect Composio, declare your outcomes, and your AI employee will discover opportunities, show evidence, and execute safe, approved actions across any Composio tool—learning and improving every day.

---

## 1) PRD (Product)

### 1.1 Problems

- Customers use many tools; some lack notifications; work falls through cracks.
- Business value is not in APIs; outcomes must be declared and plans must be data‑backed.
- Teams want immediate value without custom integrations, and strong guardrails.

### 1.2 Goals

- G1 Universal (Composio‑only): Any Composio tool works day‑one via a single universal action (no per‑tool code).
- G2 Value‑iterative: Plans driven by Value Objectives; proposals cite evidence; learning from approvals/edits.
- G3 Lightweight core: one executor, schema‑driven forms, small typed agents, minimal persistent data.
- G4 Safety: least‑privilege scopes, approvals, idempotency, rate buckets, quiet hours, DNC, audit, undo, pause.
- G5 Native multi‑employee: roster switcher, global desk, tiny assignments drawer.

### 1.3 Success metrics

- Connect→Value ≤ 60s (first approved action executes).
- ≥70% proposals approved without edits by week 2.
- ≥65% tenants connect ≥2 Composio apps in first session.
- ≥99% approved actions complete ≤5 min (p95).
- Leading indicators for each objective improve week‑over‑week.

### 1.4 Scope (v1)

- Five surfaces: Desk, Approvals, Activity & Safety, Integrations (Composio), Hire/Roster.
- Employees: 1→N with shared approvals and light routing.
- Actions: any Composio tool via `mcp.exec`; phone calls via LiveKit worker.
- Proactivity: pull‑based readers (even w/o notifications) + optional Composio triggers.

### 1.5 Non‑goals (v1)

- Vendor MCPs, custom connectors, offline uploads/BYO tokens, destructive/financial ops by default, deep app‑specific UI.

---

## 2) Core Concepts

- Value Objective: user‑declared outcome (e.g., “Increase demos 20% in 30 days”).
- Capability Graph: normalized abilities from Composio (e.g., “can read tickets”, “can send email”).
- Signals: small summaries (counts + exemplars) produced by Reader Kernels via Composio read tools.
- Evidence Card: human‑readable proof (“12 tickets >24h; examples TCK‑842, TCK‑909, TCK‑911”).
- Proposed Actions: drafts tied to objectives and evidence; each is a universal Action Envelope.
- Outbox: the only executor for writes.
- Trust Score: per‑employee metric that gates autonomy.

---

## 3) UX (Operator experience)

Five surfaces: Desk, Approvals, Activity & Safety, Integrations (Composio), Hire/Roster.

- Desk (Global & Individual): Plan of Day (5–15 cards) + AG‑UI sidecar narration.
  - Card: title, why (Evidence snippet), risk badge, Approve / Edit / Skip
  - Approve all low‑risk one‑click
- Approvals: grouped by app & employee; schema‑driven forms from Composio tool schemas.
- Activity & Safety: Outbox health, retries, DLQ, rate‑limit badges; Pause/Undo.
- Integrations (Composio): Connect Composio, discover tools, Allowed Writes toggles; JIT connect/upgrade; ROI meter.
- Hire / Roster: first hire wizard; roster chips (All | A | B | +) and Assignments drawer.

Value onboarding (≤2 minutes): choose 1–3 Value Objectives, set guardrails, see immediate results after Warm Scan.

---

## 4) Architecture (minimal & universal)

```
React (Vite/Next) + CopilotKit (AG‑UI)
──────────────────────────────────────
• Desk, Approvals, Activity, Integrations, Roster
• SSE AG‑UI stream (narration, tool events, approvals)
• Schema-driven Action Preview (from Composio JSON Schemas)

FastAPI (Gateway & Control Plane)
────────────────────────────────
• Auth (Supabase JWT), CORS
• AG‑UI sessions (/agui/session, /agui/input)
• Objectives / Employees / Plan / Approvals / Activity APIs
• Composio Broker (only source of tools)
• Schedulers: Warm Scan + Trickle Refresh
• Outbox Relay (single executor for writes; idempotent)

Supabase/Postgres (RLS)
───────────────────────
• Minimal state: objectives, employees, program_assignments, tasks, actions, outbox,
  tools_catalog, tool_policies, signals (optional), call_jobs, call_outcomes, audit_log, trust_ledger

ADK Agents (typed I/O)
──────────────────────
• Outcome Planner • Drafter • Compliance • QA/Eval

LiveKit Worker (existing)
─────────────────────────
• claim→dial→outcome; transcripts; enqueue crm.activity via Outbox
```

Invariants: one universal write, one executor, one UI stream; zero per‑tool code; typed agents; strict RLS.

---

## 5) Composio‑only Integration

- Single connection per tenant; discover apps/tools and JSON Schemas via Composio MCP.
- Allowed Tools & risk policy stored per tool: risk_default, approval_default, write_allowed, rate_bucket.
- JIT Connect & JIT Scope Upgrade: on approve, prompt minimal scope upgrade; original action auto‑executes.
- Connection health: per‑tool status (connected, missing_scope, expired, error) displayed in Integrations and on cards.

---

## 6) Planning across many tools

Reader Kernels (config, not code): generic pull readers via Composio read tools (e.g., `changes_since`, `deadline_window`, `stale_items`).

Signals & Evidence Cards: small stored signals; rendered evidence with counts, ages, exemplars, last refreshed.

Value Programs: YAML/JSON mapping Signals → Proposed Actions with micro‑estimates of Δ on leading metrics. Top 5–15 become Plan of Day.

---

## 7) The only write: Action Envelope (`mcp.exec`)

```json
{
  "action_id":"uuid",
  "external_id":"stable-id",
  "tenant_id":"uuid",
  "employee_id":"uuid",
  "type":"mcp.exec",
  "tool":{"name":"slack.chat.postMessage","composio_app":"slack"},
  "args":{"channel":"#cs","text":"Daily digest …"},
  "risk":"low|medium|high",
  "approval":"auto|required|granted|denied",
  "constraints":{"rate_bucket":"slack.minute","must_run_before":"2025-10-05T17:00:00Z"},
  "result":{"status":"pending|sending|sent|failed|conflict|skipped","provider_id":"ts_123","error":null},
  "timestamps":{"created_at":"…","sent_at":null,"completed_at":null}
}
```

Executor: Outbox only (idempotent, jittered retries, DLQ). UI is schema‑driven from Composio JSON Schemas.

---

## 8) ADK Agents (typed, small, effective)

- Outcome Planner: builds plan from Value Objectives + Capability Graph + Signals; emits AG‑UI narration + Evidence.
- Drafter: populates args via short promptlets; enforces tone/length/links.
- Compliance: assigns risk; enforces quiet hours, DNC, rate buckets; marks APPROVAL_REQUIRED; JIT scopes.
- QA/Eval: samples drafts; checks tone/sensitive terms; updates Trust Score; suggests template tweaks.

ADK never writes to tools—only proposes envelopes. Outbox executes.

---

## 9) Multi‑employee (native & minimal)

- Roster chips: All | A | B | +; Global Desk grouped by employee; drag‑to‑reassign.
- Assignments drawer: per program capacity/day and priority per employee.
- Trust gates per employee: <0.6 Propose; 0.6–0.8 Assist; >0.8 Trusted (auto low + pre‑approved medium; never high).

---

## 10) APIs (frontend ↔ backend)

- `POST /composio/connect`, `GET /composio/tools`
- `POST /objectives`, `POST /employees`, `POST /plan/run?employee_id=`
- `POST /approvals`, `POST /tasks/{id}/reassign`, `POST /employee/{id}/pause|resume`
- `GET /activity?cursor=&employee_id?=`

AG‑UI events (subset): RUN_STARTED, RUN_FINISHED, TEXT_MESSAGE_*, TOOL_CALL_*, STATE_DELTA, APPROVAL_REQUIRED, APPROVAL_DECISION, ERROR.

---

## 11) Data Model (RLS‑scoped, minimal)

Tables: objectives, employees, program_assignments, tasks, actions, outbox, tools_catalog, tool_policies, signals (optional), contacts_lite, call_jobs, call_outcomes, audit_log, trust_ledger. See `docs/architecture/data-model.md` for details and indexes.

---

## 12) Scheduling & Rate Limits

- Warm Scan (post‑connect): at most 1–2 reads per category.
- Trickle Refresh (30–60 min): top‑N deltas; respect rate buckets (`email.daily`, `slack.minute`, `tickets.api`).
- On‑demand: narrow reads for visible proposals.
- Degradation: UI shows “delayed by provider limits”.

---

## 13) Security & Compliance

- Composio‑only; least‑privilege scopes; JIT upgrades tied to concrete actions.
- Allowed Tools double‑gated (Composio + Broker); high‑risk off by default.
- Backend‑only writes; RLS isolation; quiet hours & DNC; audit with PII minimisation.

---

## 14) Observability, SLAs, Runbooks

Metrics: connect→value, approvals/edit rate, Outbox latency/retries, rate‑limit hits, Trust trend, objective leading indicators.

SLAs: read/control 99.9%; Outbox 99.5%; completion p95 ≤ 5 min; freshness ≤ 60 min.

Runbooks: outbox stuck, schema change, Composio outage. See `docs/operations/runbooks/*`.

---

## 15) Acceptance Criteria

Per page checklists for Integrations, Desk, Approvals, Activity & Safety, Hire/Roster, A11y. See the dedicated section in this file when designing or testing.

---

## 16) Wireframes & Sidecar

Condensed ASCII for Desk and Integrations plus an AG‑UI event → UI mapping table. Implement the Sidecar as documented in `docs/implementation/sidecar-agui.md`.

---

## 17) Future Hooks

Daily summary modal, weekly value review, team switcher—no new pages required.

---

Links: architecture overview (`docs/architecture/overview.md`), action envelope (`docs/architecture/universal-action-envelope.md`), data model (`docs/architecture/data-model.md`), Composio execution (`docs/architecture/composio-execution.md`).

