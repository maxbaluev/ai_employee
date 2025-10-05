# Delivery Roadmap (Snapshot)

This is a trimmed version of the original roadmap aligned with the new documentation.
Update it as milestone plans evolve.

## Phase 0 — Local Foundations (DONE)

- Next.js + CopilotKit demo page wired to ADK agent.
- FastAPI wrapper exposing AGUI events.

## Phase 1 — Composio Read Path (IN PROGRESS)

- Integrate Composio catalog fetch + connected account lifecycle.
- Surface warm scan evidence in Desk UI.

## Phase 2 — Approvals & Outbox (PLANNED)

- Schema-driven approval surfaces.
- Supabase persistence + Outbox worker with retries and DLQ.
- Trust scoring + quiet hours guardrails.

## Phase 3 — Operations & Autonomy (PLANNED)

- Full observability stack (metrics, tracing, dashboards).
- Runbooks exercised (Composio outage, DLQ recovery).
- Optional autonomy upgrades for low-risk toolkits.

Track progress using issues linked to each phase. Update this snapshot at the end of each
sprint.
