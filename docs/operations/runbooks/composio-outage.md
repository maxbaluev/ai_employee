# Runbook: Composio Outage

**Status:** Planned (integration pending)

This runbook outlines the steps to follow when Composio APIs are degraded or returning
errors. Execute it even in staging to keep muscle memory fresh.

## Detection

- Sudden spike in `composio_execution_latency_seconds` or error rate > 20%.
- API responses ≥ 500 or timeouts when calling `composio.tools.execute` / `tools.get`.
- Operators report failures when approving actions.

## Immediate Actions

1. **Switch platform to read-only:**
   - Disable Outbox processing (pause worker or set feature flag).
   - Surface a banner in the UI explaining that actions are queued.
2. **Retry strategy:** confirm Tenacity backoff is respectably capped to avoid hammering
   the provider.
3. **Open incident channel** with stakeholders (product, support, leadership).
   - Announce using the communication templates in
     [`incident-template.md`](incident-template.md#communication-templates).

## Diagnosis Checklist

- Check Composio status page / Slack to confirm a regional or global outage.
- Ensure credentials (`COMPOSIO_API_KEY`) have not expired or been revoked.
- Verify connected accounts are still active.

## Recovery

1. Once Composio signals recovery, re-enable the Outbox worker.
2. Monitor the backlog until `outbox_queue_size` returns to baseline.
3. Post-incident: capture timeline, impact, and action items in the incident tracker.

Update this runbook once the Outbox worker is implemented.
