# Functional Requirements Summary

**Source:** Consolidated from legacy requirements (`docs/requirements.md`)

These requirements remain valid even though the implementation is incomplete. Track
progress in Jira/Linear and update the status column as features land.

| ID | Description | Key Dependencies | Status |
|----|-------------|------------------|--------|
| FR-001 | Capture objectives (metric, target, horizon) before plans run. | Supabase tables, REST API | Planned |
| FR-002 | Configure guardrails (quiet hours, allowed toolkits, tone). | Supabase, guardrail callbacks | Planned |
| FR-003 | Manage Composio connected accounts lifecycle. | Composio SDK, catalog service | Planned |
| FR-010 | Warm scan after connecting; surface evidence cards. | Scheduler, catalog, UI surfaces | Planned |
| FR-012 | Plan assembly creates envelopes with tool slug, args, evidence. | Agent refactor, catalog metadata | In progress |
| FR-020 | Schema-driven edits enforced client + server side. | JSON Schema renderer, validation service | Planned |
| FR-022 | Outbox executes envelopes with retries + DLQ. | Worker, Supabase, Tenacity | Planned |
| FR-030 | Roster management with autonomy levels. | Supabase, UI surfaces | Planned |
| FR-040 | Activity timeline for execution traces. | Supabase audit log, UI surface | Planned |
| FR-050 | Tenant isolation via RLS. | Supabase policies | Planned |

Update this table whenever requirements change or features ship.
