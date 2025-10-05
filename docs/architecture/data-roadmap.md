# Data & Roadmap

**Status:** Planned (no persistent storage implemented yet)

Although `pyproject.toml` already lists database- and scheduling-related dependencies,
the repository currently operates entirely in memory. This document anchors the future
state so we build a consistent control plane as we add persistence.

## Target Supabase Schema (Draft)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `tenants` | Tenant metadata | `id (uuid)`, `name`, `plan`, timestamps |
| `objectives` | Value objectives per tenant | `id`, `tenant_id`, `metric`, `target`, `horizon` |
| `guardrails` | Quiet hours, allowed toolkits, tone | `tenant_id`, `config (jsonb)` |
| `connected_accounts` | Composio account linkage | `id`, `tenant_id`, `provider`, `status`, `scopes` |
| `tool_catalog` | Cached Composio schema | `tenant_id`, `tool_slug`, `json_schema`, `risk`, `version` |
| `tasks` | Planned actions | `id`, `tenant_id`, `objective_id`, `state`, `evidence` |
| `outbox` | Approved envelopes awaiting execution | `id`, `tenant_id`, `envelope`, `status`, `attempts`, `external_id` |
| `audit_log` | Append-only event log | `id`, `tenant_id`, `category`, `payload`, `actor` |

All tables must enforce Row-Level Security. Migration tooling can live inside the agent
package or a dedicated `db/` directory.

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

## Interim Approach

Until Supabase is online, keep behaviour in memory but preserve the module boundaries
above. Design the interfaces (`CatalogService`, `OutboxRepository`, `AuditLogger`) so the
in-memory implementation can later be swapped for Supabase-backed versions without
touching the agent or UI.

Update this document whenever the data model changes or jobs are added.
