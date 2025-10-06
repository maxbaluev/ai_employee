# Architecture Overview

**Status:** Implemented (UI ↔ ADK bridge + Supabase control plane + Outbox worker)
· In progress (Composio‑only broker, Sidecar polish)

This overview summarises how requests flow through the platform today and calls out the
gaps you must close to reach the product vision captured in the references.

```
React (Next.js) + CopilotKit (AG‑UI)
 ├─ Shared state (`useCoAgent`) renders Desk/Approvals/Activity/Integrations/Roster
 └─ Frontend actions (`useCopilotAction`) for UX‑only effects

Next.js API `/api/copilotkit`
 └─ CopilotRuntime + HttpAgent → forwards messages to FastAPI agent

FastAPI (`agent/app.py`)
 ├─ Wraps ADK `LlmAgent` (typed agents: Planner, Drafter, Compliance, QA/Eval)
 ├─ Streams AG‑UI events + JSON Patch state deltas
 └─ Brokers Composio (discover tools, JSON Schemas, policies)

Outbox Worker (`worker/outbox.py`)
 └─ Sole executor for `mcp.exec` Action Envelopes (idempotent, retries, DLQ)

Supabase/Postgres (RLS)
 ├─ Minimal state: objectives, employees, tasks, actions, outbox, tools_catalog, policies,
 │  signals (optional), audit_log, trust_ledger
 └─ Supabase Cron + Edge Functions for catalog sync and periodic refresh
```

Invariants: one universal write, one executor, one UI stream; zero per‑tool code.

Each component is elaborated in the dedicated sub-pages:

- `frontend.md` – Next.js + CopilotKit patterns and decisions.
- `agent-control-plane.md` – ADK callbacks, FastAPI surface, and the planned control
  plane modules.
- `composio-execution.md` – Composio‑only integration end‑to‑end.
- `universal-action-envelope.md` – single write contract (`mcp.exec`).
- `data-roadmap.md` – persistence model, background jobs, and roadmap status.

When you add new behaviour, update both the relevant sub-page and this diagram.
