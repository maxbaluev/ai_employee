# Minimal Data Model (RLS)

**Status:** Drafted October 6, 2025 · Matches universal PRD

This document enumerates the minimal tenant‑scoped schema that powers the control plane.
See `docs/architecture/data-roadmap.md` for migration conventions and operational notes.

## Tables

- objectives — `objective_id pk, tenant_id, name, metric_key, target_value, horizon_days, created_at`
- employees — `employee_id pk, tenant_id, role, autonomy, schedule, status, created_at`
- program_assignments — `employee_id, program_id, capacity_per_day, priority, enabled`
- tasks — `id pk, tenant_id, employee_id, objective_id?, program_id?, title, status, proposed_at, approved_at, executed_at, seed_ref jsonb`
- actions — `id pk, tenant_id, task_id, employee_id, type="mcp.exec", tool jsonb, args jsonb, risk, approval_state, result jsonb, external_id, created_at, completed_at`
- outbox — `id pk, tenant_id, action_id, status(pending/sending/sent/failed/dead), retry_count, next_attempt_at, last_error`
- tools_catalog — `tenant_id, composio_app, tool_key, category, json_schema, read_write_flags, risk_default, approval_default, write_allowed, rate_bucket, updated_at` (pk `(tenant_id, composio_app, tool_key)`)
- tool_policies — `tenant_id, composio_app, tool_key, risk, approval, write_allowed, rate_bucket`
- signals (optional) — `id pk, tenant_id, kind, source_tool, features jsonb, examples jsonb, updated_at`
- contacts_lite — `tenant_id, contact_id pk, vendor, vendor_contact_id, display_name, phone_e164[], email_hash[], tz, features jsonb, updated_at`
- call_jobs / call_outcomes — existing LiveKit integration tables
- audit_log — `id pk, tenant_id, who, what, when, details jsonb`
- trust_ledger — `employee_id, day, approved_no_edit, edited, rejected, errors, complaints, score` (pk `(employee_id, day)`)

## Indexes

- `outbox(status, next_attempt_at)` — efficient worker polling
- `actions(external_id)` — idempotency
- GIN indexes on JSONB fields referenced by Reader Kernels
- Tenant‑scoped indexes (e.g., `(tenant_id, created_at desc)`) for dashboards

## Views (recommended)

- `outbox_pending_view` — tenant‑scoped pending envelopes
- `outbox_history_view` — recent execution outcomes
- `catalog_tools_view` — flattened tool schema/policy for UI

## RLS Policies

- Tenants can `SELECT` their rows; service role can `UPSERT` where applicable.
- Ensure audit logs capture actor + tenant on every mutation.

Keep this file synchronized with migrations. Add ADRs for any non‑backwards‑compatible changes.

