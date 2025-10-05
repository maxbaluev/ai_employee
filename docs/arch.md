# AI Employee Platform — Architecture v1.1

> Minimal, verifiable plan for a Composio-only AI employee built on the existing repo (`src/app`, `agent/`) and upstream libraries bundled in `libs_docs/`. This replaces earlier drafts.

---

## 1. Scope & Dependencies

- **UI runtime:** Next.js 15 + CopilotKit (`@copilotkit/react-core`, `@copilotkit/react-ui`, `@copilotkit/runtime`). Verified by `src/app/page.tsx`, `src/app/layout.tsx`, and API route `src/app/api/copilotkit/route.ts`.
- **Agent runtime:** Google ADK LlmAgent served through FastAPI via `ag_ui_adk` (see `agent/agent.py`). Runner emits AGUI events consumed by CopilotKit (`@ag-ui/client` typings in `node_modules`).
- **Tooling:** Composio Python SDK (`composio.tools.get`, `composio.tools.execute`, `composio.connected_accounts`) with Google ADK provider (`libs_docs/composio_next/python/providers/google_adk/google_adk_demo.py`). Composio is the *only* external execution surface (ADR-0001).
- **State & scheduling:** Planned FastAPI control plane with Supabase/Postgres (RLS) for persistence, APScheduler for warm/trickle jobs, Tenacity for retries (dependencies already listed in `pyproject.toml`).

The architecture focuses on assembling these components with as little glue code as possible—re-using generated schemas, built-in AGUI wiring, and Composio metadata rather than custom integrations.

---

## 2. Verified Capabilities

| Capability | Evidence |
| ---------- | -------- |
| CopilotKit sidecar, shared state, frontend actions | `src/app/page.tsx`, `libs_docs/copilotkit_docs/adk/shared-state/...`, `.../frontend-actions.mdx` |
| Copilot Runtime ↔ ADK bridge | `src/app/api/copilotkit/route.ts`, `@ag-ui/client/dist/index.d.ts`, `libs_docs/copilotkit_docs/adk/quickstart.mdx` |
| ADK callbacks/state & function tools | `agent/agent.py`, `libs_docs/adk/full_llm_docs.txt` |
| Composio tool discovery & execution | `libs_docs/composio_next/python/examples/tools.py`, `.../connected_accounts.py` |
| Composio + ADK integration | `libs_docs/composio_next/python/providers/google_adk/google_adk_demo.py` |
| AGUI event set (RunStarted, ToolCall*, StateDelta, etc.) | `node_modules/@ag-ui/client/dist/index.d.ts` |

---

## 3. High-Level Topology

```
Next.js (CopilotKit UI)
├─ CopilotSidebar / desk pages (React)
│  ├─ useCopilotAction  (frontend actions)
│  └─ useCoAgent        (AGUI shared state)
├─ /api/copilotkit      (CopilotRuntime + ExperimentalEmptyAdapter)
│  └─ HttpAgent("http://agent:8000/")
│
FastAPI Control Plane
├─ ag_ui_adk.ADKAgent (wraps google.adk.agents.LlmAgent)
│  ├─ before_* callbacks manage state and prompt
│  └─ Runner streams AGUI events via SSE
├─ REST endpoints (objectives, approvals, tools, activity)
├─ Scheduler (APScheduler) for warm_scan/trickle_refresh
├─ Outbox service (idempotent execution via composio.tools.execute)
│  ├─ tenacity-based retries + DLQ
│  └─ quiet hours / rate-bucket enforcement
│
Supabase/Postgres (RLS)
├─ objectives, employees, assignments
├─ signals, evidence cards, tasks, actions, outbox queue
├─ tool_catalog (schemas, scopes, risk defaults)
│
Composio Cloud
├─ OAuth / connected accounts
├─ Tool schemas + metadata (`tools.get`, `toolkits.get_connected_account_*`)
├─ Execution API (`tools.execute`, `tools.proxy`)
└─ Webhook/trigger support (future)
```

---

## 4. Minimal Implementation Strategy

### 4.1 Frontend

- **Single CopilotKit Provider** in `layout.tsx` already points to `/api/copilotkit` with agent `my_agent`. Expand by splitting pages (`Desk`, `Approvals`, etc.) that read from shared state and REST endpoints—no custom websocket layer needed.
- **Schema-driven forms**: Use Composio JSON Schema (`tool.json_schema` from catalog) with a generic renderer (e.g., `@rjsf/core`) to prevent bespoke per-tool code. Enforce constraints at approve-time and surface validation errors inline.
- **State hydration**: `useCoAgent` receives `StateDeltaEvent` updates emitted from ADK. Persist plan/evidence/action snapshots inside ADK state to minimize API round-trips.

