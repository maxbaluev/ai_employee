# Incident Postmortem Template

**Status:** In progress · Update once the worker and guardrail stacks are GA

Use this template after any incident (production or staging) that triggers an
operator-facing alert or materially impacts tenant workflows. Store all artefacts
(logs, screenshots, queries) alongside the incident ticket or under
`docs/operations/runbooks/artifacts/<incident-id>/` so future reviews have a single
reference point.

## Summary

- **Incident ID / Link:**
- **Date / Duration:**
- **Primary Systems Affected:**
- **Detection Method:** (alert, operator report, synthetic monitor)

## Impact

- **Tenant scope:**
- **User-facing symptoms:**
- **SLO / SLA breach:**

## Timeline

| Timestamp (UTC) | Event |
|-----------------|-------|
| 2025-10-06 14:03 | Alert fired (`outbox_dlq_size > 0` for tenant Foo) |
|  |  |

## Root Cause

- What triggered the incident?
- Contributing factors (config drift, missing guardrails, dependency issues)?

## Remediation

- Short-term fixes applied during the incident.
- Longer-term code or infrastructure changes implemented immediately after.

## Follow-ups

- [ ] Action item 1 (owner, due date)
- [ ] Action item 2 (owner, due date)

### Comms Snippet

Use this as a starting point for stakeholder updates (Slack/email). Adjust tone based on
audience.

```
Heads-up: We detected an issue with <system/feature> starting at <time UTC>. Impacted tenants experienced <symptom>. We have applied <mitigation> and are monitoring recovery. Expect another update by <next-update-time>. Reference: <incident-link>.
```

Keep the template up to date with real examples after each review cycle.
