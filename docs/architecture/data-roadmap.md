# Data & Roadmap

**Status:** Planned (no persistent storage implemented yet)

Although `pyproject.toml` already lists database- and scheduling-related dependencies,
the repository currently operates entirely in memory. This document anchors the future
state so we build a consistent control plane as we add persistence.

## Target Supabase Schema (Draft)

Below are the starter tables we expect to land in Supabase. The initial DDL lives in
`db/migrations/001_init.sql`; keep future migrations alongside the application so we can
evolve the schema in lock-step with the agent.

### `tenants`
- **Columns:** `id uuid primary key`, `name text`, `plan text`, `created_at timestamptz default now()`, `updated_at timestamptz`.
- **Indexes:** primary key + `create index tenants_plan_idx on tenants(plan)`. 
- **RLS:** enable RLS; policy `select on tenants using (id = auth.uid())` once auth wiring exists.
- **Cross-links:** feeds guardrail defaults (`docs/governance/security-and-guardrails.md`).

### `objectives`
- **Columns:** `id uuid pk`, `tenant_id uuid references tenants(id)`, `title text`, `metric text`, `target numeric`, `horizon interval`, timestamps.
- **Indexes:** `create index objectives_tenant_metric_idx on objectives(tenant_id, metric)`.
- **RLS:** tenant-scoped policy `using (tenant_id = auth.jwt() ->> 'tenant_id')::uuid`.
- **Cross-links:** aligns with shared state schema (`docs/implementation/frontend-shared-state.md`).

### `guardrails`
- **Columns:** `id uuid pk`, `tenant_id uuid references tenants(id)`, `quiet_hours jsonb`, `trust_threshold numeric`, `scopes jsonb`, timestamps.
- **Indexes:** `create unique index guardrails_tenant_uidx on guardrails(tenant_id)`.
- **RLS:** allow select/update for tenant owners only; block insert without service role.
- **Cross-links:** maps to guardrail docs (`docs/governance/security-and-guardrails.md`, `docs/implementation/backend-callbacks.md`).

### `connected_accounts`
- **Columns:** `id uuid pk`, `tenant_id uuid references tenants(id)`, `provider text`, `status text`, `scopes text[]`, `linked_at timestamptz`, `metadata jsonb`.
- **Indexes:** `create index connected_accounts_tenant_provider_idx on connected_accounts(tenant_id, provider)`.
- **RLS:** tenant owners can read/write their rows; Composio sync runs via service role.
- **Cross-links:** matches Composio integration guide (`docs/implementation/composio-tooling.md`).

### `tool_catalog`
- **Columns:** `id bigserial pk`, `tenant_id uuid references tenants(id)`, `tool_slug text`, `version text`, `risk text`, `schema jsonb`, `updated_at timestamptz`.
- **Indexes:** `create unique index tool_catalog_tenant_slug_version_idx on tool_catalog(tenant_id, tool_slug, version)`.
- **RLS:** read access for tenant; write restricted to catalog sync job.
- **Cross-links:** forms the backing store for schema-driven UI (`docs/implementation/frontend-shared-state.md`).

### `outbox`
- **Columns:** `id uuid pk`, `tenant_id uuid references tenants(id)`, `envelope jsonb`, `status text`, `attempts integer default 0`, `external_id text`, `next_run_at timestamptz`, `last_error text`.
- **Indexes:** `create index outbox_tenant_status_idx on outbox(tenant_id, status)` and `create unique index outbox_external_id_uidx on outbox(external_id)`.
- **RLS:** allow select/insert/update for tenant owners; worker runs with elevated role.
- **Cross-links:** supports worker contract (`#outbox-worker-contract` below).

### `audit_log`
- **Columns:** `id bigint generated always as identity primary key`, `tenant_id uuid`, `actor_type text`, `actor_id text`, `category text`, `payload jsonb`, `created_at timestamptz default now()`.
- **Indexes:** `create index audit_log_tenant_created_idx on audit_log(tenant_id, created_at desc)`.
- **RLS:** read-only per tenant; writes allowed to service roles to ensure tamper-evidence.
- **Cross-links:** referenced by governance guidance (`docs/governance/ownership-and-evergreen.md`).

