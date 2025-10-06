# Composio Tooling Integration Guide

**Status:** Implemented (control plane + Supabase-backed worker) · In progress (OAuth UX &
advanced catalog sync)

This guide documents how the Python control plane wires Composio today and what is still
outstanding. It draws on the vendor examples vendored under `libs_docs/` so you can map
behaviour back to upstream SDK guidance.

## 1. Bootstrap the Client

- Runtime settings live in `agent/services/settings.py` (`AppSettings`). The control
  plane reads `COMPOSIO_API_KEY`, optional OAuth credentials, and default toolkits from
  those settings.
- A Composio client is instantiated via `Composio(provider=GoogleAdkProvider(), api_key=…)`.
  See `_resolve_in_memory_catalog` and `_sync_catalog_from_composio` inside
  `agent/agents/control_plane.py` for the canonical pattern.
- Reference implementation: `libs_docs/composio_next/python/providers/google_adk/google_adk_demo.py`.

```python
from composio import Composio
from composio_google_adk import GoogleAdkProvider

def build_composio(settings: AppSettings) -> Composio:
    return Composio(
        provider=GoogleAdkProvider(),
        api_key=settings.composio_api_key,
    )
```

## 2. Catalog Discovery & Persistence

- `agent/services/catalog.py` exposes `ComposioCatalogService` for live discovery and
  `SupabaseCatalogService` for persistence. When Supabase credentials are present, the
  control plane hydrates the remote catalog and upserts rows via
  `catalog_service.sync_entries()` before serving traffic.
- Schema and scope metadata flow into the Desk shared state so the frontend can render
  schema-driven approval forms. See `DeskBlueprint.register_envelope()` for how the queue
  absorbs those entries.
- Supabase Cron jobs (documented in `docs/operations/run-and-observe.md`) should trigger
  nightly syncs using the SQL patterns from `libs_docs/supabase/llms_docs.txt`
  (`cron.schedule`, `net.http_post`).

## 3. Connected Accounts & OAuth (In Progress)

- Composio’s hosted connection URLs come from
  `composio.accounts.create_connection_link(...)`. Emit the link through shared state so
  the UI can open it, capture the state token, and handle the callback with
  `accounts.exchange_code`.
- Persist the resulting `connected_account_id`, granted scopes, and metadata in Supabase
  (`connected_accounts` table) and emit audit logs via `StructlogAuditLogger` or
  `SupabaseAuditLogger`.
- The UI surfaces (`docs/implementation/ui-surfaces.md`) will reference this data when
  rendering approval flows. Until then, keep the API + worker insulated from missing
  accounts by short-circuiting envelopes when a required account is absent.

## 4. Scope Handling & Guardrails

- `agent/guardrails/scopes.py` checks `requested_scopes` vs `enabled_scopes` before the
  model call. Populate shared state in `DeskBlueprint.register_envelope()` so the guard
  has enough context.
- When a scope upgrade is needed, enqueue an approval envelope with the catalog schema.
  The refusal copy templates in `libs_docs/adk/full_llm_docs.txt` keep the user-facing
  tone consistent.
- Store scope grants per `connected_account_id` in Supabase so both the agent and worker
  can validate permissions without round-trips to Composio.

## 5. ADK Tooling & Enqueue Flow

- Rather than exposing every Composio tool directly to the LLM, the control plane wraps
  them in a single `enqueue_envelope` tool. This keeps approval gating in one place and
  aligns with the desk workflow.
- Inside `_build_enqueue_envelope_tool` we:
  1. Look up the catalog entry (`CatalogService.get_tool`).
  2. Validate arguments against the stored JSON Schema (`ToolCatalogEntry.validate_arguments`).
  3. Normalise payloads to `Envelope` objects and queue them via `OutboxService.enqueue`.
  4. Emit audit events and update shared state.
- If you need direct Composio function tools (e.g. for low-risk actions), leverage the
  conversion helpers in `GoogleAdkProvider` (`libs_docs/composio_next/python/providers/google_adk/`).

## 6. Execution & Worker Semantics

- `worker/outbox.py` polls Supabase for pending envelopes, executes them with
  `composio.tools.execute`, and manages retries with Tenacity. Provider conflicts (HTTP
  409) short-circuit into the `conflict` status; other failures can be retried or moved
  to DLQ.
- Metadata from successful runs is persisted back to Supabase and surfaced to the UI via
  `StateDeltaEvent`s (see `agent/callbacks/after.py`).
- Follow the Supabase patterns in `libs_docs/supabase/llms_docs.txt` when extending DLQ
  reporting or adding telemetry around execution latency.

## 7. Testing Strategy

- Unit-test callbacks and guardrails with the in-memory services (`InMemoryCatalogService`,
  `InMemoryOutboxService`) and Composio stubs. The ADK guidance in
  `libs_docs/adk/full_llm_docs.txt` includes recommended doubles for `CallbackContext`.
- Smoke-test catalog sync + Supabase persistence by running `pnpm run dev:agent` with
  Supabase credentials configured; the agent will upsert catalog entries on boot.
- Before shipping new toolkits, add Playwright coverage in
  `libs_docs/copilotkit_examples/tests` to ensure approvals render schema-driven forms
  correctly.

Keep this guide current: reference upstream docs when SDK behaviour changes and update
status once OAuth surfaces and advanced catalog sync are live.
