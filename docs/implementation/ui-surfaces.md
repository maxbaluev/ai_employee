# Building New UI Surfaces

**Status:** Implemented (scaffold + shared state demo) · In progress (productised
surfaces) · Planned (Supabase-backed data fetch)

Use this guide whenever you introduce a new customer-facing surface (Desk, Approvals,
Integrations, Activity & Safety). The patterns below codify what we learned from the
CopilotKit examples in `libs_docs/copilotkit_examples/` and the ADK integration docs in
`libs_docs/copilotkit_docs/adk/`.

## 1. Shape Shared State Intentionally

- Create a focused state slice per surface (e.g. `desk.queue`, `approvals.drafts`).
- Register the slice with `useCoAgent` and keep it serialisable; ADK replicates it across
  the Copilot runtime.
- Document the schema in `agent/state_contract.md` and reference the shared-state
  patterns in `libs_docs/copilotkit_docs/adk/shared-state/index.mdx` for bidirectional
  updates.
- Emit `StateDeltaEvent` updates whenever the agent mutates the slice so UI optimism and
  replay remain deterministic.

```tsx
"use client";

import { useCoAgent } from "@copilotkit/react-core";

type QueueItem = {
  id: string;
  title: string;
  evidence: string[];
  status: "pending" | "approved" | "rejected";
};

export function DeskState() {
  const { state } = useCoAgent<{ queue: QueueItem[] }>({
    name: "desk",
    initialState: { queue: [] },
  });

  return state.queue;
}
```

## 2. Compose the React Surface

- Place App Router routes under `src/app/(desk)/`, `src/app/(approvals)/`, etc. to keep
  layout boundaries clean.
- Use `CopilotSidebar`, `CopilotComposer`, and `CopilotTaskList` from `@copilotkit/react-ui`
  for consistency with the examples under `libs_docs/copilotkit_examples/`.
- Hydrate initial data from REST endpoints (Supabase once available) and merge subsequent
  updates from shared state.
- Lean on the generative UI primitives outlined in
  `libs_docs/copilotkit_docs/adk/generative-ui/index.mdx` for cards, tables, and inline
  summaries instead of bespoke components.

```tsx
import { CopilotSidebar } from "@copilotkit/react-ui";

export function DeskShell({ children }: { children: React.ReactNode }) {
  return (
    <CopilotSidebar className="max-w-sm border-l bg-slate-900">
      {children}
    </CopilotSidebar>
  );
}
```

## 3. Wire Human-in-the-Loop Controls

- Render JSON Schema forms for approvals using a generic renderer; see
  `docs/implementation/composio-tooling.md` for schema sourcing and
  `libs_docs/copilotkit_docs/adk/human-in-the-loop/index.mdx` for agent-side HITL
  patterns.
- When the agent requests confirmation (e.g. `requireHumanApproval` action), surface a
  modal or drawer that captures the operator's choice and emits a follow-up action to the
  agent.
- Log every approval decision through the shared state so callbacks and audit services
  remain the source of truth.

### Schema-driven Approval Forms

- Source the schema from the catalog (`tool_catalog.schema`) and map it into the generic
  form renderer (`JSONSchemaForm` or CopilotKit primitives). Reference
  `docs/schemas/approval-modal.json` for the canonical JSON Schema exposed via shared
  state (see Approval Flow Contract in `docs/implementation/frontend-shared-state.md`).
- Example scope escalation payload:

  ```json
  {
    "envelopeId": "env_123",
    "proposal": {
      "summary": "Request calendar scope upgrade",
      "evidence": ["Scope mismatch detected for Google Calendar"]
    },
    "requiredScopes": ["CALENDAR.READ", "CALENDAR.WRITE"],
    "approvalState": "pending"
  }
  ```

- Example evidence request payload:

  ```json
  {
    "envelopeId": "env_456",
    "proposal": {
      "summary": "Submit expense report",
      "evidence": ["Receipt.pdf", "Policy clause"]
    },
    "requiredScopes": [],
    "approvalState": "pending"
  }
  ```

- Wire the submit/cancel actions to the CopilotKit handler exactly as shown in the
  Playwright patterns (shared state test) to keep smoke coverage consistent.

## 4. UX & Accessibility Checklist

- Meet WCAG AA contrast for every card and button; copy CopilotKit's token palette where
  possible instead of inventing new colors.
- Keyboard navigation must stay intact—avoid trapping focus inside custom drawers.
- Provide inline help (hover or info icon) that links back to the relevant doc section
  whenever the action is non-trivial.
- Keep latency visible. The CopilotKit progress components in
  `libs_docs/copilotkit_examples/Dockerfile.ui` demos show how to wire spinners and
  transcripts without blocking the sidebar.

## 5. Verification Before Merge

- Add Playwright coverage for the new surface, following the patterns in
  `libs_docs/copilotkit_examples/`.
- Capture one screenshot per critical flow and attach it to the PR for asynchronous UX
  review.
- Run an exploratory pass in the browser (use the CLI browser tooling) to validate that
  shared state, actions, and HITL flows behave as expected.

Update this document as soon as the first production surface lands, including concrete
state schemas and Playwright snippets.
