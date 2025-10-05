Below is the **UX Specification (v1.0)** for the **AI Employee Platform** designed around a **single MCP source: Composio**.
It is universal (any Composio tool works), value‑iterative (outcomes → evidence → proposals), and lightweight (one action, one executor, one event stream). This UX spec is contract‑ready and maps 1:1 to the PRD & Architecture you approved.

---

# 0) Product UX Principles

1. **Value first, then tooling:** users declare outcomes; the UI shows how connecting Composio tools advances those outcomes—before asking for access.
2. **One rhythm:** _Plan → Approve → Execute → Summary_; every surface reinforces this rhythm.
3. **Explainable by default:** each proposal shows **Evidence** (counts & exemplars) and **Why now**.
4. **Minimal muscle memory:** five pages only; schema‑driven forms; one approval workflow.
5. **Consent by design:** least‑privilege scopes; explicit **JIT Connect/Scope Upgrade** tied to a specific action.
6. **Safe & recoverable:** approvals, undo, pause, audit, rate‑limit awareness, quiet hours/DNC, trust‑gated autonomy.
7. **Scales calmly:** one employee → many with a simple roster switcher and an assignments drawer.

---

# 1) Personas & Key Journeys

**Personas**

- **Operator/Owner (primary):** connects Composio, sets outcomes, approves actions daily.
- **Manager (secondary):** sets guardrails, reviews summaries, adjusts autonomy/trust.
- **Admin/Security (shadow):** reviews scopes, allowed tools, activity/audit.

**Core Journeys**

1. **First‑run to value:** declare outcome → connect Composio → see Plan with Evidence → approve a task → execution proof.
2. **Daily loop:** scan Plan, bulk‑approve low‑risk, edit 1–2 items, observe execution; pause/undo if needed.
3. **Expand capability:** approve a proposal that needs a missing tool/scope → JIT Connect/Upgrade → action runs automatically.
4. **Grow team:** add a second employee, drag‑reassign a few cards, set routine capacities.

---

# 2) Information Architecture

Top‑level nav (persistent):

- **Desk** ▾ (Global | Employee A | Employee B …)
- **Approvals**
- **Activity & Safety**
- **Integrations** (Composio)
- **Hire / Roster**

Global header elements:

- **Objective selector** (shows current Value Objective + KPI chip)
- **Trust chip** (per selected employee)
- **Pause/Resume** button (employee/global contextual)
- **Help** (policies, how scopes work, what we store)

---

# 3) Global Patterns & UI System

- **AG‑UI sidecar** on the right (narration, tool calls, errors, approvals).
- **Schema‑driven forms** for action preview & edit (generated from Composio tool JSON Schemas).
- **Risk badges:** Low (green), Medium (amber), High (red, locked).
- **Approval chips:** Auto / Needs approval / Blocked (writes disabled).
- **Evidence chips:** show counts; “3 exemplars”; “last refreshed 14m ago”.
- **Undo/Cancel** on queued actions until “sending”.
- **Rate‑limit badges** when throttling (e.g., Gmail daily limit).

---

# 4) Page‑Level Specifications

## 4.1 Value Canvas (first‑run modal)

**Goal:** map user outcomes → leading metrics → eligible proposals.

**Form fields (stepper, 2–3 min):**

- **Objective template** (Sales demos / CS response / Support backlog / Docs self‑serve / Custom)
- **Target & horizon** (e.g., “+20% in 30 days”)
- **Guardrails** (quiet hours, tone, allowed channels)
- **Autonomy default** (Observe/Propose/Assist/Trusted — defaults to Propose)

**Post‑submit:** show a confirmation banner: “We’ll propose today’s plan aligned to _Increase demos_ and explain every step with evidence.”

---

## 4.2 Integrations (Composio)

**Goal:** connect once; discover many tools; motivate with concrete value; keep risk crystal clear.

**Sections**

1. **Composio Connect Card**
   - CTA: **Connect Composio**
   - Once connected: connection health, last sync time; link to Composio dashboard

2. **Unlocked Apps Grid**
   - App card (logo, name, category; connection badge)
   - **Allowed Writes** toggle (off by default for high‑risk categories)
   - **Risk chip** and **scope summary** (e.g., “send‑only email”)
   - **Issues** surface (expired token, missing scope)

3. **Gap Map (value‑driven prompts)**
   - “To place holds for interested replies: enable **Calendar events.insert**” → **Enable & Run Now**
   - “To log CRM notes after calls: enable **HubSpot engagements.write**”

**JIT Connect/Scope Upgrade Modal**

- **Header:** “Enable _gmail.messages.send_ (send‑only)?”
- **Body:**
  - “This enables the approved action: **Send 4 emails to trials ending this week**”
  - “Value now: saves ~18 minutes; progresses ‘Increase demos’”
  - Scopes list (minimal; each with a plain‑English description)
  - Safety affirmations: “Undo available before send; quiet hours enforced.”

