# Runbook: Outbox DLQ Recovery

**Status:** Draft (worker implementation pending)

This runbook covers recovering from stuck or failed envelopes once the Outbox worker is
live.

## Detection & thresholds

- `outbox_dlq_size{tenant}` > 0 for > 5 minutes (alert defined in
  `docs/references/observability.md`).
- `outbox_processed_total{status="retry"}` increasing faster than
  `{status="success"}`.
- Repeated Tenacity failures logged for the same envelope ID.
- Operators report actions stuck in "Waiting" for > 10 minutes.

## CLI toolkit

Assuming the worker exposes the verbs planned in `docs/architecture/data-roadmap.md`:

```bash
# Inspect queue status for a tenant
mise run worker:status --tenant TENANT_ID

# Drain 20 envelopes from the DLQ back into the active queue
mise run worker:drain --tenant TENANT_ID --source dlq --limit 20

# Retry a specific DLQ envelope after remediation
mise run worker:retry-dlq --tenant TENANT_ID --envelope ENVELOPE_ID
```

If these commands are unavailable, escalate to the platform team for manual Supabase
updates or direct worker intervention.

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

## DLQ Replay Walkthrough

1. **Pre-checks** – Confirm the DLQ alert (`outbox_dlq_size`) and cross-reference the
   audit log for the latest failure reason (source: `docs/governance/security-and-guardrails.md`).
2. **Remediate cause** – Apply one of the remediation options above (scopes, schema fix,
   provider conflict).
3. **Replay command** – Execute `mise run worker:retry-dlq --tenant TENANT_ID --envelope ENVELOPE_ID`
   or drain a batch (`--limit`) if multiple envelopes share the same root cause.
4. **Audit expectations** – Ensure the worker emits an `audit_log` entry containing
   `actor_type='worker'`, the `envelope_id`, and a succinct reason (`retry-after-fix`). If
   performed manually, record the operator details in the audit log or ticket.
5. **Success criteria** – Envelope transitions to `status='success'`, DLQ gauge returns
   to 0, and UI surfaces reflect completion.

## Verification checklist

1. `/healthz` returns `{"status": "ok"}` for the agent and worker services.
2. `outbox_dlq_size` falls back to 0 and stays flat for 10 minutes.
3. `outbox_processed_total{status="success"}` increases for the affected tenant.
4. UI "Waiting" badges clear and audit logs show the rerun outcome.

## Post-Mortem

- Capture root cause, resolution, and preventive actions using the
  [`Incident Postmortem Template`](incident-template.md).
- Store supporting artefacts (logs, SQL, screenshots) with the incident ticket or under
  `docs/operations/runbooks/artifacts/<incident-id>/` for future audits.
- Add guardrail/worker tests covering the failure scenario.
- Consider synthetic monitors for the impacted tool category.
