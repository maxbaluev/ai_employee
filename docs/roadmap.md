# Roadmap — AI Employee Platform

Timeline assumes two-week sprints. Dates are placeholders; update during planning.

## Sprint 0 — Foundations

- Finalize Composio contract & scope inventory.
- Implement environment setup automation (Make targets, codex.yml).
- Replace demo tools in ADK agent with Composio FunctionTools (see `docs/todo.md` §1).
- Establish telemetry scaffolding (logging format, OpenTelemetry exporter stub).

## Sprint 1 — Universal MVP

- Tool catalog persistence with risk/rate metadata.
- Warm Scan readers + Evidence Cards on Desk.
- Schema-driven Approvals with JIT scope upgrade flow.
- Outbox worker delivering Gmail/Slack/HubSpot envelopes with idempotency.
- Audit log and Activity & Safety surface for Outbox visibility.

## Sprint 2 — Proactivity & Trust

- Trickle Refresh scheduler with rate bucket enforcement.
- Trust score computation & autonomy gates (auto low-risk when Trusted).
- Bulk Approve low-risk + drag-and-drop Global Desk.
- Integrate LiveKit call completions into Activity timeline.

## Sprint 3 — Hardening & Scale

- Observability dashboards (metrics + traces) per `docs/observability.md`.
- Security posture: threat model validation, penetration test prep, quiet hours/DNC enforcement.
- Localization prep (extract copy, enable translation pipeline).
- Runbooks for Composio outage, Outbox DLQ, trust score anomalies.

## Backlog / Open Questions

- Should we add codex-guided self-healing for failed planner runs?
- Evaluate automated kernel verification against Composio schema changes.
- Investigate multi-tenant analytics exports (requires cross-tenant safeguards).