- **CTA:** **Enable & Run Action** (on success, returns to Desk with that action marked “sent”)

**Empty state copy**

- “Connect Composio to discover apps already in your stack and unlock ready‑to‑run tasks aligned to your objective.”

---

## 4.3 Desk (Global & Individual)

**Goal:** approve 5–15 items in <3 minutes; see why; act with confidence.

**Layout**

- **Toolbar:** Objective chip, Date selector (Today/This week), Filters (App, Risk), **Approve all low‑risk**
- **Plan Cards** (grouped by employee in Global view)
  - Icon (app) + Title (task)
  - **Why now**: Evidence snippet (count, max age, 2–3 IDs) + “last refreshed”
  - **Risk/Approval** badges
  - **Approve / Edit / Skip**
  - Expand → Action Preview (schema form + content preview)

- **AG‑UI Sidecar** (right)
  - Streams narration (`TEXT_MESSAGE_*`), tool reads/writes, state counters, errors

**Interactions**

- **Approve** → card animates “Queued → Sent”; sidecar shows `TOOL_CALL_*`.
- **Edit** → opens schema‑form modal with live validation.
- **Approve all low‑risk** → confirmation (“5 tasks from Slack/Notion/HubSpot will execute”).

**Empty state (individual)**

- “No proposals right now. We refresh every 30–60 minutes or when you connect more apps.”

**Global Desk**

- Collapsible groups per employee; **drag‑to‑reassign** card to another employee (snackbar confirm).

---

## 4.4 Approvals (shared inbox)

**Goal:** approve many with clarity; edit only what matters.

**Features**

- Group by app and employee; select rows; **Approve selected / Reject selected**
- **Schema‑driven modals** for edit/preview per action
- **Diff view** for high‑impact changes (e.g., CRM stage update)
- Filters: Employee, App, Risk, Created time, Routine/Program

**Microcopy**

- “Edits here apply to this action only. We learn from your edits to improve future drafts.”

---

## 4.5 Activity & Safety

**Goal:** visibility & control after approval.

**Sections**

- **Action Timeline** — status chips (Sent / Skipped / Failed / Conflict‐deduped); link to provider resource if safe
- **Outbox Health** — counts, retry curve, DLQ list with **Requeue**; rate‑limit badges
- **Controls** — **Pause Employee/All**, **Undo queued** (per action)
- **Calls** — recent calls, transcript preview, **Add to DNC** (confirm)
- **Rate‑limit Monitor** — per bucket (e.g., `email.daily`)

**Copy**

- “_Conflict_ means the provider reported this already exists; we treat it as success to avoid duplicates.”

---

## 4.6 Hire / Roster & Assignments Drawer

**Hire (first employee)**

- Role label (Sales Assistant / CS Assistant / Support / Generalist)
- Hours / timezone (defaults)
- Autonomy default (Propose)

**Roster**

- Cards with name/role/autonomy/trust score/output summary; actions: Open Desk / Pause / Edit / Clone
- Header chips: **All | A | B | +**

**Assignments Drawer** (right sheet)

- Value Programs list (e.g., Trials 7d, Backlog 24h, Replies Needed)
- Per‑employee **capacity/day** sliders + **priority** (High/Normal/Low)
- “Estimated time load today” for transparency
- **Save** applies routing immediately

---

# 5) Sidecar (AG‑UI) — event → UI mapping

| Event                          | UI                                                    |          |                                                     |
| ------------------------------ | ----------------------------------------------------- | -------- | --------------------------------------------------- |
| `RUN_STARTED / RUN_FINISHED`   | Banner with timestamp                                 |          |                                                     |
| `TEXT_MESSAGE_*`               | Streaming narration bubbles (typing effect)           |          |                                                     |
| `TOOL_CALL_START / END`        | Inline “Reading HubSpot deals…” ✓ with elapsed time   |          |                                                     |
| `TOOL_CALL_ARGS`               | Collapsible JSON snippet (dev/debug)                  |          |                                                     |
| `STATE_DELTA`                  | Counters: low/med/high proposals; approvals remaining |          |                                                     |
| `APPROVAL_REQUIRED / DECISION` | Sticky pill linking to that approval                  |          |                                                     |
| `ERROR {retryable              | terminal                                              | policy}` | Red banner with the action link & recovery guidance |

Sidecar quick actions: **Pause**, **Approve all low‑risk**, **Explain this plan**.

---

# 6) Evidence Cards & Gap Map (value‑led conversion)

**Evidence Card (render)**

- **Title:** “9 trials ≤7d (HubSpot.deals.list)”
- **Body:** “Examples: D‑309, D‑322, D‑341 · Oldest: 6d · Last refreshed: 12m ago”
- **Footer:** “Improves: _Increase demos_ (leading: outreach to expiring trials)”

