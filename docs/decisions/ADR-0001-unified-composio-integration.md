# ADR-0001 — Composio as Sole Tool Provider

- **Status:** Accepted
- **Date:** 2025-03-10
- **Decision Makers:** Platform Eng · Product · Security

## Context

We require a single execution surface that provides consistent schemas, scopes, and rate
limits across diverse SaaS tools. Google ADK agents expect tools surfaced via MCP, and
CopilotKit can render schema-based forms without per-tool UI code. Maintaining custom
connectors would fracture maintenance and risk inconsistent guardrails.

## Decision

Adopt Composio as the exclusive MCP/tool provider for the AI employee. All read/write
capabilities must be sourced through Composio toolkits, fetched at runtime via
`composio.tools.get` and executed with `composio.tools.execute`. Persist metadata in the
platform catalog per tenant.

## Consequences

- **Positive**
  - Zero per-tool code; schema-driven UI and validation.
  - Centralised scope/risk metadata enabling JIT upgrades and policy enforcement.
  - Simplifies Outbox implementation (single execution path).
- **Risks**
  - Vendor dependency; outages or schema changes affect the entire platform.
  - Tool coverage limited to the Composio catalog; customer-specific APIs require a new
    ADR.
  - Requires proactive schema-drift monitoring to avoid broken forms.

## Follow-ups

1. Implement automated catalog sync with drift alerts (`docs/architecture/composio-execution.md`).
2. Define contingency plan for Composio outages (`docs/operations/runbooks/composio-outage.md`).
3. Evaluate redundancy options (read caches, alternate providers) before GA.
