# ADR-0003 — Google ADK as the Agent Runtime

- **Status:** Accepted
- **Date:** 2025-10-05
- **Decision Makers:** Platform Eng · Product · Security
`
## Context

The AI employee needs a deterministic runtime that can coordinate multi-step plans,
stream state to the UI, and support human checkpoints. The Google Agent Development Kit
(`libs_docs/adk/full_llm_docs.txt`) provides:

- First-class multi-agent orchestration (`LlmAgent`, coordinator/sub-agent patterns).
- Structured shared state storage that the AG-UI bridge streams to CopilotKit.
- Callback hooks (`before_model_modifier`, `after_model_modifier`) for injecting guardrails
  and logging.
- Official tooling to expose agents as FastAPI apps via `ag_ui_adk` (`libs_docs/copilotkit_docs/adk/quickstart.mdx`).

Alternatives (custom LangChain stack, bespoke FastAPI) would recreate this feature set at
the cost of reliability and vendor support.

## Decision

Standardise on Google ADK for orchestrating all server-side agent logic. Concretely we
will:

1. Define every production agent by composing ADK `LlmAgent` instances and the provided
   orchestration primitives.
2. Expose agents through `ag_ui_adk.ADKAgent` and `add_adk_fastapi_endpoint` so the
   CopilotKit runtime can communicate without custom protocols.
3. Implement business logic, guardrails, and telemetry inside ADK callbacks and services
   rather than forking request handling.
4. Track ADK release cadence (weekly per docs) and pin versions in `pyproject.toml` to
   avoid breaking changes.

## Consequences

- **Positive**
  - Shared state and HITL semantics align with CopilotKit expectations out of the box.
  - Multi-agent expansion (specialist agents per workflow) becomes a configuration change
    rather than a refactor.
  - Vendor documentation and samples reduce onboarding time for new contributors.
- **Risks**
  - Dependency on Google's roadmap; if ADK stagnates we may need to migrate.
  - Runtime assumes Python; polyglot agents require language-specific bridges.
  - Callback misuse can introduce tight coupling between prompts and guardrails—code review
    must enforce separation of concerns.

## Follow-ups

1. Refactor `agent/` into modular packages (`agents/`, `callbacks/`, `services/`) per
   `docs/implementation/backend-callbacks.md`.
2. Draft a migration doc for introducing additional specialised agents (desk, approvals)
   using ADK sub-agent patterns.
3. Add contract tests that mock Composio while exercising ADK callbacks to validate guardrail
   behaviour (`docs/implementation/composio-tooling.md`).