**Gap Map banner**

- “To place holds after replies: enable **Calendar events.insert** (minimal scope).”
- “To log notes after calls: enable **HubSpot engagements.write** (minimal).”
- CTA: **Enable & Run Now** (JIT connect/upgrade → executes the pending approved action).

---

# 7) Action Preview (Schema → Form mapping)

**Supported schema primitives**

- `string` (with `format: email|uri|date-time` → typed inputs)
- `number|integer` (min/max)
- `boolean` (switch)
- `enum` (select; searchable if >5)
- `array` (chip list or rows)
- `object` (collapsible section)
- `oneOf|anyOf` (segmented control)
- `default|examples` prefill; `required` → disable Approve until valid

**Validation UX**

- Inline error text; submit summary; disable **Approve** until form valid
- Live preview for content types (email body, Slack text, Notion page)

---

# 8) Autonomy, Trust & Risk UI

- **Trust Chip** in header: “Trust 0.72 · Assist” with trend arrow
- Tooltips: “Rises with approvals w/out edits; falls with rejections/errors.”

**Default gates (per employee)**

- `<0.6` **Propose** — all approvals required
- `0.6–0.8` **Assist** — auto for internal low‑risk
- `>0.8` **Trusted** — auto for low & pre‑approved medium; never high

**Risk labels**

- Low (green, “Auto when Trusted”)
- Medium (amber, “Needs approval”)
- High (red lock, “Writes disabled by default”)

---

# 9) Notifications & Toasters

**Toasts**

- Success: “Sent 4/4 tasks to Slack/Notion/HubSpot.”
- Rate‑limit: “Gmail send limit 75% used; slowing down.”
- Error: “Zendesk 429; retry in ~2m.”

**In‑app banners**

- Token expired: “Reconnect Gmail send‑only to continue.”
- Safety: “Writes disabled for ['finance','public social']; enable in Integrations.”

---

# 10) Accessibility (WCAG 2.1 AA)

- Keyboard:
  - Desk: ↑/↓ to select card; **Enter** approve; **E** edit; **S** skip; **A** approve all low‑risk
  - Approvals: arrows navigate; **Enter** approve; **R** reject
  - Global: `[` and `]` cycle employees

- Focus traps in modals; ARIA roles (`list`, `listitem`, `status` live region)
- Contrast ≥ 4.5:1; icons + text for risk (no color‑only).
- Reduced motion respected.

---

# 11) States & Edge Cases

**Loading/skeletons**

- Desk cards placeholder with shimmer; sidecar prints “Preparing plan…”

**Empty**

- “No proposals yet. We refresh every 30–60 min or when you connect more apps.”

**Errors**

- **Schema mismatch:** fallback to raw JSON editor + “Simulate” preview; recommendations to resync tool schema.
- **Rate‑limited:** card badge “Delayed by provider limit”; tooltip with next attempt time.
- **Conflict (idempotency):** timeline shows “Already exists” and counts as success.
- **Quiet hours/DNC:** sending disabled; card offers “Schedule at 8:00”.

---

# 12) Component Library & Design Tokens

**Core components**

- PlanCard / ApprovalRow / ActionPreviewModal / SidecarStream
- IntegrationCard / JITConnectModal / GapMapBanner
- ActivityTimeline / OutboxPanel / RateLimitBadge
- RosterChip / AssignmentsDrawer / TrustChip
- Toast / Banner / ConfirmationDialog

**Tokens**

- Spacing: 4 / 8 / 12 / 16 / 24 / 32
- Radius: 6 / 10
- Shadows: `elev-1`, `elev-2`
- Typography: Inter 14/16/20 (400/600)
- Colors:
  - Brand `brand/500`
  - Risk: `low` (green‑600), `med` (amber‑600), `high` (red‑600)
  - Status: `ok` (green‑500), `warn` (amber‑500), `error` (red‑500), `info` (blue‑500)

---

# 13) Analytics & Success Metrics

**Events**

- `onboarding.objective_set` {objective, target, horizon}
- `integrations.composio_connected` {apps_discovered}
- `gapmap.jit_connect_opened` {tool_key, scopes}
- `gapmap.jit_connect_success` {tool_key, scopes, action_unblocked:true}
- `desk.plan_shown` {cards_total, low, med, high}
- `desk.approve_all_low_risk_clicked` {count}
- `approval.item_approved` {tool_key, edits_made, risk}
- `outbox.action_sent` {tool_key, latency_ms, retries}
- `outbox.action_failed` {tool_key, error_category}
- `employee.paused/resumed`
- `trust.score_updated` {employee_id, score, delta}

**Dashboards**

- Connect→Value (median), approvals rate, edit rate, failure rate, retries, trust trend, backlog, rate‑limit hits, objective leading metric trend.

