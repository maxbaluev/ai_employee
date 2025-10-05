# AI Employee Platform — UX Spec v1.1

> Ground-truth UX contract aligned with CopilotKit + AGUI capabilities and the architecture in `docs/arch.md`. Designed for speed (minimal custom UI) while keeping operators in control.

---

## 1. Principles

1. **Outcome-first**: Objectives and evidence are always visible; no task without “why”.
2. **Explainable actions**: Every proposal shows tool, scopes, parameters, and evidence link.
3. **Single rhythm**: Plan → Approve → Execute → Review; all surfaces reinforce this.
4. **Default to human review**: Auto execution only after trust proves safe.
5. **Leverage schemas**: Reuse Composio JSON Schema to render/edit approvals—no bespoke forms.
6. **Recoverable**: Undo, pause, and audit breadcrumbs built-in; operators can always intervene.
7. **Minimal UI code**: Prefer CopilotKit hooks/sidecar, generic table/card components, and server-driven config.

---

## 2. Personas & Journeys

| Persona | Goals | Core Journeys |
| ------- | ----- | ------------- |
| Operator | Approve/monitor tasks | First-run to value, daily plan review, handle JIT scopes |
| Manager | Configure guardrails, staffing | Adjust objectives/autonomy, manage roster |
| Security/Admin | Oversight & compliance | Review audit logs, scope changes, incidents |

**Journeys**
1. First-run wizard → Composio connect → Warm Scan → Approve first action (with evidence).
2. Daily Desk review → Approve/edit/skip (bulk low-risk, drag to reassign) → Track execution.
3. Approve action that needs scope → JIT modal → Auto-execution → Audit confirmation.
4. Add second employee → Set program capacity → Observe trust scores.

---

## 3. Navigation & Layout

```
[ Desk ▾ ] [ Approvals ] [ Activity & Safety ] [ Integrations ] [ Hire / Roster ]
 Header: Objective selector | Trust chip | Pause button | Help
 Right side: CopilotKit Sidecar (AGUI stream + quick actions)
```

- Keep nav fixed across pages. Use shared layout components.
- CopilotKit Sidecar shows streaming narration, tool calls, errors; offers quick actions (`Pause`, `Approve all low-risk`, `Explain plan`).

---

## 4. Page Specifications

### 4.1 Value Onboarding (modal sequence)
- **Step 1:** Pick template objective or custom (name, KPI, target delta, horizon).
- **Step 2:** Configure guardrails (quiet hours, permitted channels, tone defaults).
- **Step 3:** Select autonomy baseline (Observe/Propose/Assist/Trusted). Default: Propose.
- **Result:** Confirmation with expectation (“Warm Scan will surface X within ~2 minutes”).

### 4.2 Integrations
- **Connect card:** OAuth button (`composio.connected_accounts.initiate`), status, last sync, instructions.
- **Tool grid:** For each Composio tool (from catalog): app icon, slug, description, scopes summary, risk badge, write toggle, status (Connected / Missing scope / Disabled / Error).
- **Gap map banners:** Suggest enabling tools when blocked actions exist (pull from Outbox/pending approvals).
- **JIT scope modal:** Shows pending action details, required scopes (plain language via `toolkits.get_connected_account_initiation_fields`), value unlocked, undo promise.

### 4.3 Desk (Global & per employee)
- **Toolbar:** Objective chip, timeframe selector (Today/Week), filters (Risk, App, Program), `Approve all low-risk` button (enabled when safe).
- **Plan cards:** Card Title (action), risk/approval badges, evidence snippet (count, exemplars, last refresh), buttons (Approve/Edit/Skip). Expand shows schema form + preview (e.g., email body).
- **Global view:** Cards grouped by employee; drag-and-drop to reassign (updates backend, triggers StateDelta to other clients).
- **Empty state:** “No proposals yet. Warm Scan runs after connections; Trickle Refresh every 30–60 minutes.”

### 4.4 Approvals Inbox
- Table view leveraging generic data grid.
- Columns: Action, Employee, Tool, Risk, Status, Last updated, Evidence icon.
- Bulk select with Approve / Reject / Export.
- Edit opens same schema-driven form; highlight diffs for high-impact fields.
- Filters: Program, Risk, App, Employee, Created range, Scope needed.

