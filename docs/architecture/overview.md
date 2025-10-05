# Architecture Overview

**Status:** Implemented (UI ↔ ADK bridge) · In progress (Composio tooling) · Planned
(Supabase control plane, Outbox worker)

This overview summarises how requests flow through the platform today and calls out the
gaps you must close to reach the product vision captured in the references.

```
Browser (Next.js + CopilotKit)
 ├─ Shared state (`useCoAgent`) renders Desk/Approvals surfaces (planned)
 └─ Frontend actions (`useCopilotAction`) invoke tools via Copilot Runtime

Next.js API `/api/copilotkit`
 └─ CopilotRuntime + HttpAgent → forwards messages to Python agent over HTTP

FastAPI app (`agent/agent.py`)
 ├─ Wraps google.adk `LlmAgent`
 ├─ Provides before/after callbacks for guardrails + state
 └─ Streams AGUI events back to CopilotKit

Composio (planned integration)
 ├─ `Composio.tools.get` discovers schemas & scopes
 └─ `Composio.tools.execute` executes Outbox envelopes

Supabase/Postgres (planned)
 ├─ Catalog + connected accounts + tasks + audit log
 └─ Driven by APScheduler jobs + Outbox workers
```

Each component is elaborated in the dedicated sub-pages:

- `frontend.md` – Next.js + CopilotKit patterns and decisions.
- `agent-control-plane.md` – ADK callbacks, FastAPI surface, and the planned control
  plane modules.
- `composio-execution.md` – how Composio will be integrated end-to-end.
- `data-roadmap.md` – persistence model, background jobs, and roadmap status.

When you add new behaviour, update both the relevant sub-page and this diagram.
