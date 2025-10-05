# Threat Model — AI Employee Platform

## 1. Assets

- Tenant data: objectives, signals, tasks, actions, audit logs.
- Composio OAuth tokens and scope policies.
- Trust scores and autonomy settings.
- LiveKit call recordings/transcripts.

## 2. Actors

- **Tenant users** (operators, managers) — trusted but may misconfigure.
- **Malicious user** — tries to escalate privileges or extract data.
- **External attacker** — targets exposed APIs or injected content.
- **Composio service** — upstream dependency; compromise could affect tool behavior.

## 3. Entry Points

- Next.js UI (browser) → API calls.
- `/api/copilotkit` runtime endpoint (AGUI events).
- FastAPI REST endpoints (objectives, approvals, tools).
- Outbox worker calling Composio APIs.
- LiveKit webhook/event ingestion (future).

## 4. Threats & Mitigations

| Threat | Description | Mitigations |
| ------ | ----------- | ----------- |
| Session hijack | Stolen auth tokens used to issue approvals. | Use Supabase JWT with short TTL, refresh, audit suspicious approvals. |
| Cross-tenant data leak | RLS misconfiguration exposes data. | Strict RLS policies; automated tests (`FR-050`). |
| Prompt/plan injection | Malicious content from external tools manipulates planner. | Sanitize tool outputs, apply guardrails in ADK callbacks, limit autop-run to low-risk. |
| Scope escalation | Outbox executes with unintended scopes. | JIT scope requires human approval; store allowed scopes per tool; enforce at Outbox dispatch. |
| Composio outage | Planner/Outbox fails, actions stall. | Degrade to read-only, queue actions, alert via observability metrics. |
| Quiet hours bypass | Scheduled messages sent during restricted times. | Quiet-hour check before dispatch; audit log entry for overrides. |
| LiveKit data exposure | Calls contain PII. | Store minimal metadata, redact transcripts, enforce DNC compliance. |

## 5. Residual Risks / Open Questions

- No automated static analysis for Composio schema changes; risk of unsanitized fields entering prompts.
- AGUI transport currently unsecured beyond HTTPS; consider signed events for multi-tenant isolation.
- Need formal incident response doc (`runbooks/` future) covering Composio breach scenario.
- LiveKit stream security assumptions need validation; ensure tokens scoped per call.
