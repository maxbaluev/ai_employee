# Roadmap (Final)

Two-week sprint cadence. Update dates during planning.

## Sprint 0 — Foundations
- Finalize Composio contract + toolkit list.
- Replace demo tools with Composio FunctionTools (docs/todo §1).
- Stand up tool catalog + connected account endpoints.
- Decide metrics backend, commit to OTLP/Prometheus path.
- Produce `codex.yml`, Makefile, `.env.example` updates.

## Sprint 1 — Universal MVP
- Implement Supabase schema + RLS for tenants, objectives, tasks, actions, audit.
- Build Warm Scan + Evidence pipeline (kernels, APScheduler).
- Deliver Desk & Approvals UI with schema-driven forms.
- Ship Outbox worker (basic retries, quiet hours, idempotency).
- Integrations page with JIT scope modal + tool toggles.

## Sprint 2 — Proactivity & Trust
- Trickle Refresh scheduler with rate bucket budgets.
- Trust ledger + auto-approval for low-risk actions; expose trust chip.
- Global Desk drag-and-drop reassignment; Approve-all low-risk.
- Activity & Safety page with timeline, DLQ controls, rate-limit gauges.
- LiveKit worker integration into Activity timeline.

## Sprint 3 — Hardening & Ops
- Observability dashboards + alerts per `docs/observability.md`.
- Runbooks for Composio outage, Outbox DLQ, trust anomalies.
- Logging hygiene + privacy audits (hash verification, retention checks).
- Localization prep (extract strings, translation pipeline stub).
- Penetration test + update threat model.

## Backlog / Future
- Composio trigger ingestion for push updates.
- Multi-agent orchestration (compliance reviewer) using CopilotRuntime service adapters.
- Tenant-level analytics exports (adopted tools, trust trend) with privacy guardrails.
- Self-healing planner diagnostics (auto reruns, diff reports).
