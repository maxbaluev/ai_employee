# Building New UI Surfaces

**Status:** Implemented (desk + approvals scaffolds, schema-driven forms) · In progress
(productised surfaces)

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
- Emit `StateDeltaEvent` updates whenever the agent mutates the slice. The control plane
  now reassigns the `desk`, `approvalModal`, `guardrails`, and `outbox` keys so the AGUI
  bridge emits JSON Patch deltas automatically.

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

- Place App Router routes under `src/app/(workspace)/desk`, `src/app/(workspace)/approvals`, etc. to keep
  layout boundaries clean.
- Use `CopilotSidebar`, `CopilotComposer`, and `CopilotTaskList` from `@copilotkit/react-ui`
  for consistency with the examples under `libs_docs/copilotkit_examples/`.
- Hydrate initial data from Supabase-backed REST endpoints and merge subsequent updates
  from shared state.
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

### Desk Surface Scaffold

- Render the main queue inside `src/app/(workspace)/desk/page.tsx`. Combine shared state with
  any initial data fetched on the server (Supabase).
- Keep actions idempotent; the agent will replay `StateDeltaEvent`s if the user reloads
  the page.

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

export function DeskPage() {
  const { state, setState } = useCoAgent<DeskState>({
    name: "desk",
    initialState: { queue: [] },
  });

  useCopilotAction({
    name: "desk:updateStatus",
    parameters: [{ name: "id", type: "string", required: true }, { name: "status", type: "string", required: true }],
    handler: ({ id, status }) =>
      setState((prev) => ({
        ...prev,
        queue: prev.queue.map((item) =>
          item.id === id ? { ...item, status: status as DeskState["queue"][number]["status"] } : item,
        ),
      })),
  });

  return (
    <section className="space-y-3">
      {state.queue.map((item) => (
        <DeskCard key={item.id} task={item} />
      ))}
    </section>
  );
}
```

- Expose helper actions (`desk:approve`, `desk:reject`, `desk:assign`) for quick actions
  triggered by the agent or UI buttons.
- Always render empty-state UI so the surface stays useful before the agent streams
  data.

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
  form renderer (`JSONSchemaForm` or CopilotKit primitives). Reference the updated
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
  Playwright patterns (`libs_docs/copilotkit_examples/tests/approvals.spec.ts`) to keep
  smoke coverage consistent.

```tsx
"use client";

import Form from "@rjsf/core";
import { JSONSchema7 } from "json-schema";
import { useCoAgent, useCopilotAction } from "@copilotkit/react-core";

type ApprovalModal = {
  schema: JSONSchema7;
  uiSchema?: Record<string, unknown>;
  formData: Record<string, unknown>;
  envelopeId: string;
};

export function ApprovalModalForm() {
  const { state, setState } = useCoAgent<{ modal: ApprovalModal | null }>({
    name: "approvals",
    initialState: { modal: null },
  });

  const approve = useCopilotAction({
    name: "approvals:approve",
    parameters: [{ name: "envelopeId", type: "string", required: true }, { name: "formData", type: "object", required: true }],
  });

  if (!state.modal) {
    return null;
  }

  return (
    <Form
      schema={state.modal.schema}
      uiSchema={state.modal.uiSchema}
      formData={state.modal.formData}
      onChange={({ formData }) =>
        setState((prev) => ({
          ...prev,
          modal: prev.modal ? { ...prev.modal, formData } : prev.modal,
        }))
      }
      onSubmit={({ formData }) =>
        approve({ envelopeId: state.modal!.envelopeId, formData })
      }
      onError={(errors) => console.warn("approval modal validation", errors)}
    >
      <div className="flex justify-end gap-2">
        <button type="button" onClick={() => setState((prev) => ({ ...prev, modal: null }))}>
          Cancel
        </button>
        <button type="submit" className="btn btn-primary">
          Approve
        </button>
      </div>
    </Form>
  );
}
```

- Derive optional `uiSchema` metadata from the catalog service so we can annotate fields
  with helper text, icons, or scope warnings without patching the schema.
- Store decision outcomes back in shared state (`approvals.history`) so the agent can
  summarise them in transcripts and audit logs.

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
