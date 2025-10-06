
# Layered TODO Tracker (Universal PRD)

Status: Updated October 6, 2025 · Composio-only · One executor · Supabase-only analytics

This tracker mirrors the canonical PRD (`docs/prd/universal-ai-employee-prd.md`). Keep
items checked only when code + docs + tests have landed together. Reference `libs_docs/`
patterns for ADK, CopilotKit, and Composio.

## 1. Getting Started & Toolchain

- [x] Document mise + uv bootstrap directly in `docs/getting-started/setup.md`; include
      `mise doctor` preflight and troubleshoot appendix. (`docs/getting-started/setup.md`,
      `docs/operations/run-and-observe.md`)
- [x] Added Supabase credential bootstrap guidance. (`docs/getting-started/setup.md#supabase-credential-bootstrap`)

## 2. Architecture (Frontend · Agent · Composio · Data)

- [x] Replace the Proverbs agent diagram with the modular blueprint now that coordinator scaffolding ships. (`docs/architecture/agent-control-plane.md`, `AGENTS.md`)
- [x] Embed the Composio catalog → envelope → Outbox sequence diagram using
      `libs_docs/composio_next/python/providers/google_adk/google_adk_demo.py` as the source. (`docs/architecture/composio-execution.md`)
- [x] Add Supabase ERD and migration conventions. (`docs/architecture/data-roadmap.md`, `docs/architecture/data-model.md`)
- [x] Update frontend architecture to include planned Desk/Approvals route layout and
      state contracts. (`docs/architecture/frontend.md`, `docs/implementation/frontend-shared-state.md`)

## 3. Implementation Guides

- [x] Provide guardrail module docs + pytest snippets (quiet hours, trust, scopes,
      evidence). (`docs/implementation/backend-callbacks.md`)
- [x] Draft Composio OAuth + scope handling walkthrough. (`docs/implementation/composio-tooling.md`)
- [x] Add Desk/Approvals UI scaffolds that map JSON Schema → form components using
      CopilotKit patterns. (`docs/implementation/ui-surfaces.md`, `libs_docs/copilotkit_docs/adk/`)

## 4. Data & Workers (Universal Action Envelope)

- [x] Check in Supabase migration scripts + seeds and document apply steps. (`docs/architecture/data-roadmap.md`, `db/migrations/001_init.sql`, `db/seeds/000_demo_tenant.sql`, `db/README.md`)
- [x] Define Supabase tables + Outbox worker operations (CLI, telemetry, health). (`docs/architecture/data-roadmap.md`, `docs/operations/runbooks/outbox-recovery.md`)
- [x] Document DLQ replay process end-to-end including audit expectations. (`docs/operations/runbooks/outbox-recovery.md`, `docs/governance/security-and-guardrails.md`)
- [ ] Create `db/migrations/002_vnext_universal_action_envelope.sql` implementing:
      employees, program_assignments, tasks, actions, tool_policies, trust_ledger,
      signals; enhance tool_catalog and outbox; indexes + views; RLS. (See agent plan)
- [ ] Implement Supabase Cron jobs: `catalog-sync-nightly`, `trickle-refresh-hourly`,
      `embedding-reindex-nightly` and document Edge Functions payloads.
- [ ] Wire automated migration tooling (Supabase CLI) into CI/CD.

## 5. Frontend Surfaces & Shared State (Five Surfaces)

- [x] Publish shared state JSON schemas (Desk, Approvals) + link to schema files. (`docs/implementation/frontend-shared-state.md`, `AGENTS.md`, `docs/schemas/`)
- [x] Add Playwright smoke patterns checklist. (`docs/implementation/frontend-shared-state.md`)
- [ ] Document schema-driven approval forms with live JSON Schema examples for
      Slack, Gmail, Notion, HubSpot, Zendesk, Calendar. (`docs/implementation/ui-surfaces.md`)
- [ ] Implement “Approve all low‑risk” flow and copy; a11y shortcuts. (`desk`)
- [ ] Integrations: policy toggles, JIT connect/scope modal, connection health badges.
- [ ] Activity & Safety: timeline, DLQ requeue, rate‑limit badges, Pause/Undo.

## 6. Observability & Operations (Supabase-only)

- [x] Document `/metrics` endpoint + collector configuration; update metric catalog. (`docs/operations/run-and-observe.md`, `docs/references/observability.md`)
- [x] Record dashboard placeholders and PromQL queries until real screenshots exist. (`docs/references/observability.md`)
- [x] Document Supabase Cron scheduling approach across architecture and operations docs; replace all APScheduler references. (`docs/architecture/data-roadmap.md`, `docs/architecture/composio-execution.md`, `docs/operations/run-and-observe.md`, `AGENTS.md`)
- [x] Expand incident runbooks with real postmortems and comms templates. (`docs/operations/runbooks/`, `docs/operations/runbooks/postmortems/outbox-dlq-2025-09-18.md`)
- [x] Wire Composio OAuth env vars once backend settings are ready. (`docs/implementation/composio-tooling.md`, `agent/services/settings.py`)

## 7. Governance & Documentation

- [x] Add guardrail PR checklist + doc audit log guidance. (`docs/governance/security-and-guardrails.md`, `docs/governance/ownership-and-evergreen.md`)
- [x] Append TODO references to PR templates / CONTRIBUTING once those docs exist.

---

### Next Up

1. Generate example Reader Kernel configs and Value Program mappings under
   `docs/references/` (six Composio tools) to bootstrap UI.
2. Add Playwright test checklist tied to acceptance criteria in the PRD.

Update this tracker as milestones land. Remove completed items only when the associated
code, documentation, and tests are merged.
