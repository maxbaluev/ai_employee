# Runbook: Outbox DLQ Recovery

**Status:** Planned (worker not yet implemented)

This runbook covers recovering from stuck or failed envelopes once the Outbox worker is
live.

## Detection

- `outbox_dlq_size > 0` for more than 5 minutes.
- Repeated Tenacity failures logged for the same envelope.
- Operators see actions marked as "Waiting" for extended periods.

## Immediate Stabilisation

1. Pause automated approvals for the affected tenant to avoid queue growth.
2. Investigate the DLQ payload – confirm the failure reason (scope error, provider
   conflict, validation failure).
3. Communicate status to operators (UI banner or direct message).

## Remediation Options

- **Scope / permission issue** – prompt the operator to upgrade scopes via the
  Integrations surface, then requeue the envelope once scopes are enabled.
- **Provider conflict** – mark as `conflict`, notify the operator, and do not retry.
- **Validation bug** – fix server-side schema mapping, add regression tests, and requeue
  affected envelopes.

## Post-Mortem

- Capture root cause, resolution, and preventive actions.
- Update guardrails tests to cover the failure scenario.
- Consider adding synthetic monitoring for the affected tool category.

Fill in the TODOs when the worker ships.
