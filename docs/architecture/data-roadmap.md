# Data Roadmap & Supabase Schema

**Status (October 6, 2025):** Implemented (catalog, objectives, outbox, employees, tasks, actions, audit) · In progress (signals, connected-account UX)

This document describes the persistence layer backing the control plane. Treat it as the
authoritative map when adding migrations or debugging Supabase data flows.

## Entity Overview

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ tool_catalog     │     │ objectives       │     │ audit_log        │
│──────────────────│     │──────────────────│     │──────────────────│
│ tenant_id (PK*)  │◄───▶│ tenant_id (FK)   │     │ envelope_id      │
│ tool_slug (PK*)  │     │ objective_id     │     │ actor_type/id    │
│ schema JSONB     │     │ metric/target    │     │ payload JSONB    │
│ required_scopes  │     │ horizon/summary  │     │ created_at       │
└──────────────────┘     └──────────────────┘     └──────────────────┘
           │                                       ▲
           │                                       │
           ▼                                       │
┌──────────────────┐     ┌──────────────────┐      │
│ employees        │     │ program_assign.  │      │
│──────────────────│     │──────────────────│      │
│ tenant_id (FK)   │◄────│ tenant_id (FK)   │      │
│ role/autonomy    │     │ capacity/priority│      │
└──────────────────┘     └──────────────────┘      │
           │                                       │
           ▼                                       │
┌──────────────────┐     ┌──────────────────┐      │
│ tasks            │◄────│ actions          │      │
│──────────────────│     │──────────────────│      │
│ employee_id (FK) │     │ external_id      │      │
│ status/proposed  │     │ tool/args/result │      │
└──────────────────┘     └──────────────────┘      │
           │                                       │
           ▼                                       │
┌──────────────────┐     ┌──────────────────┐      │
│ outbox           │◄────│ outbox_dlq       │──────┘
│──────────────────│     │──────────────────│
│ external_id      │     │ status='dlq'     │
│ rate_bucket      │     │ attempts/error   │
│ must_run_before  │     │                  │
└──────────────────┘     └──────────────────┘
```

> **PK*** – Composite key on `(tenant_id, tool_slug)` ensures catalog entries are
> deduplicated per tenant. Supabase enforces row-level security (RLS) so tenants can only
> read their own rows.

## Table Details

- **tool_catalog** – Populated by the catalog sync job. Columns include
  `category`, `read_write_flags`, `risk_default`, `approval_default`, `write_allowed`,
  `rate_bucket`, `schema`, and `required_scopes`. RLS: tenant `SELECT`, service role `UPSERT`.
- **objectives** – Long-lived goals rendered in the Desk queue seeding process. RLS
  mirrors `tool_catalog`.
- **employees** – Native multi-employee support (role, autonomy, schedule, status). RLS tenant-scoped.
- **program_assignments** – Per-employee program capacity and priority. RLS tenant-scoped.
- **tasks** – Proposed work items; links objectives/programs to employees; stores seed references to Evidence Cards. Index on `(tenant_id, employee_id, status)`.
- **actions** – Historical projection of executed envelopes (universal Action Envelope). Unique index on `external_id`.
- **outbox** – Primary action queue. Worker updates `status`, `attempts`, `metadata`, and
  `next_run_at`. Universal fields: `rate_bucket`, `must_run_before`, `result` JSON. Indexes:
  - `status_next_run_idx` on `(status, next_run_at)` for efficient polling.
  - `tenant_created_idx` on `(tenant_id, created_at desc)` for tenant-scoped dashboards.
- **outbox_dlq** – Stores failed envelopes when `move_to_dlq=True`. Shares schema with
  `outbox` for easy replay.
- **audit_log** – Append-only log; worker writes structured events with
  `actor_type='worker'`.
- **tool_policies** – Per-tool overrides (risk, approval, write_allowed, rate_bucket).

## Migration Conventions

- Place SQL migrations under `db/migrations/<version>_<description>.sql`. Use explicit
  column types and default values; avoid `SERIAL` in favour of `gen_random_uuid()` and
  `identity` columns where possible.
- Seed demo data in `db/seeds/` to keep local onboarding deterministic.
- When adding tables, update this document and the ERD ASCII diagram above. Include RLS
  policies and indexes in the same migration file.
- Run migrations via Supabase CLI:

  ```bash
  supabase db reset --schema public
  supabase db push
  ```

- For production, use Supabase change requests or CI pipelines to apply migrations; do
  **not** rely on `db push` from developer machines.

## Catalog Sync Job

- Command: `uv run python -m agent.services.catalog_sync`
- Scheduler: Supabase Cron (`catalog-sync-nightly`) invokes an Edge Function which runs
  the command with the service role key.
- Failure handling: the job logs via `structlog`. Monitor `cron_job_runs_total` and set up
  alerts for consecutive failures.

## Outbox Worker Lifecycle

- Command: `uv run python -m worker.outbox start`
- Polling: `outbox_poll_interval_seconds` (default 5s) controls the sleep between empty
  batches. `outbox_batch_size` defines the per-loop fetch limit.
- Retry semantics:
  - Worker uses Tenacity with exponential backoff up to `outbox_max_attempts`.
  - `SupabaseOutboxService.list_pending` excludes records with `next_run_at` in the
    future, ensuring scheduled retries respect delays.
  - Conflicts (`HTTP 409`) transition to `status='conflict'` without retry.
  - Non-retryable errors move the envelope to `outbox_dlq`.

## Views Available

- `outbox_pending_view` – optimized view of pending envelopes ready to send.
- `outbox_history_view` – terminal statuses with metadata for Activity timelines.
- `catalog_tools_view` – flattened tool + policy view consumed by Integrations.

## Observability Hooks

- **Supabase dashboards** – build charts directly from `outbox`, `outbox_dlq`, and
  `audit_log` using the SQL snippets in `docs/operations/run-and-observe.md`.
- **Logging** – `StructlogAuditLogger` records guardrail decisions and envelope outcomes
  with tenant and envelope identifiers. Persisted in `audit_log` for review.
- **DLQ alerts** – schedule a Supabase cron job or Edge Function to poll
  `select count(*) from outbox_dlq` and notify on-call channels when the count rises
  above zero for multiple intervals.

Keep this document updated whenever migrations or new tables land. Link architectural
decisions (ADRs) when introducing significant persistence changes.
