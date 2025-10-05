# Core Concepts

**Status:** Implemented (UI + ADK scaffold) · In progress (Composio integration) ·
Planned (Supabase control plane, Outbox worker)

The AI Employee Platform is intentionally thin: most of the heavy lifting happens inside
battle-tested libraries (CopilotKit, Google ADK, Composio). This section explains how the
pieces fit together today and which extensions are coming next.

## 1. User Experience Layer (Next.js + CopilotKit)

- `src/app/page.tsx` demonstrates the Copilot sidebar, shared state, and frontend
  actions. The UI subscribes to agent state via `useCoAgent` and exposes actions with
  `useCopilotAction`.
- `/api/copilotkit/route.ts` (see the Next.js app directory) instantiates a
  `CopilotRuntime` and bridges requests to the Python agent using `HttpAgent` from
  `@ag-ui/client`.
- Planned: replace the demo page with product surfaces (Desk, Approvals, Integrations).
  The `docs/implementation/frontend-shared-state.md` guide covers the conventions we will
  follow when building them.

## 2. Agent Runtime (FastAPI + Google ADK)

- `agent/agent.py` defines a single `LlmAgent` with callbacks that maintain a simple
  “proverbs” state and a stubbed weather tool.
- `ag_ui_adk` adds an HTTP endpoint (`/`) that streams AGUI events consumed by
  CopilotKit.
- Planned: move prompt construction, guardrails, and multi-employee logic into dedicated
  modules rather than living in a single file. See
  `docs/implementation/backend-callbacks.md` for preview code.

## 3. Composio Execution Layer (Planned Integration)

- ADR-0001 mandates that Composio is the sole tool provider.
- The repository already vendors example code in
  `libs_docs/composio_next/python/providers/google_adk/google_adk_demo.py` showing how to
  request tools and execute calls through ADK.
- Actual integration work (connected accounts, catalog sync, Outbox execution) is still
  pending. Follow `docs/implementation/composio-tooling.md` when you start landing it.

## 4. Data Plane & Control Services (Planned)

- `pyproject.toml` lists Supabase, APScheduler, Tenacity, and structlog dependencies, but
  there are no modules using them yet.
- Roadmap items (catalog persistence, Outbox worker, audit log) are documented in
  `docs/architecture/data-roadmap.md`. Treat those sections as the contract for future
  work.

## 5. Observability & Safety

- Today the agent and UI log to stdout; there is no metrics or tracing pipeline.
- The new expectations for metrics, logging hygiene, and runbooks live in
  `docs/operations/run-and-observe.md` and `docs/governance/security-and-guardrails.md`.

Keep this mental model handy—the rest of the docs assume you know where to plug work into
the system.
