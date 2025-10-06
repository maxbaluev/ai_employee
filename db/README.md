# Database Scaffolding

This directory holds the Supabase/Postgres schema that backs the agent control plane.

## Migrations

- `migrations/001_init.sql` mirrors the draft schema described in
  `docs/architecture/data-roadmap.md`. It enables `pgcrypto` to support
  `gen_random_uuid()`; ensure the extension is available in your environment. Apply the
  migration using your preferred tooling, e.g.:

  ```bash
  supabase db execute --file db/migrations/001_init.sql
  ```

  or run it manually inside `psql` while iterating locally.
- Future migrations should be added with incrementing numeric prefixes.

## Seeds

- `seeds/000_placeholder.sql` exists as a slot for fixture data once we define tenant
  bootstrap flows.
- Keep seed scripts idempotent so they can be re-run in ephemeral environments.

See `docs/architecture/data-roadmap.md` for column-level details and RLS notes.
