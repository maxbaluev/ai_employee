Below is the **from‑scratch, contract‑ready PRD + Architecture** for an **AI Employee Platform** that is:

- **Composio‑only** (single MCP source of truth; no vendor MCPs, no BYO tokens, no side channels).
- **Universal across any Composio tool** from day one (email, docs, chat, CRM, tickets, calendar, dev, billing, etc.).
- **Value‑iterative** (plans derive from user outcomes, then improve with evidence and feedback).
- **Lightweight and robust** (one universal action, one executor, schema‑driven UI, typed agents, strict RLS).

It builds on your existing stack: **Vite/React + CopilotKit/AG‑UI** (UI), **FastAPI** (gateway), **Supabase/Postgres (RLS)** (state), **Google ADK** (agents), and **LiveKit** (calls).

---

# AI Employee Platform — PRD & Architecture

**(Composio‑Only, Universal MCP, Value‑Iterative)**

**Version:** 3.0
**Audiences:** Product · Engineering · Security · Design
**Stack:** React (CopilotKit + AG‑UI) · FastAPI · Supabase (RLS) · ADK Agents · LiveKit · **Composio MCP (only)**

---

## 0) One‑line promise

> Connect Composio, declare your outcomes, and your AI employee will **discover opportunities**, **show evidence**, and **execute safe, approved actions** across _any Composio tool_—learning and improving every day.

---

## 1) PRD (Product)

### 1.1 Problems

- Customers use **many tools**; some **lack notifications**; work falls through cracks.
- **Business value is not in APIs**; outcomes must be **declared** and plans must be **data‑backed**.
- Teams want **immediate value** without custom integrations, and **strong guardrails**.

### 1.2 Goals

- **G1 Universal (Composio‑only):** Any Composio tool works day‑one via a **single universal action** (no per‑tool code).
- **G2 Value‑iterative:** Plans driven by **Value Objectives**; proposals cite **evidence**; learning from approvals/edits.
- **G3 Lightweight core:** one executor, schema‑driven forms, small typed agents, minimal persistent data.
- **G4 Safety:** least‑privilege scopes, approvals, idempotency, rate buckets, quiet hours, DNC, audit, undo, pause.
- **G5 Native multi‑employee:** roster switcher, global desk, tiny assignments drawer.

### 1.3 Success metrics

- **Connect→Value ≤ 60s** (first approved action executes).
- **≥70%** proposals approved without edits by week 2.
- **≥65%** tenants connect ≥2 Composio apps in first session.
- **≥99%** approved actions complete ≤5 min (p95).
- Leading indicators for each objective improve week‑over‑week.

### 1.4 Scope (v1)

- Five surfaces: **Desk**, **Approvals**, **Activity & Safety**, **Integrations (Composio)**, **Hire/Roster**.
- Employees: 1→N with shared approvals and light routing.
- Actions: **any Composio tool** via `mcp.exec`; phone calls via LiveKit worker.
- Proactivity: **pull‑based readers** (even w/o notifications) + optional Composio triggers.

### 1.5 Non‑goals (v1)

- Vendor MCPs, custom connectors, offline uploads/BYO tokens, destructive/financial ops by default, deep app‑specific UI.

---

## 2) Core Concepts

- **Value Objective**: user‑declared outcome (e.g., “Increase demos 20% in 30 days”).
- **Capability Graph**: normalized abilities from Composio (e.g., “can read tickets”, “can send email”, “can create doc”).
- **Signals**: small summaries (counts + exemplars) produced by **Reader Kernels** via **Composio read tools**.
- **Evidence Card**: human‑readable proof (“9 trials ≤7d; examples D‑309, D‑322”).
- **Proposed Actions**: draft tasks tied to objectives and evidence; each is a **universal Action Envelope**.
- **Outbox**: the **only** executor for writes.
- **Trust Score**: per‑employee metric that gates autonomy.

---

## 3) UX (Operator experience)

### 3.1 Surfaces (five)

1. **Desk** (Global & Individual): Plan of Day (5–15 cards) + **AG‑UI sidecar** narration
   - Card: title, _why_ (Evidence Card snippet), risk badge, **Approve / Edit / Skip**
   - **Approve all low‑risk** one‑click

