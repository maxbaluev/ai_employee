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
   cron_job_runs_total = Counter(
       "cron_job_runs_total", "Supabase Cron job runs", ["job_name", "status"]
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
| `cron_job_runs_total` | Counter | `job_name`, `status` |
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

## Supabase Cron Jobs

All recurring scheduled workloads use Supabase Cron instead of in-process schedulers. This
ensures schedules survive agent restarts and scale independently.

### Managing Cron Jobs

- **Dashboard**: Navigate to **Integrations → Cron** in the Supabase dashboard to view,
  pause, or delete jobs.
- **SQL**: Use `cron.schedule()` to create jobs and `cron.unschedule()` to remove them:
  ```sql
  -- Schedule a nightly catalog sync
  SELECT cron.schedule(
    'catalog-sync-nightly',
    '0 2 * * *',  -- 2 AM daily
    $$SELECT net.http_post(
      url := 'https://your-project.supabase.co/functions/v1/catalog-sync',
      headers := '{"Authorization": "Bearer ' || current_setting('app.service_role_key') || '"}'::jsonb
    )$$
  );
  ```
- **Logs**: All runs are logged in `cron.job_run_details` with status, start time, and
  error messages.

### Registered Jobs

| Job Name | Schedule | Purpose | Edge Function |
|----------|----------|---------|---------------|
| `catalog-sync-nightly` | Daily at 2 AM | Sync Composio tool catalog (`uv run python -m agent.services.catalog_sync`) | `/functions/v1/catalog-sync` |
| `trickle-refresh-hourly` | Every hour | Refresh toolkit signals | `/functions/v1/trickle-refresh` |
| `embedding-reindex-nightly` | Daily at 3 AM | Recalculate embeddings | `/functions/v1/embedding-reindex` |

Update this table whenever new jobs are added.

### Edge Functions & pg_net Patterns

- Cron jobs and reactive pipelines should call Edge Functions using the `net.http_post`
  approach documented in `libs_docs/supabase/llms_docs.txt` (search for `cron.schedule`
  examples). Package payloads as JSON and include the `service_role` bearer token so the
  function can interact with Postgres securely.
- Use Edge Functions to fan out telemetry or hydrate external APIs. Keep these functions
  idempotent—store a `job_run_id` in Supabase so retries do not duplicate work.
- For synchronous agent tooling (e.g. evidence embeddings), call Edge Functions via the
  Supabase JS client: `supabase.functions.invoke('catalog-sync', { body })`. This mirrors
  the patterns in `libs_docs/composio_next/python/README.md` where the SDK exchanges
  tokens before executing a tool.
- Prefer Edge Functions over direct Postgres RPC for operations that require secret
  management or third-party API calls. Reserve RPCs for pure data mutations that run
  inside the database transaction boundary.

## Health Checks

- UI: rely on Next.js built-in health endpoint (`/`).
- Agent: expose `/healthz` returning success if the ADK runner can create a session and
  (once implemented) connect to Supabase/Composio.
- Supabase Cron: monitor `cron.job_run_details` for failed runs and `cron_job_runs_total`
  metric for trends.

## Alerting Baseline

| Scenario | Detection | First Response |
|----------|-----------|----------------|
| Composio outage | `copilotkit_requests_total{outcome="error"}` and `composio_execution_latency_seconds` > SLO | Follow `docs/operations/runbooks/composio-outage.md` |
| Outbox DLQ growth | `outbox_dlq_size{tenant}` > 0 for 5 min | Follow `docs/operations/runbooks/outbox-recovery.md` |
| Cron job failure | `cron_job_runs_total{status="failure"}` increases or jobs missing from `cron.job_run_details` | Check Supabase dashboard (Integrations → Cron), verify Edge Function health, review `cron.job_run_details` logs |

## Local Troubleshooting

1. Run `npm run dev:debug` to enable verbose agent logs.
2. Use `curl -N http://localhost:8000/` to stream raw AGUI events.
3. If the UI cannot connect to the agent, ensure `NEXT_PUBLIC_COPILOTKIT_URL` (default is
   `/api/copilotkit`) points to a reachable endpoint.

Expand this document with concrete command snippets once observability wiring lands.