### 4.2 Copilot Runtime

- Keep the `ExperimentalEmptyAdapter` until multi-agent orchestration is required. For additional agents (e.g., evaluation), switch to a service adapter without modifying UI components.
- Inject middleware hooks (`onBeforeRequest`, `onAfterRequest`) to record metrics/traces (`docs/observability.md`).

### 4.3 ADK Agent

- Replace demo tools with Composio-provided `FunctionTool` objects using the GoogleAdkProvider. ADK natively consumes these as typed tools—no manual schema translation.
- Maintain state (signals, assigned tasks, trust metadata) in `callback_context.state` for quick plan iteration. Use `before_model_callback` to stitch signals and guardrails into prompts.
- Enforce safety directly in callbacks (e.g., fail fast if required scope disabled, or quiet hours). This keeps Outbox simple—reject invalid drafts before approval.

### 4.4 Control Plane + Outbox

- **Tool catalog sync**: Periodically call `composio.tools.get(user_id, toolkits, search)` and persist `json_schema`, `scopes`, `rate_limits`. Use the Python SDK’s `toolkits.get_connected_account_initiation_fields` to drive UI prompts.
- **Connected accounts**: Manage via `composio.connected_accounts` (initiate, wait_for_connection, enable/disable). Store IDs per tenant/app to reuse for execution.
- **Outbox**: Persist envelopes (`tool_slug`, `args`, `connected_account_id`, `risk`, `rate_bucket`, `external_id`). Dispatch with `composio.tools.execute(...)`. Handle provider conflicts by marking “success” per Composio recommendation. Idle detection + DLQ requeue via built-in Tenacity wait strategies.
- **Trickle refresh**: APScheduler jobs invoke reader kernels defined as JSON/YAML (no custom code). Each kernel maps to `composio.tools.execute` (read endpoints) with JSONPath extraction to produce Signals.

### 4.5 Data Model (RLS friendly)

The table layout in previous draft still applies; ensure indexes on `(tenant_id, status, rate_bucket)` for Outbox, `(tenant_id, objective_id)` for tasks, and unique `external_id` to enforce idempotency.

---

## 5. Interaction Flows

1. **Connect Composio**: Tenant initiates OAuth (`connected_accounts.initiate`). We wait for activation, sync available tools, and default `write_allowed=false` for risky categories.
2. **Warm Scan**: Scheduler executes configured kernels using Composio read tools. Signals stored; evidence cards pumped into ADK state and RLS tables.
3. **Planning**: Operator triggers plan run; CopilotRuntime streams AGUI events. ADK constructs proposals referencing Signals and Objectives.
4. **Approval**: Operator edits via schema form, approves, or rejects. Approval API copies envelope into Outbox with `approval_state=granted`.
5. **Execution**: Outbox worker pops queue, respects quiet hours/rate buckets, calls `composio.tools.execute` with correct `connected_account_id`, and updates status (`sent`, `failed`, `conflict`). AGUI events or state deltas inform UI.
6. **Feedback loop**: Trust score updated from audit logs; ADK references trust in next plan run (auto-approve low-risk when threshold met).

---

## 6. Safety & Compliance Considerations

- Guard all secrets with environment variables (`python-dotenv` only for dev). Never persist OAuth tokens outside secure store.
- Double-gate writes: `tool.write_allowed` in catalog *and* approval state. High-risk toolkits stay disabled until manager toggles.
- Quiet hours + DNC enforced both at Planner (card indicates blocked) and Outbox (hard stop). Provide override actions with audit trail.
- Composio outages → degrade to read-only: keep pending actions queued, surface banner, retry later. See `docs/observability.md` for alert thresholds.

---

## 7. Extensibility Hooks

- **Multi-agent**: Add specialized ADK agents (e.g., Compliance) and register via CopilotRuntime `agents` map, using service adapter for coordination.
- **Triggers/Webhooks**: Composio supports triggers; ingest into task queue once warm/trickle stable.
- **LiveKit worker**: Continue using existing worker; register call completions as Outbox success events for audit.
- **Localization**: Abstract strings pronto (see `docs/nfr.md`).

---

## 8. Open Issues / Next Steps

1. Implement tool catalog sync + connected account management (docs/todo.md §2).
2. Define reader kernel DSL and store baseline YAML configs.
3. Build Outbox worker skeleton leveraging Tenacity + composio.tools.execute.
4. Instrument CopilotRuntime/Outbox with OpenTelemetry per `docs/observability.md`.
5. Add runbooks for Composio outage and DLQ saturation.

This architecture keeps the system elegant and low-code by leaning on CopilotKit’s AGUI plumbing, ADK’s typed agents, and Composio’s schema/tooling fabric. Any new code should respect these boundaries to avoid bespoke integrations.
