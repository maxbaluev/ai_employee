# Product Requirements Document — AI Employee Platform (Final)

## 1. Vision & Summary

Deliver a controllable, Composio-only AI teammate that plans, explains, and executes work across tenant SaaS tools with minimal custom engineering. The product bundles CopilotKit UI, Google ADK agents, and Composio’s tool ecosystem into a production workflow that operators can trust.

## 2. Problem Statement

Operators manage large queues across disparate tools, lack consolidated evidence, and waste time on repetitive drafting. Existing automations require per-app integrations and risky background execution. We need a unified system that:
- surfaces opportunities using real data,
- requests human approval with transparent evidence,
- executes safely with auditability,
- scales to multiple AI employees without extra connectors.

## 3. Goals & Objectives

1. **Fast value:** First approved action within five minutes of connecting Composio.
2. **Explainability:** 100% of proposals cite evidence (tool slug + exemplars) before requesting approval.
3. **Human oversight:** Zero unapproved writes until trust > threshold; undo/pause always available.
4. **Operational trust:** Outbox SLA p95 ≤ 5 minutes; audit log covers approvals, scopes, executions.
5. **Low-code scaling:** Add new toolkits or objectives without bespoke code—reuse Composio schemas and ADK prompts.

## 4. Scope (v1)

- 5 core surfaces: Desk, Approvals, Activity & Safety, Integrations, Hire/Roster.
- Read path: Warm Scan + Trickle Refresh via Composio read tools (no vendor-specific code).
- Write path: Action envelopes executed through single Outbox worker with Composio `tools.execute`.
- Trust scoring + autonomy gates (Propose → Assist → Trusted).
- LiveKit hand-off for call-based tasks (existing worker integration).

## 5. Non-Goals

- Support for non-Composio connectors or BYO API keys.
- Automated financial/destructive actions without explicit enablement.
- Offline document ingestion, custom ETL.
- Heavy analytics dashboards (beyond metrics defined in `docs/observability.md`).

## 6. Personas

| Persona | Needs |
| ------- | ----- |
| Operator | Approve/edit actions quickly, ensure safety |
| Manager | Configure objectives, guardrails, staffing |
| Security/Admin | Review scopes, audit trails, incident response |

## 7. Success Metrics

| Metric | Target |
| ------ | ------ |
| Connect → first approved action | ≤ 5 minutes |
| Approved actions without edits (week 2) | ≥ 70% |
| Tenants connecting ≥2 apps in first session | ≥ 65% |
| Outbox completion p95 | ≤ 5 minutes |
| Incident MTTR (Outbox/Composio failures) | < 30 minutes |
| Audit completeness (events logged) | 100% critical actions |

## 8. Key Requirements (see `docs/requirements.md` for detail)

- Objective/guardrail onboarding, schema-driven approvals, Outbox with idempotency, trust gates, audit events, rate-limit awareness, quiet hours, undo/pause.

## 9. Constraints & Assumptions

- Composio remains available; outages degrade to read-only (tracked in Observability doc).
- Supabase/Postgres provides RLS; we manage migrations.
- Tenants supply Composio OAuth credentials; secrets stored outside repo.
- UI and agent run within same deployment but can scale separately.

## 10. Risks & Mitigations

| Risk | Mitigation |
| ---- | ---------- |
| Composio schema drift | Daily catalog sync, fallback to raw JSON editor, monitor validations |
| Trust miscalibration | Start conservative; require manual override to increase autonomy |
| Approval fatigue | Evidence-first cards, bulk low-risk approval, trust gating |
| Quiet hour breaches | Validate both at planner and Outbox; log overrides |
| LiveKit integration drift | Establish contract tests with worker team |

## 11. Deliverables

- Production-ready `/docs` folder (this doc set).
- Implemented control plane + Outbox per `docs/arch.md` roadmap.
- UI surfaces tied to UX spec (`docs/ux.md`).
- Observability instrumentation with dashboards & alerts.
- Runbooks for key incidents (Composio outage, Outbox DLQ).

## 12. References

- `docs/arch.md` (architecture)
- `docs/ux.md` (UX contract)
- `docs/requirements.md` (functional)
- `docs/nfr.md` (non-functional)
- `docs/threat-model.md` (security)
- `docs/observability.md` (metrics/alerts)
- `docs/roadmap.md` (delivery plan)
