# Product Vision Snapshot (Universal)

See the canonical PRD: `docs/prd/universal-ai-employee-prd.md`.

## Vision

Deliver a controllable, Composio-only AI teammate that plans, explains, and executes
tasks across tenant SaaS tools with minimal custom engineering. Operators must understand
every recommendation, approve with confidence, and roll back when needed.

## Primary Pain Points Solved

1. Fragmented tooling and evidence across SaaS apps.
2. Manual drafting and repetitive follow-up work.
3. Risky automations that operate without human oversight.

## Success Metrics (from PRD v3.0)

| Metric | Target |
|--------|--------|
| Connect → first approved action | ≤ 60 seconds |
| Approved actions without edits (week 2) | ≥ 70% |
| Tenants connecting ≥ 2 apps in first session | ≥ 65% |
| Outbox completion p95 | ≤ 5 minutes |
| Incident MTTR (Composio/Outbox failures) | < 30 minutes |

## Core Surfaces

- **Desk** – operator queue with evidence-first cards.
- **Approvals** – schema-driven edit + approve/reject flows.
- **Activity & Safety** – audit log, DLQ, guardrail toggles.
- **Integrations** – connected account lifecycle and catalog visibility.
- **Hire/Roster** – manage AI employees, autonomy levels, quiet hours.

Keep this document aligned with the PRD when metrics or scope change.
