# Postmortem: Outbox DLQ Backlog – September 18, 2025

**Status:** Closed · Lessons applied to guardrail + worker backlog handling

## Summary

- **Incident ID / Link:** INC-2025-09-18-OUTBOX · `https://linear.app/ai-employee/issue/INC-2025-09-18-OUTBOX`
- **Date / Duration:** 2025-09-18 03:07–04:02 UTC (55 minutes)
- **Severity:** Sev 1 (tenant-affecting, partial workflow degradation)
- **Primary Systems Affected:** Outbox worker, Supabase `envelopes` + `envelope_attempts`
- **Detection Method:** Alert `outbox_dlq_size > 0` fired via Grafana OnCall
- **Incident Commander / Comms Owner:** Priya Shah (IC) / Luis Ortega (Comms)

## Impact

- **Tenant scope:** Tenants `acme-demo` and `northern-labs`
- **User-facing symptoms:** Approval flows stuck in "Waiting" state; operators unable to dispatch actions to Composio
- **SLO / SLA breach:** No SLA breach (under 60-minute recovery); breached internal workflow latency target

## Timeline

| Timestamp (UTC) | Event |
|-----------------|-------|
| 2025-09-18 03:07 | Grafana alert `outbox_dlq_size > 0` triggered (threshold: >0 for 5 minutes) |
| 2025-09-18 03:09 | IC assigned, incident channel `#inc-outbox-20250918` opened |
| 2025-09-18 03:12 | Worker logs show repeated Tenacity retries due to `HTTP 403` from Composio scope mismatch |
| 2025-09-18 03:18 | IC paused Outbox processing via feature flag `outbox.processing.enabled=false` |
| 2025-09-18 03:24 | Operators notified affected tenants; scopes re-authorisation requested |
| 2025-09-18 03:33 | New Composio OAuth tokens issued; scopes validated via `uv run python -m agent --check-scopes` |
| 2025-09-18 03:40 | DLQ envelopes drained back to active queue (`retry-dlq --limit 10`) |
| 2025-09-18 03:52 | Queue cleared; `outbox_dlq_size` returned to 0 |
| 2025-09-18 04:02 | Post-incident monitoring complete; incident closed |

## Root Cause

- **Trigger:** Composio OAuth scopes were revoked after a tenant admin rotated credentials without re-enabling `calendar.events.write`.
- **Contributing factors:**
  - Missing alert on `oauth_scope_expiry_days_remaining` metric (planned but not yet shipped).
  - Guardrail missing explicit validation for scope revocations, allowing tasks to queue before failure surfaced.

## Remediation

- **During incident:**
  - Paused Outbox worker to prevent additional DLQ growth.
  - Scoped Tenacity retries to 3 attempts to reduce noise while root cause investigated.
  - Issued tenant-facing updates every 10 minutes via Statuspage and shared Slack channels.
- **Post-incident:**
  - Added scope validation to guardrail checks (`agent/guardrails/scopes.py`).
  - Raised alert for `composio_scope_valid` toggle via Grafana.
  - Shipped Supabase migration to persist last-successful scope check timestamp.

## Follow-ups

- [x] Add regression test covering scope revocation failure path (`tests/guardrails/test_scopes.py`) – Owner: Priya Shah – Due: 2025-09-20
- [x] Update `agent/services/outbox.py` to short-circuit envelopes missing mandatory scopes – Owner: Evan Wu – Due: 2025-09-22
- [ ] Create tenant-facing knowledge base article covering scope refresh process – Owner: Luis Ortega – Due: 2025-10-10
- [ ] Automate scope expiry alerting via Supabase Edge Function – Owner: Data Platform – Due: 2025-10-24

## Communications Archive

### Internal Slack – Initial Alert (03:09 UTC)

> :rotating_light: Sev 1 declared for Outbox worker. Detected via `outbox_dlq_size` alert (03:07 UTC). Impact: approvals stuck for tenants acme-demo + northern-labs. Call bridge: meet.google.com/outbox-sev1. Next update by 03:19 UTC.

### Statuspage – Update #1 (03:18 UTC)

```
We are investigating elevated failures when dispatching automated actions. Affected tenants may see approvals stuck in "Waiting". We have paused execution to prevent duplicate attempts and are working with our automation provider. Next update by 03:28 UTC.
```

### Statuspage – Recovery (03:52 UTC)

```
Resolved – Automation approvals are processing normally again as of 03:46 UTC. Root cause was expired Composio OAuth scopes for two tenants. We refreshed credentials, drained the backlog, and are monitoring. Follow-up tasks are tracked in INC-2025-09-18-OUTBOX.
```

### Stakeholder Email (04:05 UTC)

```
Subject: [Resolved] Automation backlog for approvals

Hi team,

Earlier today (03:07–04:02 UTC) we experienced a backlog in the automation Outbox affecting two tenants. Approvals were paused while we re-authorised Composio scopes. No actions were lost, and queued envelopes completed by 03:52 UTC. We have added guardrails to detect scope revocations earlier and are publishing a tenant-facing guide for re-authorising integrations.

Incident reference: INC-2025-09-18-OUTBOX. Reach out if you see any lingering impact.

Thanks,
Luis
```

## Artefacts

- Worker logs: `s3://ai-employee-logs/worker/2025/09/18/outbox-sev1.log`
- Grafana dashboard snapshot: `docs/operations/runbooks/artifacts/INC-2025-09-18-OUTBOX-grafana.png`
- Guardrail test PR: `https://github.com/ai-employee/agent-control-plane/pull/482`

---

Document owner: Incident Commander rotates after every Sev-1. Update on each review cycle.
