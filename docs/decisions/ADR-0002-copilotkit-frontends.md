# ADR-0002 — CopilotKit for All Operator Surfaces

- **Status:** Accepted
- **Date:** 2025-10-05
- **Decision Makers:** Platform Eng · Product · Design

## Context

Operator workflows need a conversational UI, shared state across the agent and browser,
and low-latency feedback when actions require review. The CopilotKit ADK quickstart and
examples bundled in `libs_docs/copilotkit_docs/adk/` and `libs_docs/copilotkit_examples/`
demonstrate production-ready primitives:

- `CopilotRuntime` + `HttpAgent` bridge Next.js routes to ADK agents with minimal glue
  code.
- `useCoAgent`, `useCopilotAction`, and `CopilotSidebar` ship first-class support for
  shared state streaming, UI-side actions, and human-in-the-loop prompts (`shared-state`,
  `human-in-the-loop`, `generative-ui` docs).
- Styling, accessibility, and keyboard behaviours are maintained by the upstream library
  and match the design language we expect to scale.

Rebuilding these primitives from scratch would fragment UX, duplicate maintenance, and
slow down product iteration.

## Decision

Adopt CopilotKit as the mandatory frontend interaction framework for every operator
surface. All web experiences must:

1. Use `CopilotRuntime` (`src/app/api/copilotkit/route.ts`) to connect to the ADK agent.
2. Render conversation and shared state via CopilotKit components and hooks (`useCoAgent`,
   `useCopilotAction`, `CopilotSidebar`, `CopilotTaskList`).
3. Implement human-in-the-loop review flows with CopilotKit actions, mirroring the
   patterns in `libs_docs/copilotkit_docs/adk/human-in-the-loop/`.
4. Extend styling and theming by overriding CopilotKit tokens rather than forking
   components.

## Consequences

- **Positive**
  - Shared state, actions, and HITL flows remain consistent with the ADK runtime.
  - Faster surface delivery by composing existing CopilotKit widgets instead of writing
    bespoke chat or approval components.
  - Accessibility and keyboard support inherit upstream fixes without additional work.
- **Risks**
  - Upstream API changes could break our surfaces; we must track release notes.
  - Custom UX beyond CopilotKit's primitives may require extension points or upstream
    contributions.
  - Tight coupling to React; non-React shells would need a new ADR.

## Follow-ups

1. Establish a version pin and update playbook for CopilotKit (`docs/operations/run-and-observe.md`).
2. Document theming overrides and shared layout contracts in
   `docs/implementation/frontend-shared-state.md` and `docs/implementation/ui-surfaces.md`.
3. Add a regression checklist to Playwright smoke tests validating the sidebar and HITL
   flows whenever CopilotKit is upgraded.
