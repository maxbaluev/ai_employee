# ADR-0004 — Universal Action Envelope (`mcp.exec`)

- **Status:** Accepted
- **Date:** 2025-10-06
- **Decision Makers:** Platform Eng · Product · Security

## Context

We need a single, durable contract for all writes that keeps the UI schema-driven,
centralizes guardrails, and simplifies execution. Composio MCP provides uniform tool
schemas and a single execution API. Maintaining multiple write paths would fragment
safety checks and increase drift.

## Decision

Adopt a universal Action Envelope with `type = mcp.exec` as the only write contract.
Agents propose envelopes; the Outbox worker executes them via `composio.tools.execute`.
UI renders previews from Composio JSON Schemas. Idempotency is enforced by `external_id`.

## Consequences

- **Positive:** One executor, one schema, easier approvals/undo, consistent audits.
- **Risks:** All writes depend on Composio availability; requires robust DLQ/retry.
- **Mitigations:** Conflict-deduping, jittered retries, read-only degradation mode.

## References

- Contract: `docs/architecture/universal-action-envelope.md`
- Schema: `docs/schemas/action-envelope.json`
- PRD: `docs/prd/universal-ai-employee-prd.md`