---

# 14) Acceptance Criteria (per page)

**Integrations (Composio)**

- [ ] Connect flow completes; tools appear with schemas.
- [ ] Allowed Writes toggles persist; high‑risk tools default off.
- [ ] JIT Connect/Scope runs; upon success, the original approved action executes exactly once.

**Desk**

- [ ] Plan renders 5–15 items with Evidence; “Approve all low‑risk” works.
- [ ] Sidecar streams AG‑UI events coherently.
- [ ] Drag‑to‑reassign works in Global Desk.

**Approvals**

- [ ] Schema forms validate; required fields enforced.
- [ ] Diff view renders for high‑impact mutations (if applicable).

**Activity & Safety**

- [ ] Outbox counts, Retry/DLQ, Requeue; rate‑limit badges display; Undo queued works.

**Hire / Roster**

- [ ] Hire wizard sets role/hours/autonomy; roster chips toggle Desks.
- [ ] Assignments Drawer updates capacity/day per program & employee.

**A11y**

- [ ] Keyboard shortcuts; focus order; ARIA live regions; contrast; reduced motion.

---

# 15) Example Wireframes (ASCII, condensed)

**Desk (Global)**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Desk ▾ (All | A | B | +)   Objective: Increase demos   [Approve low-risk]  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Employee A                                                              ^   │
│ ┌─[HubSpot] Draft 4 emails to expiring trials     Low • Needs approval  │   │
│ │ Why: 9 trials ≤7d (D-309, D-322, D-341) • Refreshed 12m               │   │
│ │ [Approve] [Edit] [Skip]                                               │   │
│ └────────────────────────────────────────────────────────────────────────┘   │
│ ┌─[Notion] Create page “Top Qs this week”      Low • Auto when Trusted      │
│ │ Why: 12 tickets >24h; tags: billing, login                               │
│ │ [Approve] [Edit] [Skip]                                                   │
│ └───────────────────────────────────────────────────────────────────────────│
│ Employee B                                                                  │
│ ┌─[Slack] Post CS digest 5pm daily         Low • Requires first approval    │
│ │ Why: 12 tickets older than 24h; oldest 56h                                │
│ │ [Approve] [Edit] [Skip]                                                    │
│ └───────────────────────────────────────────────────────────────────────────│
│                                   │ Sidecar (Live)                          │
│                                   │ ▸ RUN_STARTED                           │
│                                   │ Reading HubSpot… ✓ 320ms                │
│                                   │ Proposing 2 emails, 1 doc               │
│                                   │ ▸ APPROVAL_REQUIRED (3)                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Integrations (Composio)**

```
┌─────────────────────────── Integrations ───────────────────────────┐
│ [ Connect Composio ]                                               │
│ Connected: yes • Last sync: 5m                                     │
│                                                                     │
│ Unlocked Apps                                                       │
│ [Gmail]  send-only  [Writes: ON]  Risk: Medium   Status: Healthy    │
│ [Slack]  chat.write [Writes: ON]  Risk: Low      Status: Healthy    │
│ [HubSpot] engagements.write [Writes: OFF] Risk: Med Status: Missing │
│                                                                     │
│ Gap Map                                                             │
│ Enable Calendar events.insert to auto place holds after replies.    │
│ [Enable & Run Now]                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

# 16) Content & Microcopy Standards

- Tone: **clear, practical, respectful** of user control; avoid “magic.”
- Always lead with **why** (evidence) and **what** (exact action).
- JIT Connect/Scope: spell out minimal scope, the immediate action it enables, and guarantees (undo, quiet hours).

**Examples**

- “Draft email to Jane Doe (trial ends Wed). Why: part of 9 trials expiring in 7 days.”
- “Writes disabled for ‘Public Social’. Enable in Integrations to allow posting.”
- “Undo is available until sending; we respect quiet hours (8am–8pm local).”

---

# 17) Future Hooks (no new pages required)

- **Daily summary** modal: outcomes moved, wins, proposed tweaks.
- **Weekly value review**: KPI movement, template A/B suggestions, staffing hint (capacity changes).
- **Team switcher** next to Trust chip if many employees become the norm.

---

## Summary

This UX keeps **humans in control** and **value at the center**:

- Five familiar pages, one daily rhythm.
- Proposals are **evidence‑backed** and **schema‑validated**.
- Composio is the only integration surface; **JIT Connect** ties access to concrete payoff.
- The system stays light: one universal action, one executor, one event stream.
- Scaling to multiple employees is **native and minimal**: a roster chip and a small assignments drawer.

If you want, I can deliver a **copy deck**, **component spec sheets**, and **JSON Schema examples** for 6 common Composio tools (Gmail, Slack, Notion, HubSpot, Zendesk, Calendar) so design & engineering can start building immediately.
