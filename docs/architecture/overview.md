# Architecture Overview

**Status:** Implemented (UI ↔ ADK bridge + Supabase control plane + Outbox worker)
· In progress (Composio tooling)

This overview summarises how requests flow through the platform today and calls out the
gaps you must close to reach the product vision captured in the references.

```
Browser (Next.js + CopilotKit)
 ├─ Shared state (`useCoAgent`) renders Desk/Approvals surfaces
 └─ Frontend actions (`useCopilotAction`) invoke tools via Copilot Runtime

Next.js API `/api/copilotkit`
 └─ CopilotRuntime + HttpAgent → forwards messages to Python agent over HTTP

FastAPI app (`agent/agent.py`)
 ├─ Wraps google.adk `LlmAgent`
 ├─ Provides before/after callbacks for guardrails + state
 └─ Streams AGUI events back to CopilotKit

Composio
 ├─ `Composio.tools.get` discovers schemas & scopes
 └─ `Composio.tools.execute` executes Outbox envelopes (worker-driven)

Supabase/Postgres
 ├─ Catalog + connected accounts + tasks + audit log (Supabase services)
 └─ Driven by APScheduler jobs (planned) + Outbox worker (`python -m worker.outbox start`)
```

Each component is elaborated in the dedicated sub-pages:

- `frontend.md` – Next.js + CopilotKit patterns and decisions.
- `agent-control-plane.md` – ADK callbacks, FastAPI surface, and the planned control
  plane modules.
- `composio-execution.md` – how Composio will be integrated end-to-end.
- `data-roadmap.md` – persistence model, background jobs, and roadmap status.

When you add new behaviour, update both the relevant sub-page and this diagram.
