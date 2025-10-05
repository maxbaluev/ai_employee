# Frontend Shared State & Actions

**Status:** Implemented (demo) · In progress (product surfaces)

## Patterns to Reuse

1. **Single source of truth** – Use `useCoAgent<State>()` to subscribe to the agent’s
   state. Do not maintain duplicate React state for the same data.
2. **Schema-driven forms** – Render Composio JSON Schema using a generic form renderer.
   Persist edits back through the approval API and emit `StateDeltaEvent` from the agent
   so the UI stays consistent.
3. **Frontend actions for UX polish** – Use `useCopilotAction` to let the agent request
   UI-only effects (e.g. highlighting cards, pre-filling filters). Keep these actions
   idempotent and reversible.

## Example Template

```tsx
"use client";

import { useCoAgent, useCopilotAction } from "@copilotkit/react-core";
import { DeskCard } from "@/components/desk-card";

type DeskState = {
  queue: Array<{
    id: string;
    title: string;
    evidence: string[];
    status: "pending" | "approved" | "rejected";
  }>;
};

export function DeskView() {
  const { state, setState } = useCoAgent<DeskState>({
    name: "desk",
    initialState: { queue: [] },
  });

  useCopilotAction({
    name: "highlightCard",
    parameters: [{ name: "taskId", type: "string", required: true }],
    handler: ({ taskId }) => setState((prev) => ({
      ...prev,
      queue: prev.queue.map((item) => ({
        ...item,
        highlighted: item.id === taskId,
      })),
    })),
  });

  return state.queue.map((item) => (
    <DeskCard key={item.id} task={item} onApprove={...} onReject={...} />
  ));
}
```

## State Contract

- Keep state serialisable; ADK stores it as JSON.
- Include minimal derived data (e.g. counts) to keep prompts lean.
- Document every state field in the agent module so reviewers understand the coupling.

## Testing

- Add Playwright smoke tests for every new surface once the UI stabilises.
- Unit-test action handlers to ensure they do not throw when required fields are missing.

For more examples explore `libs_docs/copilotkit_examples/` and `libs_docs/copilotkit_docs/adk/`.
