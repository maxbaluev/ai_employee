# Incident Postmortem Template

**Status:** Updated October 6, 2025 · Review quarterly or after any Sev-1 incident

Use this template after any incident (production or staging) that triggers an
operator-facing alert or materially impacts tenant workflows. Store all artefacts
(logs, screenshots, queries) alongside the incident ticket or under
`docs/operations/runbooks/artifacts/<incident-id>/` so future reviews have a single
reference point. Completed examples live in
`docs/operations/runbooks/postmortems/` to keep lessons learned close to the template.

## Summary

- **Incident ID / Link:**
- **Date / Duration:**
- **Severity:** (Sev 0–3; see `docs/operations/run-and-observe.md#incident-severity`)
- **Primary Systems Affected:**
- **Detection Method:** (alert, operator report, synthetic monitor)
- **Incident Commander / Comms Owner:**

## Impact

- **Tenant scope:**
- **User-facing symptoms:**
- **SLO / SLA breach:**

## Timeline

| Timestamp (UTC) | Event |
|-----------------|-------|
| 2025-10-06 14:03 | Alert fired (`outbox_dlq_size > 0` for tenant Foo) |
|  |  |
| 2025-10-06 14:05 | Incident channel opened (`#inc-outbox-foo`) |
| 2025-10-06 14:12 | Tenacity failures traced to expired Composio scopes |
| 2025-10-06 14:40 | Scopes re-authorised; envelopes retried |
| 2025-10-06 14:55 | DLQ cleared; monitoring for 30 minutes |

## Root Cause

- What triggered the incident?
- Contributing factors (config drift, missing guardrails, dependency issues)?

## Remediation

- Short-term fixes applied during the incident.
- Longer-term code or infrastructure changes implemented immediately after.

## Follow-ups

- [ ] Action item 1 (owner, due date)
- [ ] Action item 2 (owner, due date)
- [ ] Add dashboard / monitor updates (owner, due date)
- [ ] Ship regression tests or guardrails (owner, due date)

### Comms Snippet

Use this as a starting point for stakeholder updates (Slack/email). Adjust tone based on
audience.

```
Heads-up: We detected an issue with <system/feature> starting at <time UTC>. Impacted tenants experienced <symptom>. We have applied <mitigation> and are monitoring recovery. Expect another update by <next-update-time>. Reference: <incident-link>.
```

Keep the template up to date with real examples after each review cycle.

### Communication Templates

- **Initial Slack (internal operators):**

  > :rotating_light: Sev <level> incident declared for <system>. Detected at <time UTC> via <signal>. Impact: <summary>. Call joins: <link>. Next update by <next-update-time>.

- **Status page / tenant email:**

  ```
  Subject: Incident update – <system/feature>

  We are investigating an incident affecting <scope>. Symptoms include <symptom>. Workaround: <workaround or "none">. We will post the next update by <next-update-time>. Track progress at <status-page-link>.
  ```

- **Recovery confirmation:**

  > ✅ Resolved: <system> incident from <start-time> UTC. Root cause: <summary>. Mitigation: <steps>. Monitoring continues for <duration>. Follow-ups tracked in <ticket-ids>.

Reference completed examples in
[`postmortems/outbox-dlq-2025-09-18.md`](postmortems/outbox-dlq-2025-09-18.md) and add new
entries as incidents conclude.
