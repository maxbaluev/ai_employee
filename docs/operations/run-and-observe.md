# Run & Observe

**Status:** Implemented (logging baseline) · In progress (metrics/tracing wiring, runbooks)

This guide outlines the operational baseline expected for every environment.

## Logging

- Today both the UI and agent log to stdout. Wrap FastAPI with `structlog` (dependency
  already declared) to produce JSON logs with tenant IDs, request IDs, and tool slugs.
- Redact secrets before logging (see `docs/governance/security-and-guardrails.md`).
- Forward logs to your chosen aggregator (e.g. Loki, Datadog) in production.

## Metrics

Expose Prometheus-compatible metrics from the agent process and scrape them via Prometheus:

1. **Instrument FastAPI** using `prometheus_client` and Starlette middleware.

   ```python
   # agent/app.py (excerpt)
   from prometheus_client import Counter, Gauge, Histogram, generate_latest
   from starlette.middleware import Middleware
   from starlette_exporter import PrometheusMiddleware

   copilot_requests_total = Counter(
       "copilotkit_requests_total", "Total AGUI requests", ["agent", "outcome"]
   )
   composio_latency_seconds = Histogram(
       "composio_execution_latency_seconds", "Composio execution latency", ["tool", "status"]
   )
   outbox_queue_size = Gauge("outbox_queue_size", "Pending envelopes", ["tenant"])
   scheduler_runs_total = Counter(
       "scheduler_runs_total", "Scheduler runs", ["job", "status"]
   )

   app.add_middleware(PrometheusMiddleware)

   @app.get("/metrics")
   async def metrics():
       return Response(generate_latest(), media_type="text/plain; version=0.0.4")
   ```

2. **Configure scraping** using Prometheus or an OpenTelemetry Collector with a
   Prometheus receiver. The canonical sample lives in
   `docs/references/observability.md`.

| Metric | Type | Labels |
|--------|------|--------|
| `copilotkit_requests_total` | Counter | `agent`, `outcome` |
| `composio_execution_latency_seconds` | Histogram | `tool`, `status` |
| `outbox_queue_size` | Gauge | `tenant` |
| `scheduler_runs_total` | Counter | `job`, `status` |
| `outbox_processed_total` | Counter | `tenant`, `status=success|retry|failed` |
| `outbox_dlq_size` | Gauge | `tenant` |

Update dashboards and alerts whenever additional labels are added.

For the canonical metric catalogue, dashboard outlines, and alert expressions, see
`docs/references/observability.md`.

## Tracing

- Instrument FastAPI with `opentelemetry-instrumentation-fastapi`.
- Configure exporters via OTLP env vars above and ensure trace IDs propagate from the
  UI (`x-copilot-trace-id` header) into Composio calls.
- Link traces to metrics using consistent `service.name` and span attributes
  (`tenant`, `tool`).

## Health Checks

- UI: rely on Next.js built-in health endpoint (`/`).
- Agent: expose `/healthz` returning success if the ADK runner can create a session and
  (once implemented) connect to Supabase/Composio.

## Alerting Baseline

| Scenario | Detection | First Response |
|----------|-----------|----------------|
| Composio outage | `copilotkit_requests_total{outcome="error"}` and `composio_execution_latency_seconds` > SLO | Follow `docs/operations/runbooks/composio-outage.md` |
| Outbox DLQ growth | `outbox_dlq_size{tenant}` > 0 for 5 min | Follow `docs/operations/runbooks/outbox-recovery.md` |
| Scheduler failure | `scheduler_runs_total{status="failure"}` increases | Disable autonomous runs, notify SRE; see `docs/operations/runbooks/scheduler.md` (TBD) |

## Local Troubleshooting

1. Run `npm run dev:debug` to enable verbose agent logs.
2. Use `curl -N http://localhost:8000/` to stream raw AGUI events.
3. If the UI cannot connect to the agent, ensure `NEXT_PUBLIC_COPILOTKIT_URL` (default is
   `/api/copilotkit`) points to a reachable endpoint.

Expand this document with concrete command snippets once observability wiring lands.