2. **Approvals**: grouped by app & employee; **schema‑driven forms** from Composio tool schemas
3. **Activity & Safety**: Outbox health, retries, DLQ, rate‑limit badges; **Pause/Undo**
4. **Integrations (Composio)**:
   - **Connect Composio** (once per tenant)
   - **Discover apps & tools** (from Composio)
   - **Allowed Writes** toggles per tool; **JIT Connect/Scope Upgrade** when an approved action needs missing access
   - ROI meter: “This connect unlocks X concrete tasks now”

5. **Hire / Roster**: first hire wizard; then roster chips (All | A | B | +) and **Assignments drawer** (capacity per program)

### 3.2 Value onboarding (2 minutes)

- Choose 1–3 **Value Objectives** (templates + custom).
- Set guardrails (quiet hours, channels allowed, tone), and autonomy default (Propose).
- Results appear **immediately** on Desk after **Warm Scan**.

### 3.3 Proactivity without notifications

- After connect, **Warm Scan** runs (tiny read bursts) to produce **Evidence Cards**.
- Then **Trickle Refresh** (30–60 min) to keep Signals current.
- If Composio exposes triggers for an app, we also ingest them as **Task Seeds**.

---

## 4) Architecture (minimal & universal)

```
React (Vite) + CopilotKit (AG‑UI)
────────────────────────────────
• Desk, Approvals, Activity, Integrations, Roster
• SSE AG‑UI stream (narration, tool events, approvals)
• Schema-driven Action Preview (from Composio JSON Schemas)

FastAPI (Gateway & Control Plane)
────────────────────────────────
• Auth (Supabase JWT), CORS
• AG‑UI sessions (/agui/session, /agui/input)
• Objectives / Employees / Plan / Approvals / Activity APIs
• Composio Broker (only source of tools):
   - Connect Composio → store tenant binding
   - Discover tools & JSON Schemas → tools_catalog
   - Allowed Tools, risk defaults, rate buckets
   - JIT Connect & JIT Scope Upgrade per approved action
• Schedulers:
   - Warm Scan (post connect; read-only)
   - Trickle Refresh (small deltas) per category
• Outbox Relay (single executor for writes; idempotent)
• Optional: Composio trigger/webhook ingest

Supabase/Postgres (RLS)
───────────────────────
• Minimal state: objectives, employees, program_assignments, tasks, actions, outbox,
  tools_catalog, tool_policies, contacts_lite, signals (optional),
  call_jobs, call_outcomes, audit_log, trust_ledger

ADK Agents (typed I/O)
──────────────────────
• Outcome Planner (select readers → Signals → Proposals)
• Drafter (args population; short promptlets; guardrails)
• Compliance (risk; quiet hours; DNC; rate buckets; JIT scopes)
• QA/Eval (sample drafts; trust scoring; prompt tweaks)

LiveKit Worker (existing)
─────────────────────────
• claim→dial→outcome; consent; transcripts
• enqueue crm.activity via Outbox
```

**Invariants**: one universal write, one executor, one UI stream; zero per‑tool code; typed agents; strict RLS.

---

## 5) Composio‑only Integration (how we use it)

### 5.1 Single connection, many tools

- Tenant links **one Composio account**.
- We **discover** all available **apps/tools** and their **JSON Schemas** via Composio MCP.
- We never call vendor APIs directly; all reads/writes go through Composio MCP.

### 5.2 Allowed Tools & risk policy

- For each tool: store **risk_default**, **approval_default**, **write_allowed**, **rate_bucket**.
- High‑risk categories (finance/public social/devops/destructive) default **off**; must be explicitly enabled.

### 5.3 JIT Connect & JIT Scope Upgrade (conversion‑first)

- If user approves an action that needs a missing app/scope:
  - Show **“Connect X with minimal scope Y”** modal with the concrete **value** it unlocks.
  - On success, the **original action executes automatically** (no extra clicks).

### 5.4 Connection health

- Maintain per‑tool **status**: connected, missing_scope, expired, error.
- Display in **Integrations** and on **blocked action cards** with a one‑click fix.

---

## 6) Planning across many tools (without notifications)

### 6.1 Reader Kernels (config, not code)

Generic pull readers invoked via Composio **read tools**:

