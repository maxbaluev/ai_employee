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

## Shared Schema Definitions

Canonical schemas live in `docs/schemas/` (add them as they are finalised). Reference
them from both the agent and UI layers to avoid drift.

- `docs/schemas/desk-state.json` (planned):

  ```json
  {
    "$id": "desk-state",
    "type": "object",
    "required": ["queue", "lastUpdated"],
    "properties": {
      "queue": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["id", "title", "status"],
          "properties": {
            "id": { "type": "string" },
            "title": { "type": "string" },
            "status": { "enum": ["pending", "approved", "rejected"] },
            "evidence": { "type": "array", "items": { "type": "string" } },
            "highlighted": { "type": "boolean", "default": false }
          }
        }
      },
      "lastUpdated": { "type": "string", "format": "date-time" }
    }
  }
  ```

- `docs/schemas/approval-modal.json` (planned):

  ```json
  {
    "$id": "approval-modal",
    "type": "object",
    "required": ["envelopeId", "proposal", "requiredScopes"],
    "properties": {
      "envelopeId": { "type": "string" },
      "proposal": {
        "type": "object",
        "required": ["summary", "evidence"],
        "properties": {
          "summary": { "type": "string" },
          "evidence": { "type": "array", "items": { "type": "string" } }
        }
      },
      "requiredScopes": { "type": "array", "items": { "type": "string" } },
      "approvalState": { "enum": ["pending", "authorized", "denied"] }
    }
  }
  ```

- `docs/schemas/guardrail-state.json` (planned). The UI should expose
  `state.trust.score` when available (and optional `state.trust.source`) so
  `agent/callbacks/guardrails.enforce_trust_threshold` can evaluate it. The
  guardrail derives `allowed` based on these inputs:

  ```json
  {
    "$id": "guardrail-state",
    "type": "object",
    "properties": {
      "quietHours": {
        "type": "object",
        "required": ["allowed", "message"],
        "properties": {
          "allowed": { "type": "boolean" },
          "message": { "type": "string" },
          "configured": { "type": "boolean" },
          "window": { "type": "string" },
          "currentTime": { "type": "string" }
        }
      },
      "trust": {
        "type": "object",
        "required": ["allowed"],
        "properties": {
          "allowed": { "type": "boolean" },
          "score": { "type": "number" },
          "threshold": { "type": "number" },
          "source": { "type": "string" },
          "missingSignal": { "type": "boolean" },
          "message": { "type": "string" }
        }
      },
      "scopeValidation": {
        "type": "object",
        "required": ["allowed", "missingScopes", "requestedScopes", "enabledScopes"],
        "properties": {
          "allowed": { "type": "boolean" },
          "missingScopes": {
            "type": "array",
            "items": { "type": "string" }
          },
          "requestedScopes": {
            "type": "array",
            "items": { "type": "string" }
          },
          "enabledScopes": {
            "type": "array",
            "items": { "type": "string" }
          },
          "message": { "type": "string" }
        }
      },
      "evidence": {
        "type": "object",
        "required": ["required", "allowed", "missingEvidence"],
        "properties": {
          "required": { "type": "boolean" },
          "allowed": { "type": "boolean" },
          "missingEvidence": { "type": "array", "items": { "type": "string" } },
          "message": { "type": "string" }
        }
      }
    }
  }
  ```

Link these schemas from `agent/schemas/` or shared TypeScript types once available so
schema changes propagate consistently.

## Testing

- Add Playwright smoke tests for every new surface once the UI stabilises.
- Unit-test action handlers to ensure they do not throw when required fields are missing.
- Use fixtures that stub agent responses (`serverHandlers` or MSW) so tests remain
  deterministic.

## Playwright Smoke Patterns

Cover the core shared-state flows with lightweight smoke tests. Mock CopilotKit/agent
responses via MSW or the Playwright request route fixtures.

- **Sidebar loads** – ensure the CoAgent sidebar renders and connects.

  ```ts
  test('sidebar bootstraps', async ({ page }) => {
    await page.route('**/api/copilotkit/**', mockHandshake);
    await page.goto('/');
    await expect(page.getByTestId('copilot-sidebar')).toBeVisible();
  });
  ```

- **Desk queue render** – verify queue items from shared state surface correctly.

  ```ts
  test('desk renders queue items', async ({ page }) => {
    await withDeskState(page, { queue: [{ id: '1', title: 'Foo', status: 'pending' }] });
    await expect(page.getByText('Foo')).toBeVisible();
  });
  ```

- **Approval submit/cancel** – simulate approving and cancelling schema-driven forms.

  ```ts
  test('approval submit & cancel', async ({ page }) => {
    await withApprovalModal(page);
    await page.getByRole('button', { name: 'Approve' }).click();
    await expect(mockApprovalEndpoint).toHaveBeenCalled();
    await withApprovalModal(page);
    await page.getByRole('button', { name: 'Cancel' }).click();
    await expect(page.getByText('Approval required')).not.toBeVisible();
  });
  ```

- **Guardrail rejection banner** – ensure guardrail blocks display and halt actions.

  ```ts
  test('trust guardrail banner', async ({ page }) => {
    await withGuardrailState(page, { trust: { allowed: false, score: 0.1 } });
    await expect(page.getByText('Trust threshold')).toBeVisible();
  });
  ```

- **State delta replay** – replay `StateDeltaEvent`s and ensure UI updates.

  ```ts
  test('state delta applies', async ({ page }) => {
    const { emitDelta } = await mountDesk(page);
    emitDelta({ queue: [{ id: '2', title: 'Bar', status: 'pending' }] });
    await expect(page.getByText('Bar')).toBeVisible();
  });
  ```

Use shared helpers (`withDeskState`, `withApprovalModal`, etc.) to centralise fixtures
and keep scenarios fast. Update this list whenever new shared-state surfaces ship.

For more examples explore `libs_docs/copilotkit_examples/` and `libs_docs/copilotkit_docs/adk/`.
