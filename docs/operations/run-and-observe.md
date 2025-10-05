# Run & Observe

**Status:** Implemented (basic logging) · Planned (metrics, tracing, runbooks)

This guide outlines the operational baseline expected for every environment.

## Logging

- Today both the UI and agent log to stdout. Wrap FastAPI with `structlog` (dependency
  already declared) to produce JSON logs with tenant IDs, request IDs, and tool slugs.
- Redact secrets before logging (see `docs/governance/security-and-guardrails.md`).
- Forward logs to your chosen aggregator (e.g. Loki, Datadog) in production.

## Metrics

Plan to expose the following via Prometheus or OTLP:

| Metric | Type | Notes |
|--------|------|-------|
| `copilotkit_requests_total` | Counter | Label by agent, outcome. |
| `composio_execution_latency_seconds` | Histogram | Include `tool_slug`, `status`. |
| `outbox_queue_size` | Gauge | Pending envelopes per tenant. |
| `scheduler_runs_total` | Counter | Warm scan + trickle refresh successes/failures. |

Add a `/metrics` endpoint to the FastAPI app once the control plane exists.

## Tracing

- Use OpenTelemetry (OTLP) to trace requests from the UI through the runtime to the
  agent and (eventually) Composio. Start by instrumenting FastAPI and the HTTP bridge.
- Propagate trace IDs via headers when frontend calls REST endpoints.

## Health Checks

- UI: rely on Next.js built-in health endpoint (`/`).
- Agent: expose `/healthz` returning success if the ADK runner can create a session and
  (once implemented) connect to Supabase/Composio.

## Alerting Baseline

| Scenario | Detection | First Response |
|----------|-----------|----------------|
| Composio outage | Execution error rate > X% | Follow `docs/operations/runbooks/composio-outage.md`. |
| Outbox DLQ growth | `outbox_dlq_size > 0` for 5 minutes | Investigate envelopes, communicate to operators. |
| Scheduler failure | `scheduler_runs_total{status="failure"}` increases | Disable autonomous runs, notify SRE. |

## Local Troubleshooting

1. Run `npm run dev:debug` to enable verbose agent logs.
2. Use `curl -N http://localhost:8000/` to stream raw AGUI events.
3. If the UI cannot connect to the agent, ensure `NEXT_PUBLIC_COPILOTKIT_URL` (default is
   `/api/copilotkit`) points to a reachable endpoint.

Expand this document with concrete command snippets once observability wiring lands.