- `changes_since`, `deadline_window`, `stale_items`, `backlog_over_sla`,
  `reply_needed`, `meeting_followups`, `doc_gap`, `keyword_spike`,
  `anomaly_count`, `ownerless_items`, `top_accounts`.

**Per‑tool config** (stored alongside tool in `tools_catalog` or `tool_policies`) defines JSONPath selectors, feature extractions, and exemplars—no app‑specific code.

### 6.2 Signals & Evidence Cards

**Signal** (stored small):

```json
{
  "id": "sig_24h_backlog",
  "tenant_id": "t1",
  "kind": "backlog_over_sla",
  "source_tool": "zendesk.tickets.list",
  "features": { "backlog_count": 12, "oldest_age_hours": 56 },
  "examples": ["TCK-842", "TCK-909", "TCK-911"],
  "updated_at": "2025-10-03T12:20:00Z"
}
```

**Evidence Card** (rendered):
“12 open tickets >24h (Zendesk.tickets.list, status=open). Oldest 56h. Examples: TCK‑842, TCK‑909, TCK‑911.”

### 6.3 Value Programs (objective → proposals)

Small YAML/JSON mapping **Signals** → **Proposed Actions** (one or many envelopes), with micro‑estimates of **Δ on leading metrics**.

**Priority score**:

```
score = (Δmetric_estimate × confidence_from_history) / (effort × risk_factor)
```

Top 5–15 become **Plan of Day**.

---

## 7) The only write: **Action Envelope** (`mcp.exec`)

```json
{
  "action_id": "uuid",
  "external_id": "stable-id", // idempotent
  "tenant_id": "uuid",
  "employee_id": "uuid",
  "type": "mcp.exec",
  "tool": { "name": "slack.chat.postMessage", "composio_app": "slack" },
  "args": { "channel": "#cs", "text": "Daily digest …" },
  "risk": "low|medium|high",
  "approval": "auto|required|granted|denied",
  "constraints": {
    "rate_bucket": "slack.minute",
    "must_run_before": "2025-10-05T17:00:00Z"
  },
  "result": {
    "status": "pending|sending|sent|failed|conflict|skipped",
    "provider_id": "ts_123",
    "error": null
  },
  "timestamps": { "created_at": "…", "sent_at": null, "completed_at": null }
}
```

- **Executor**: **Outbox** only (idempotent, retries with jitter, DLQ).
- **Schema‑driven UI**: Preview & validation come directly from Composio **JSON Schemas**; no per‑tool UI code.

---

## 8) ADK Agents (typed, small, effective)

- **Outcome Planner**: builds plan from **Value Objectives** + **Capability Graph** + **Signals**; emits AG‑UI narration + Evidence Cards.
- **Drafter**: populates `args` via **short promptlets** (tone/length/links enforced).
- **Compliance**: assigns risk, enforces **quiet hours, DNC, rate buckets**, marks **APPROVAL_REQUIRED**, initiates **JIT Connect/Scope** flows when needed.
- **QA/Eval**: samples drafts; checks tone/sensitive terms; updates **Trust Score** from approvals/edits/errors; suggests template tweaks.

> ADK **never** writes to tools—only proposes envelopes. Outbox executes.

---

## 9) Multi‑employee (native & minimal)

- **Roster chips**: All | A | B | + (header).
- **Global Desk**: combined plan; cards grouped by employee; **drag‑to‑reassign**.
- **Assignments drawer**: per program **capacity/day** & **priority** per employee.
- **Trust gates** per employee:
  - `<0.6` Propose (all approvals),
  - `0.6–0.8` Assist (auto for low‑risk internal),
  - `>0.8` Trusted (auto low + pre‑approved medium; never high).

---

## 10) APIs (frontend ↔ backend)

- `POST /composio/connect` → start tenant binding to Composio; callback stores link.
- `GET /composio/tools` → list discovered tools (from `tools_catalog`).
- `POST /objectives` → create/update Value Objectives.
- `POST /employees` → create an employee (role label, hours, autonomy).
- `POST /plan/run?employee_id=` → `{ session_id, stream_url }` (AG‑UI SSE).
- `POST /approvals` → `{ action_ids[], decision, edits? }`.
- `POST /tasks/{id}/reassign` → `{ to_employee_id }`.
- `POST /employee/{id}/pause|resume`.
- `GET /activity?cursor=&employee_id?=`.

