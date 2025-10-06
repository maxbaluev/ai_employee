# Run & Observe

**Status:** Implemented (logging baseline, Supabase-only analytics) · In progress (optional metrics/tracing)

Phase 5 observability stays inside Supabase (no external Prometheus). Use analytics
routes and saved SQL/dashboard widgets for ops. See also the acceptance criteria in
`docs/prd/universal-ai-employee-prd.md`.

This guide outlines the operational baseline expected for every environment.

## Logging

- Today both the UI and agent log to stdout. Wrap FastAPI with `structlog` (dependency
  already declared) to produce JSON logs with tenant IDs, request IDs, and tool slugs.
- Redact secrets before logging (see `docs/governance/security-and-guardrails.md`).
- Forward logs to your chosen aggregator (e.g. Loki, Datadog) in production.

## Operational Dashboards

Rely on Supabase as the system of record for queue and audit data—no external telemetry
stack is required for Phase 5.

1. **Outbox status** – create a Supabase saved SQL snippet (leverages `outbox_pending_view`):

   ```sql
   select 'pending' as status, count(*)
   from outbox_pending_view
   where tenant_id = :tenant_id
   union all
   select status, count(*)
   from outbox
   where tenant_id = :tenant_id and status in ('sent','failed','conflict','skipped','success')
   group by status;
   ```

   Visualise it as a bar chart to spot stalled envelopes.

2. **DLQ backlog** – `select count(*) from outbox_dlq where tenant_id = :tenant_id;`
   Pair this with the runbook in `docs/operations/runbooks/outbox-recovery.md`.

3. **Guardrail activity** – query the audit log:

   ```sql
   select guardrail, allowed, reason, created_at
   from audit_log
   where actor_type = 'agent' and tenant_id = :tenant_id
   order by created_at desc
   limit 50;
   ```

4. **Cron health** – use Supabase's Cron dashboard or SQL:

   ```sql
   select job_name, status, last_run, last_success
   from cron.job_run_details
   order by last_run desc
   limit 20;
   ```

Pin these queries to a Supabase dashboard or embed them in the internal admin panel so
operators can monitor the system without leaving the managed stack.

## Agent Analytics API

The control plane exposes lightweight helper routes for Ops tooling:

- `GET /analytics/outbox/status?tenant=<id>` – returns status counts and DLQ size.
- `GET /analytics/guardrails/recent?tenant=<id>&limit=20` – latest guardrail audit rows.
- `GET /analytics/cron/jobs?limit=20` – recent Supabase Cron executions.

Use these endpoints from internal dashboards or scripts when you need quick snapshots
without direct SQL access.

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
- Agent: `/healthz` and `/readyz` return `{status:"ok"}`. `/metrics` is a stub for now;
  use analytics endpoints and Supabase dashboards.
- Supabase Cron: monitor `cron.job_run_details` for failed runs.

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
