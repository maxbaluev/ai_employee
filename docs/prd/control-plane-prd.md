# Control Plane Product Requirements

**Status:** Drafted October 6, 2025 · Aligns with Phase 4/5 implementation snapshot

## 1. Purpose & Vision

Give customer operators a single workspace to monitor, approve, and guide the AI
employee’s actions safely. The product must surface actionable signals (queue status,
approvals, guardrails) without leaving Supabase or the embedded control plane UI.

## 2. Target Users

- **Operations Lead** – monitors queue health, resolves DLQ incidents, coordinates human
  approvals.
- **Customer Success Manager** – reviews proposals, adds evidence, approves or rejects
  envelopes.
- **Platform Engineer** – maintains Supabase data, runs diagnostics, performs DLQ replays.

## 3. Goals & Success Metrics

| Goal | Metric | Definition |
|------|--------|------------|
| Keep queue flowing | `pending` envelopes resolved within SLA | 90% cleared in < 10 minutes (during business hours) |
| Reduce human toil | Average approvals per agent run | Aim for <1 per hour via guardrails + scopes |
| Speed incident response | DLQ replay MTTR | < 15 minutes using worker CLI + dashboard |

## 4. Functional Requirements

1. **Workspace Shell**
   - `/` overview summarising queue, approvals, guardrail blocks.
   - `/desk` rendering shared-state queue with status toggles.
   - `/approvals` rendering schema-driven forms from `tool_catalog.schema`.

2. **Analytics API**
   - `GET /analytics/outbox/status?tenant=<id>` → pending/success counts + DLQ size.
   - `GET /analytics/guardrails/recent?tenant=<id>&limit=<n>` → latest guardrail events.
   - `GET /analytics/cron/jobs?limit=<n>` → recent Supabase Cron job runs.

3. **Supabase Dashboards**
   - Saved SQL snippets for outbox status, DLQ backlog, guardrail audit trails, cron
     job health (documented in `docs/operations/run-and-observe.md`).

4. **Worker Tooling**
   - CLI actions (`status`, `drain`, `retry-dlq`, `start`) documented in the runbook.
   - Respect `next_run_at` for scheduled retries.

5. **Approvals & Guardrails**
   - Shared state slices emit JSON Patch deltas whenever desk/approvals/guardrails
     mutate so the UI mirrors the agent in real time.
   - Guardrail failures audit-logged with reason and guardrail name.

## 5. Non-Functional Requirements

- **Security** – No external observability stack; all analytics remain inside Supabase.
- **Reliability** – Worker retries up to `outbox_max_attempts`; DLQ keeps historical
  failures for replay.
- **Performance** – Desk/approvals pages render within 200 ms using shared state and
  minimal hydration.

## 6. Open Questions

- When will integrations/connected-account UI ship (Phase 6 dependency)?
- Should analytics endpoints support pagination / caching for very large tenants?
- Do we require alerting hooks beyond Supabase Cron (e.g. direct Slack webhooks)?

## 7. Next Increment

- Integrate analytics endpoints into the admin workspace (charts/cards).
- Automate Supabase migrations in CI/CD to enforce schema guardrails.
- Add automated DLQ replay playbooks (button in UI calling worker CLI).