AG‑UI events (subset we implement):
`RUN_STARTED`, `RUN_FINISHED`, `TEXT_MESSAGE_*`, `TOOL_CALL_*`, `STATE_DELTA`, `APPROVAL_REQUIRED`, `APPROVAL_DECISION`, `ERROR`.

---

## 11) Data Model (RLS‑scoped, minimal)

**objectives**
`objective_id pk, tenant_id, name, metric_key, target_value, horizon_days, created_at`

**employees**
`employee_id pk, tenant_id, role, autonomy, schedule, status, created_at`

**program_assignments**
`employee_id, program_id, capacity_per_day, priority, enabled`

**tasks**
`id pk, tenant_id, employee_id, objective_id?, program_id?, title, status, proposed_at, approved_at, executed_at, seed_ref jsonb`
_(seed_ref may embed Evidence Cards/Signal refs)_

**actions**
`id pk, tenant_id, task_id, employee_id, type="mcp.exec", tool jsonb, args jsonb, risk, approval_state, result jsonb, external_id, created_at, completed_at`

**outbox**
`id pk, tenant_id, action_id, status(pending/sending/sent/failed/dead), retry_count, next_attempt_at, last_error`

**tools_catalog**
`tenant_id, composio_app, tool_key, category, json_schema, read_write_flags, risk_default, approval_default, write_allowed, rate_bucket, updated_at`
**pk** `(tenant_id, composio_app, tool_key)`

**tool_policies**
`tenant_id, composio_app, tool_key, risk, approval, write_allowed, rate_bucket`

**signals** _(optional; or embed in tasks)_
`id pk, tenant_id, kind, source_tool, features jsonb, examples jsonb, updated_at`

**contacts_lite** (if needed for calling)
`tenant_id, contact_id pk, vendor, vendor_contact_id, display_name, phone_e164[], email_hash[], tz, features jsonb, updated_at`

**call_jobs / call_outcomes** _(existing)_

**audit_log**
`id pk, tenant_id, who, what, when, details jsonb`

**trust_ledger**
`employee_id, day, approved_no_edit, edited, rejected, errors, complaints, score`
**pk** `(employee_id, day)`

Indexes: tenant_id across tables; outbox(status,next_attempt_at); actions(external_id); GIN on JSONB fields used by kernels.

---

## 12) Scheduling & Rate Limits

- **Warm Scan** (post‑connect): at most 1–2 **read** calls per category to seed Signals/Evidence.
- **Trickle Refresh** (every 30–60 min): top‑N deltas only; strictly respect **rate buckets** (`email.daily`, `slack.minute`, `tickets.api`).
- **On‑demand**: running a plan triggers narrow reads only for visible proposals.
- **Degradation**: if rate‑limited, proposals are delayed; UI shows “delayed by provider limits”.

---

## 13) Security & Compliance

- **Composio‑only**: all reads/writes via Composio MCP; no vendor tokens directly in our system.
- **Least‑privilege scopes**; **JIT upgrades** only with explicit user consent tied to a specific action.
- **Allowed Tools**: double‑gated (Composio + Broker); high‑risk categories **off** by default.
- **Backend‑only writes**; browser never sees secrets.
- **RLS** tenant isolation; encryption at rest.
- **Quiet hours & DNC**; opt‑out recorded instantly.
- **Audit**: approvals, policy edits, envelopes; PII minimization (hash emails, mask IDs in UI if configured).

---

## 14) Observability, SLAs, Runbooks

**Metrics**: connect→value time; tools connected; proposals/approved/edit rate; Outbox sent/failed/latency/retries; rate‑limit hits; Trust trend; objective leading indicators.

**SLAs**:

- Read/control availability 99.9%; Outbox 99.5%.
- Action completion p95 ≤ 5 min.
- Signal freshness ≤ 60 min (trickle), ≤ 10 min when triggers exist.

**Runbooks**:

- Outbox stuck → inspect rate bucket, widen jitter, requeue DLQ.
- Tool schema change → resync tools; schema‑forms re‑render automatically.
- Composio outage → degrade to read‑only; banner in UI; retry later.

