# Database Scaffolding

This directory holds the Supabase/Postgres schema that backs the agent control plane.

## Migrations

- `migrations/001_init.sql` mirrors the schema described in
  `docs/architecture/data-roadmap.md`. It enables `pgcrypto` and installs helper
  functions (`current_tenant_id_uuid`, `set_updated_at`) alongside Row Level Security
  (RLS) policies for every tenant-scoped table. Apply the migration using your
  preferred tooling, e.g.:

  ```bash
  supabase db execute --file db/migrations/001_init.sql
  ```

  or run it manually inside `psql` while iterating locally.
- Future migrations should be added with incrementing numeric prefixes.

## Seeds

- `seeds/000_demo_tenant.sql` provisions a demo tenant, objectives, guardrails, catalog
  entries, a sample outbox envelope, and an audit log entry. Apply it after the initial
  migration to mirror the behaviour exercised by the Python in-memory defaults:

  ```bash
  supabase db execute --file db/seeds/000_demo_tenant.sql
  ```

- Keep seed scripts idempotent so they can be re-run in ephemeral environments.

- RLS policies default to `service_role` for mutating operations. The agent and worker
  services should use the Supabase service key; the frontend may rely on tenant-scoped
  select policies if direct Supabase queries are ever required.

See `docs/architecture/data-roadmap.md` for column-level details and RLS notes.
