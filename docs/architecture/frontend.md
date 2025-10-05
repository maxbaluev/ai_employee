# Frontend Architecture (Next.js + CopilotKit)

**Status:** Implemented (demo page + runtime bridge) · In progress (product surfaces)

## Current Implementation Snapshot

- **App router** – `src/app/layout.tsx` wires CopilotKit providers and global styles.
- **Demo surface** – `src/app/page.tsx` showcases three CopilotKit primitives:
  - `useCopilotAction` for invoking UI-affecting actions from the agent
  - `useCoAgent` for shared state (the `proverbs` list)
  - `CopilotSidebar` (from `@copilotkit/react-ui`) for the chat experience
- **Runtime endpoint** – `src/app/api/copilotkit/route.ts` creates a `CopilotRuntime`
  backed by an `HttpAgent("http://localhost:8000")` instance (see
  `libs_docs/copilotkit_docs/adk/quickstart.mdx`).

The sidebar defaults to always-open for easier debugging. Copy the ergonomics when
crafting future surfaces.

## Design Principles for Product Surfaces

1. **Schema-driven UI** – Render approval forms and tool arguments directly from
   Composio-provided JSON Schema. Avoid bespoke React forms; instead, use components such
   as React JSON Schema Form or internal wrappers.
2. **State-first rendering** – Every desk/approvals view should derive from shared state
   and the REST layer, not ad-hoc client state. The agent must emit the minimal state
   needed for instant UI optimism.
3. **No bespoke websockets** – CopilotKit already streams AGUI events. If additional
   streaming is needed, extend the runtime rather than introducing parallel channels.
4. **UX polish** – The Copilot sidebar is necessary but not sufficient. Provide
   evidence-first cards, edit affordances, and human override buttons in the main panel.

## Planned Work

| Surface | Purpose | Status |
|---------|---------|--------|
| Desk | Show queued proposals with evidence + quick actions | Planned |
| Approvals | Schema-driven edit + approve/reject flows | Planned |
| Integrations | Connected-account lifecycle + catalog inspection | Planned |
| Activity & Safety | Audit log, DLQ, guardrail controls | Planned |

Implementation recipes live in `docs/implementation/frontend-shared-state.md` and
`docs/implementation/ui-surfaces.md`.