### 4.5 Activity & Safety
- **Timeline:** Chronological Outbox events; show provider link/ID, status (Sent, Failed, Conflict), message or error.
- **Outbox health:** Queue depth, retry counts, DLQ list (with Requeue, Mark Reviewed buttons).
- **Rate limits:** Gauges per bucket (Gmail daily, Slack minute, etc.) with predicted reset.
- **Controls:** Pause All, Pause employee, Undo queued (allowed until `status=sending`).
- **Calls:** Show LiveKit tasks (call title, outcome, DNC toggle).

### 4.6 Hire / Roster
- **Hire wizard:** Name/role, timezone, hours, autonomy default, guardrail overrides.
- **Roster board:** Cards with trust chip, throughput metrics, status (Active/Paused). Quick actions: Open Desk, Pause, Edit, Clone.
- **Assignments drawer:** Program list with capacity sliders and priority toggles per employee; display estimated workload.

---

## 5. Sidecar Event Mapping

| AGUI Event | UI Response |
| ---------- | ----------- |
| `RunStartedEvent` / `RunFinishedEvent` | Banner with timestamp + duration |
| `TextMessage*` | Streaming narration bubbles (typing effect) |
| `ToolCallStartEvent` | Inline pill “Calling <tool slug>” with spinner |
| `ToolCallArgsEvent` | Expandable JSON showing arguments (link to Edit) |
| `ToolCallResultEvent` | Celebrate success or display error toast, update timeline |
| `StateDeltaEvent` / `StateSnapshotEvent` | Merge into shared state (`useCoAgent`) |
| `RunErrorEvent` | Sticky red banner; offer retry or open Activity |

Quick actions in sidecar: `Pause`, `Approve all low-risk`, `Explain plan`, `Download run transcript` (for support/audit).

---

## 6. Evidence & Approvals Contracts

- Evidence card format: “**{count} {context}** ({tool slug}) – examples: … – refreshed {relative time}. Supports objective *{name}*.”
- `Edit` modal always shows tool slug, scopes required, and connected account used.
- Conflict (Composio 409) displayed as success with “Already existed” note. Provide `Mark reviewed` to clear banner.
- Quiet-hour blocks show schedule badge with resume time + override option (requires reason).

---

## 7. Trust & Autonomy

- Trust chip (header + roster) displays numeric score (0–1), status (Propose/Assist/Trusted), trend arrow.
- Auto decisions: highlight with green halo and tooltip “Auto-approved (Trusted > 0.8).” Allow manual review.
- Rejections/edits feed trust ledger; show weekly summary email (future).

---

## 8. Notifications & Feedback

- Toasts: success (“Sent 3 Gmail drafts”), rate-limit warning, error (with retry countdown), DLQ arrival.
- Banners: Composio auth expired, quiet hours active, writes disabled (category), Outbox paused.
- Optional email/slack digest (future) for daily summary + unresolved approvals.

---

## 9. Accessibility & Shortcuts

- Desk: `↑/↓` select card, `Enter` approve, `E` edit, `S` skip, `A` approve all low-risk.
- Approvals table: arrow navigation, `Enter` approve, `Shift+Enter` reject, `Cmd/Ctrl+F` focus filters.
- Global nav: `[` / `]` cycle employees, `Ctrl+P` toggle pause, `Ctrl+/` open quick command palette.
- Full keyboard support, focus trapping in modals, ARIA live regions for sidecar, color paired with icons (WCAG 2.1 AA).

---

## 10. Analytics & Success Metrics (UI hooks)

Emit events per `docs/observability.md` + `docs/requirements.md`:
- `onboarding.objective_set`, `integrations.tool_enabled`, `desk.plan_shown`, `desk.approve_action`, `approvals.bulk_decision`, `outbox.action_failed`, `trust.score_updated`.
- Ensure payloads include `tenant_id` (hashed), `employee_id`, `tool_slug`, `risk`, `autonomy_state`.

---

## 11. Acceptance Checklist

- [ ] CopilotKit sidecar displays AGUI stream in real time (all event types above).
- [ ] Schema-driven edit forms render for every Composio tool without custom UI.
- [ ] JIT scope modal replays pending action exactly once after approval.
- [ ] Activity & Safety exposes Outbox queue, retries, DLQ with requeue.
- [ ] Keyboard shortcuts validated; accessible names and live regions verified.
- [ ] Analytics events captured with tenant context.

Deliver this UX as the single source of truth—the dev team should not invent additional flows without updating this spec.