### ERD Snapshot

```mermaid
erDiagram
    tenants ||--o{ objectives : "tenant_id"
    tenants ||--|| guardrails : "tenant_id"
    tenants ||--o{ connected_accounts : "tenant_id"
    tenants ||--o{ tool_catalog : "tenant_id"
    tenants ||--o{ outbox : "tenant_id"
    tenants ||--o{ audit_log : "tenant_id"

    tenants {
        uuid id PK
        text name
        text plan
    }
    objectives {
        uuid id PK
        uuid tenant_id FK
        text metric
        numeric target
        interval horizon
    }
    guardrails {
        uuid tenant_id PK
        jsonb config
        timestamptz updated_at
    }
    connected_accounts {
        uuid id PK
        uuid tenant_id FK
        text provider
        text status
    }
    tool_catalog {
        bigint id PK
        uuid tenant_id FK
        text tool_slug
        text version
        jsonb schema
    }
    outbox {
        uuid id PK
        uuid tenant_id FK
        jsonb envelope
        text status
        int attempts
    }
    audit_log {
        bigint id PK
        uuid tenant_id FK
        text category
        jsonb payload
        text actor
    }
```

All tables run with Row-Level Security enabled and assume JWTs carry a `tenant_id` claim. 
Adjust policies once authentication wiring is finalised.

## Scheduling & Jobs

- **Warm scan** – triggers immediately after a tenant connects Composio; executes read
  tools to hydrate signals and evidence into Supabase.
- **Trickle refresh** – runs every 30–60 minutes per toolkit category respecting rate
  buckets. Store scheduling metadata alongside tool definitions.
- **Catalog drift monitor** – compares local schema with the latest `composio.tools.get`
  output; raises alerts when drift occurs.

## Outbox Worker Contract

- Entry point: `python -m worker.outbox` (referenced in `pyproject.toml`).
- Input: envelopes persisted in the `outbox` table with `status='pending'`.
- Processing rules:
  - Acquire tenant-level locks to avoid double-execution.
  - Check guardrails (quiet hours, autonomy thresholds) before executing.
  - Use Tenacity for retries with a maximum attempt count configurable per risk tier.
  - Write results back to Supabase and emit audit log entries.
- Telemetry: latency histogram, attempt counter, failure counter, conflict counter, and
  dlq size metric.

### Outbox Worker Operations (planned)

- **CLI verbs** (`uv run python -m worker.outbox <command>`):
  - `start` – launch the continuous processing loop.
  - `status` – output queue depth, DLQ size, last processed envelope timestamp, and worker version.
  - `drain [--tenant <uuid>]` – process all pending envelopes (optionally scoped to a tenant) then exit.
  - `pause` / `resume` – toggle new-work intake while keeping the process alive.
  - `retry-dlq [--limit N]` – requeue envelopes from the DLQ with bounded concurrency.
- **Telemetry surface** (export via `/metrics` and OTLP):
  - `outbox_processed_total{tenant,status}` – counter with `status=success|retry|failed`.
  - `outbox_processing_duration_seconds` – histogram for envelope latency (p50/p95/p99).
  - `outbox_dlq_size{tenant}` – gauge capturing backlog.
  - `outbox_retry_total{tenant}` – counter for retry attempts.
  - `outbox_processed_per_minute` – derived Prometheus rate used in dashboards.
- **Health checks**:
  - `/healthz` – reports healthy when the worker loop is active and Supabase connectivity is verified.
  - `/metrics` – Prometheus endpoint exposing the telemetry above.
  - `status` exit code – non-zero when DLQ backlog exceeds SLO threshold (enables smoke checks in CI/CD).

## Interim Approach

Until Supabase is online, keep behaviour in memory but preserve the module boundaries
above. Design the interfaces (`CatalogService`, `OutboxRepository`, `AuditLogger`) so the
in-memory implementation can later be swapped for Supabase-backed versions without
touching the agent or UI.

Update this document whenever the data model changes or jobs are added.
