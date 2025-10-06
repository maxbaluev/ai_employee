# Control Plane Use Cases

**Status:** Aligned with Phase 4/5 implementation (October 6, 2025)**

## UC-01 · Monitor Queue Health

| Item | Description |
|------|-------------|
| **Actor** | Operations Lead |
| **Trigger** | Opening `/` or `/desk` while the agent is running |
| **Preconditions** | Worker connected to Supabase; shared state emitting queue deltas |
| **Main Flow** | 1. Navigate to `/` overview → review pending/approved counts.<br>2. Switch to `/desk` → inspect queue cards, evidence, statuses.<br>3. Use quick actions (Approve / Flag / Reset) to annotate queue items.<br>4. If counts spike, open Supabase dashboard or call `worker.outbox status`. |
| **Postconditions** | Updated queue statuses reflected in shared state and analytics API. |

## UC-02 · Approve an Envelope

| Item | Description |
|------|-------------|
| **Actor** | Customer Success Manager |
| **Trigger** | Guardrail or agent requests human approval |
| **Preconditions** | `approvalModal` slice populated; schema available from catalog |
| **Main Flow** | 1. Open `/approvals` → review summary, evidence, required scopes.<br>2. Fill schema-driven form fields (mapped from `schema.properties`).<br>3. Click `Approve` (updates shared state to `authorized`).<br>4. Agent/worker resumes, envelope enqueued/executed. |
| **Alternate Flow** | - Reject: mark `denied`, supply rejection notes.<br>- Cancel: mark `cancelled`, notify agent to defer. |
| **Postconditions** | Approval outcome stored in shared state; audit log records action. |

## UC-03 · Replay DLQ Envelopes

| Item | Description |
|------|-------------|
| **Actor** | Platform Engineer |
| **Trigger** | Alert (Supabase dashboard or Cron check) showing DLQ backlog |
| **Preconditions** | Worker CLI available; cause identified (e.g. scope mismatch) |
| **Main Flow** | 1. Run `uv run python -m worker.outbox status --tenant TENANT_ID` to confirm pending vs DLQ counts.<br>2. Address root cause (scope upgrade, schema fix).<br>3. Run `uv run python -m worker.outbox retry-dlq --tenant TENANT_ID --envelope ENV_ID` or drain batch.<br>4. Monitor `/analytics/outbox/status` and `/desk` until DLQ returns to zero. |
| **Postconditions** | Envelope transitions to `success`, audit log records worker action, DLQ cleared. |

## UC-04 · Review Guardrail Activity

| Item | Description |
|------|-------------|
| **Actor** | Operations Lead / Platform Engineer |
| **Trigger** | Guardrail block notification or dashboard request |
| **Preconditions** | Guardrail modules logging to Supabase `audit_log` |
| **Main Flow** | 1. Call `GET /analytics/guardrails/recent?tenant=TENANT_ID` or view Supabase SQL snippet.<br>2. Filter by guardrail name (quiet hours, trust, scopes, evidence).<br>3. If repeated blocks occur, adjust configuration (`AppSettings`) or escalate to guardrail owners. |
| **Postconditions** | Insight recorded; configuration updates planned via backlog. |

## UC-05 · Track Cron Sync Health

| Item | Description |
|------|-------------|
| **Actor** | Platform Engineer |
| **Trigger** | Scheduled health check or incident investigation |
| **Preconditions** | Supabase Cron configured (catalog sync, trickle refresh) |
| **Main Flow** | 1. Request `GET /analytics/cron/jobs?limit=20`.<br>2. Verify latest entries show `status='success'`.<br>3. On repeated failures, inspect Edge Function logs and rerun manually. |
| **Postconditions** | Cron job health validated; incidents triaged using existing runbooks. |

> Update this file as new surfaces (Integrations, Activity) ship so operators and PMs can
> reference canonical workflows.