---

## 15) Implementation Plan (least code)

**Sprint 1 — Universal MVP**

- Composio connect; discover tools → `tools_catalog`.
- Value Objectives wizard; seed 2–3 **Value Programs**.
- Reader Kernels (6) + JSONPath evaluator; **Warm Scan**; **Evidence Cards**.
- Desk + Approvals (schema‑forms) + Activity; **JIT Connect/Scope Upgrade** modals.
- **Outbox** executor (`mcp.exec`, idempotent; retries + DLQ); **AG‑UI** event stream.
- LiveKit calls; CRM note via Outbox.

**Sprint 2 — Proactivity & Multi‑employee**

- **Trickle Refresh**; **rate buckets**; optional **Composio triggers** ingestion.
- Trust gating; **Approve all low‑risk**; **Daily Summary**; **Weekly Value Review**.
- **Roster chips**; **Global Desk**; **Assignments drawer** (capacity per program).
- Add 2–3 more programs (Support backlog, Docs digest, Reply needed).

---

## 16) Acceptance Criteria

- Tools are discovered from Composio; schemas persisted; forms render correctly.
- Evidence Cards always show **endpoint + params + counts + 1–3 examples** (no bulk payloads).
- Approving an action that needs access shows **JIT Connect/Scope** and **executes exactly once** on success.
- Outbox idempotency (`external_id`) treats provider “conflict” as success; retries & DLQ work.
- RLS isolation proven; no cross‑tenant reads/writes.
- LiveKit calls: consent; DNC; CRM note via Outbox.

---

## 17) Risks & Mitigations

| Risk                             | Impact                | Mitigation                                                                    |
| -------------------------------- | --------------------- | ----------------------------------------------------------------------------- |
| Tool heterogeneity / odd schemas | Form/preview mismatch | Strict JSON Schema validation; raw‑JSON fallback; simulate mode               |
| No notifications                 | Stale awareness       | Warm Scan + Trickle Refresh; optional Composio triggers                       |
| Over‑permissioning fear          | Low connection rate   | Minimal scopes; JIT upgrades per action with explicit value; clear undo/pause |
| Approval fatigue                 | Throughput limits     | Small plans; “Approve all low‑risk”; Trust gates auto internal low‑risk       |
| Rate limits                      | Delays/failures       | Per‑tool buckets, backoff/jitter, carry‑over; user‑visible counters           |
| Draft quality variance           | Lower trust           | Capture edits → promptlet tuning; QA/Eval; Trust gates bound autonomy         |

---

## 18) Example Configs

**Reader kernel (per tool)**

```yaml
kernel: deadline_window
tool_key: hubspot.deals.list
args: { stage: "trial", limit: 50 }
select: "$.items[?(@.trial_end <= now()+7d)]"
features:
  due_count: "count($)"
examples: "$[:5]"
```

**Value Program**

```yaml
program: sales.trials7d
objective: increase_demos
signals: [deadline_window]
actions:
  - type: mcp.exec
    tool: gmail.messages.send
    args_template:
      to: "${contact.email}"
      subject: "Quick check-in before trial ends"
      body_html: "${templates.trial_nudge}"
    risk: medium
    approval: required
  - type: mcp.exec
    tool: hubspot.engagement.create
    args_template:
      contact_vendor_id: "${contact.vendor_id}"
      body_markdown: "${summaries.call}"
    risk: low
    approval: auto_when_trusted
```

---

### Why this version is the right ground base

- **Composio‑only & universal:** One integration powers _every_ tool; zero per‑tool code.
- **Value‑iterative & evidence‑first:** Plans align to outcomes; proposals carry proof; learning improves drafts and autonomy.
- **Light & robust:** One write, one executor, one UI stream; typed agents; minimal state; strict RLS.
- **Easy to adopt:** JIT Connect/Scope upgrades tied to concrete blocked actions; instant payoff after OAuth.
- **Scales calmly:** add employees, capacities, programs—no new surfaces or connectors.

If you want, I can deliver ready‑to‑use **Program** and **Kernel** starter files (YAML/JSON) and **promptlets** for email/ticket/docs so engineering can begin wiring Sprint‑1 immediately.
