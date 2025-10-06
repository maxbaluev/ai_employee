# Observability Reference

**Status:** Supabase-only analytics implemented; optional metrics/tracing in progress.

This document is the canonical source for telemetry names, sampling defaults, and
runbook cross-references. Update it in lockstep with `docs/operations/run-and-observe.md`
and the linked runbooks.

## Analytics (primary)

- Use Supabase dashboards and the built-in analytics API routes:
  - `GET /analytics/outbox/status?tenant=<id>`
  - `GET /analytics/guardrails/recent?tenant=<id>&limit=20`
  - `GET /analytics/cron/jobs?limit=20`
- Recommended Supabase queries:
  - Outbox status: union of `outbox_pending_view` and terminal statuses from `outbox`.
  - DLQ backlog: `select count(*) from outbox_dlq where tenant_id=:tenant_id`.
  - Guardrail activity: `select guardrail, allowed, reason, created_at from audit_log where actor_type='agent'`.

## Metrics (optional, future)

- `/metrics` endpoint is a stub in Phase 5. If you add Prometheus, expose counters and
  histograms mirroring the catalogue below:

  | Metric | Type | Labels | Purpose |
  |--------|------|--------|---------|
  | `copilotkit_requests_total` | Counter | `agent`, `outcome` | Volume + error ratio of AGUI requests. |
  | `copilotkit_request_latency_seconds` | Histogram | `agent`, `outcome` | P95 budget 1.5s. |
  | `guardrail_decisions_total` | Counter | `guardrail`, `decision` | Track quiet hours, trust, scopes, evidence. |
  | `composio_execution_latency_seconds` | Histogram | `tool`, `status` | Identify slow or failing tools. |
  | `outbox_processed_total` | Counter | `tenant`, `status` | Success/retry/failure envelope counts. |
  | `outbox_queue_size` | Gauge | `tenant` | Depth of ready envelopes. |
  | `outbox_dlq_size` | Gauge | `tenant` | Dead-letter backlog. |
  | `cron_job_runs_total` | Counter | `job_name`, `status` | Supabase Cron job execution tracking. |

- **Dashboards:**
  - **Control Plane Overview:** request volume, latency P95, guardrail blocks by type.
  - **Outbox Worker:** processed/minute, queue size trend, DLQ growth, retry heatmap.
  - **Composio Tooling:** execution latency, retry ratio, tool-level error codes.

### Dashboard Queries & Placeholders

- **Control Plane Overview** (`public/images/observability/control-plane.png` TBD)
  - Requests per outcome:

    ```promql
    sum by (outcome) (rate(copilotkit_requests_total[5m]))
    ```

  - Latency P95:

    ```promql
    histogram_quantile(0.95, sum by (le) (rate(copilotkit_request_latency_seconds_bucket[5m])))
    ```

  - Guardrail decisions:

    ```promql
    sum by (guardrail, decision) (increase(guardrail_decisions_total[15m]))
    ```

- **Outbox Worker** (`public/images/observability/outbox-worker.png` TBD)
  - Processed envelopes per status:

    ```promql
    sum by (status) (rate(outbox_processed_total[5m]))
    ```

  - DLQ size trend:

    ```promql
    max by (tenant) (outbox_dlq_size)
    ```

  - Retry attempts heatmap:

    ```promql
    sum by (tenant) (increase(outbox_processed_total{status="retry"}[30m]))
    ```

- **Composio Tooling** (`public/images/observability/composio-tooling.png` TBD)
  - Execution latency P95 by tool:

    ```promql
    histogram_quantile(0.95, sum by (le, tool) (rate(composio_execution_latency_seconds_bucket[5m])))
    ```

  - Failure ratio:

    ```promql
    sum(rate(composio_execution_latency_seconds_count{status="failure"}[5m])) /
    sum(rate(composio_execution_latency_seconds_count[5m]))
    ```

  - Guardrail interactions (quiet hours, scopes, trust):

    ```promql
    sum by (guardrail) (increase(guardrail_decisions_total[1h]))
    ```

- **Alerts:** connect to runbooks.
  - `outbox_dlq_size > 0` for 5 minutes → `docs/operations/runbooks/outbox-recovery.md`
  - `copilotkit_request_latency_seconds_bucket{le="1.5"}` alert on P95 exceedance →
    `docs/operations/runbooks/ui-latency.md` (TBD).
  - `composio_execution_latency_seconds` > 15s P95 or failure rate >20% →
    `docs/operations/runbooks/composio-outage.md`.

## Tracing (optional)

- **Instrumentation packages:** `opentelemetry-instrumentation-fastapi`,
  `opentelemetry-sdk`, `opentelemetry-instrumentation-structlog`.
- **Environment defaults:**

  ```bash
  export OTEL_SERVICE_NAME=agent-control-plane
  export OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-collector.internal:4317
  export OTEL_TRACES_SAMPLER=parentbased_traceidratio
  export OTEL_TRACES_SAMPLER_ARG=0.1
  ```

- **Span attributes:** ensure `tenant_id`, `envelope_id`, `tool_name`, `guardrail` are
  attached where relevant.
- **Context propagation:** forward `traceparent` from CopilotKit UI → FastAPI →
  Composio worker envelope executions.

## Logging

- `structlog` configured in `agent/services/audit.py`; logs emit JSON lines. Required
  keys: `tenant_id`, `envelope_id`, `correlation_id`, `guardrail` (when present).
- Ship logs via stdout to the aggregator; scrubbing rules described in
  `docs/governance/security-and-guardrails.md`.
- When adding new log fields update this reference and the downstream parsing rules.
