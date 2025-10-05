# Observability Reference

Use this as the canonical list of metrics, logs, and dashboards once
`docs/operations/run-and-observe.md` is fully implemented.

## Metrics Catalogue (to be instrumented)

- Outbox queue size, latency, and failure counters.
- Scheduler run counts and latency.
- CopilotKit request rate, response time, and error rate.
- Composio execution latency, success ratio, and conflict count.

## Dashboards (planned)

1. **Operator Health** – pending approvals, average turnaround, approval vs rejection.
2. **Execution Pipeline** – Outbox throughput, Composio latency, DLQ backlog.
3. **Guardrails** – Quiet hour violations, scope upgrade prompts, trust score trends.

## Alerts (planned)

- Outbox DLQ > 0 for 5 minutes.
- Composio failure rate > 20% over 5 minutes.
- Scheduler failures in two consecutive runs.

Sync this reference when new signals are instrumented.
