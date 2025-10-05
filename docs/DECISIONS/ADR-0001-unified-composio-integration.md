# ADR-0001 — Composio as Sole Tool Provider

- **Status:** Accepted
- **Date:** 2025-03-10
- **Decision Makers:** Platform Eng + Product + Security

## Context

We require a single integration surface that provides consistent schemas, scopes, and rate limits across diverse SaaS tools. Google ADK agents expect tools surfaced via MCP, and CopilotKit can render schema-based forms without per-tool UI code. Maintaining custom connectors would fracture maintenance and risk inconsistent guardrails.

## Decision

Adopt Composio as the exclusive MCP/tool provider for the AI employee. All read/write capabilities must be sourced through Composio toolkits, fetched at runtime via `composio.tools.get` (Python) and persisted in a tenant-specific catalog.

## Consequences

- **Positive:**
  - Zero per-tool code; schema-driven UI and validation.
  - Centralized scope/risk metadata enabling JIT upgrades and policy enforcement.
  - Simplifies Outbox implementation (single execution path `mcp.exec`).
- **Negative / Risks:**
  - Vendor dependency; outages or schema changes affect entire platform.
  - Tool coverage limited to Composio catalog; customer-specific APIs require future ADR.
  - Need proactive schema-drift monitoring to avoid broken forms.

## Follow-ups

1. Implement automated catalog sync with drift alerts (`docs/roadmap.md` Sprint 1).
2. Define contingency runbook for Composio outage (`docs/runbooks` future).
3. Evaluate redundancy options (e.g., fallback read caches) before GA.
