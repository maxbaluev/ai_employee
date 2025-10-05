# Functional Requirements (Final)

Mapped to architecture (`docs/arch.md`), UX (`docs/ux.md`), and implementation roadmap (`docs/todo.md`). Each requirement references relevant libraries/features for validation.

## 1. Onboarding & Configuration

- **FR-001 Value Objectives**
  - Must capture (name, KPI metric, target delta, horizon) before plans run.
  - API: `POST /objectives`; stored under tenant with RLS.
  - UI reflects objective chip immediately via `useCoAgent` state.

- **FR-002 Guardrails**
  - Configure quiet hours, allowed channels/tools, tone presets, autonomy baseline per tenant and employee.
  - Stored in `guardrails` table (JSON); enforced in ADK callbacks and Outbox preflight.

- **FR-003 Composio Connection Lifecycle**
  - Initiate via `composio.connected_accounts.initiate`, wait for activation, persist account ID, status transitions (pending/active/disabled/error).
  - `GET /tools` returns discovered tools + statuses; Integrations UI mirrors.

## 2. Planning & Evidence

- **FR-010 Warm Scan**
  - Within two minutes of connection, APScheduler executes configured reader kernels (YAML) using `composio.tools.execute`. Signals saved with `updated_at` timestamps.
  - Evidence cards appear on Desk referencing Signals and tool slugs.

- **FR-011 Trickle Refresh**
  - Scheduler runs every 30–60 minutes, per toolkit category. Honors rate buckets persisted in catalog; backlog gracefully handled.
  - Missed cycles generate Activity banner + metric (`scheduler_runs_total` failure).

- **FR-012 Plan Assembly**
  - ADK agent composes action envelopes with `tool.slug`, `args`, `evidence_ref`, `objective_id`, `risk`.
  - Narration streamed through AGUI; proposals stored in `tasks` table.

## 3. Approvals & Execution

- **FR-020 Schema-Driven Edit**
  - UI generates forms directly from `tool.json_schema`. Required fields enforced client and server side.
  - Backend validates against schema during `POST /approvals` to prevent drift.

- **FR-021 Approval Workflow**
  - Decisions: approve, edit (approve with changes), reject, bulk approve low-risk.
  - Outbox only enqueues `approval_state=granted`. Audit log entry created for each decision.

- **FR-022 Outbox Execution**
  - Worker dequeues, checks quiet hours/DNC, ensures connected account active, and calls `composio.tools.execute` with `external_id` for idempotency.
  - Provider conflict (409) recorded as success with note `status=conflict`.
  - Failures retried with Tenacity backoff; after threshold, moved to DLQ.

- **FR-023 JIT Scope Upgrade**
  - If `tool.requires_scope` missing, UI prompts using data from `toolkits.get_connected_account_initiation_fields`.
  - After enabling, original action auto-executes exactly once; audit logs include enabling event + action result.

## 4. Multi-Employee & Trust

- **FR-030 Roster Management**
  - `POST /employees` (role, timezone, autonomy). `PATCH /employees/{id}` for pause/resume.
  - Drag-and-drop reassign updates `tasks.employee_id`; ADK state sync ensures UI updates without reload.

- **FR-031 Assignments Drawer**
  - Program capacities/priority stored in `program_assignments`. Planner respects capacity when selecting cards.

- **FR-032 Trust Gates**
  - Trust score computed daily (approved w/out edits, edits, rejections, errors). Default thresholds: <0.6 Propose, 0.6–0.8 Assist, >0.8 Trusted.
  - Auto approvals logged with flag; UI highlights card as auto-run.

## 5. Observability & Audit

- **FR-040 Activity Timeline**
  - `GET /activity` paginates Outbox events with provider IDs, statuses, errors. Supports filter by employee/tool/date.

- **FR-041 Audit Trail**
  - Append-only log capturing objectives changes, approvals, scope toggles, Outbox results, trust recalculations. Exposed via `GET /audit` with RLS.

- **FR-042 Metrics & Traces**
  - Emit metrics listed in `docs/observability.md` using OTLP/Prometheus. Each critical flow (plan run, approval, delivery) produces trace ID.

## 6. Security & Compliance

- **FR-050 Tenant Isolation (RLS)**
  - All queries validated by automated tests; cross-tenant access returns 403.

- **FR-051 Guardrails Enforcement**
  - Quiet hours, DNC, disallowed tool categories prevent Outbox execution; overrides require manager approval + audit entry.

- **FR-052 Secrets & Logging**
  - No plaintext secrets in logs; hashed per `docs/logging-privacy.md`. `.env.example` documents required vars.

## 7. Extensibility Hooks

- **FR-060 Triggers (Future)**
  - System prepared for Composio triggers ingestion; placeholders ensure we can append to tasks queue without redesign.

- **FR-061 Multi-Agent Support**
  - CopilotRuntime config allows registering additional agents (e.g., compliance reviewer) without refactoring UI; ensure `agents` map in `/api/copilotkit` configurable.

## 8. Testing Expectations

- Unit tests for planner callbacks, guardrail enforcement, Outbox idempotency.
- Integration tests hitting Composio staging (mock) to validate schema-driven forms + execute flows.
- End-to-end tests using Playwright (Desk approvals, JIT scope, Outbox timeline).
- Security tests verifying RLS and quiet hour safeguards.

Any deviation from these requirements must produce an ADR before implementation.
