# Observability Plan

## Metrics

| Metric | Source | Notes |
| ------ | ------ | ----- |
| `connect_value_seconds` | FastAPI control plane | Time from Composio connect to first approved action. Emit histogram. |
| `outbox_delivery_seconds` | Outbox worker | Enqueue-to-completion latency per tool + rate bucket labels. |
| `outbox_failures_total` | Outbox worker | Counter by failure category (provider_4xx, provider_5xx, scope_missing, quiet_hours). |
| `plan_cards_generated_total` | ADK planner | Counts proposals per objective and risk tier. |
| `approval_decisions_total` | Control plane | Labeled by decision (approve, reject, edited, auto). |
| `trust_score` | Control plane | Gauge per employee; accompany with change events. |
| `scheduler_runs_total` | Scheduler | Track warm_scan/trickle_refresh success/failure.

## Logging

- Structured JSON with fields: `timestamp`, `level`, `tenant_id`, `employee_id`, `request_id`, `run_id`, `event`, `context` (dict).
- Sensitive values hashed or redacted (`email`, `phone`). See `docs/logging-privacy.md`.
- UI logs limited to warnings/errors; avoid duplicating backend context.

## Tracing

- Use OpenTelemetry (OTLP) exporters.
- Required spans:
  - `plan.run` (CopilotRuntime → ADK agent → signals fetch).
  - `approval.decision` (UI action → API → Outbox enqueue).
  - `outbox.delivery` (enqueue → Composio call → result).
- Propagate `traceparent` through AGUI metadata if possible; otherwise map run IDs to trace IDs in middleware.

## Dashboards

- **Overview**: connect→value, actions per tool, Outbox latency percentiles, approval rate.
- **Reliability**: DLQ backlog, retry counts, Composio error codes, scheduler failures.
- **Adoption**: Objectives per tenant, tools enabled, trust score distribution.

## Alerts

- Outbox DLQ > 10 pending items for 15 minutes.
- `outbox_delivery_seconds` p95 > 10 minutes for 3 consecutive intervals.
- Scheduler failure rate > 20% over 1 hour.
- Composio API errors (5xx) > 5/min.

## Gaps / TODO

- Need to select metrics backend (Prometheus vs. hosted solution).
- Tracing propagation through AGUI requires spike; fallback is manual correlation logs.
- LiveKit worker metrics presently siloed; add integration in Sprint 2 (see `docs/roadmap.md`).
