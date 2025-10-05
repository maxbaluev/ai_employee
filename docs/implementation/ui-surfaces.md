# Building New UI Surfaces

**Status:** Planned

Use this checklist whenever you introduce a new customer-facing surface (Desk,
Approvals, Integrations, Activity & Safety). The goal is to keep UX consistent while the
backend evolves.

## 1. Define the State Contract

- Add a new slice to the agent state (e.g. `desk.queue`, `approvals.forms`).
- Document the schema in `agent/state_contract.md` (create the file when the first real
  surface ships).
- Emit `StateDeltaEvent` updates whenever the agent mutates the slice.

## 2. Build the React Surface

- Place components under `src/app/(desk)/` etc. using the App Router.
- Hydrate initial data from REST endpoints (once Supabase exists) and subscribe to
  shared state for live updates.
- Provide empty states and error boundaries – operators must understand what to do next.

## 3. Wire Approvals & Actions

- For edit/approve flows, render JSON Schema via a generic form component and submit the
  edited payload back to the control plane.
- All destructive actions must require confirmation and emit an audit event.

## 4. Accessibility & UX

- Meet WCAG AA contrast for every card and button.
- Keyboard navigation must work (CopilotKit surfaces full keyboard support out-of-the-box; keep it intact).
- Provide inline help (hover or info icon) that links back to this documentation when the
  action is non-trivial.

## 5. Verification

- Add Playwright coverage for the new surface.
- Include screenshots or short demos in the PR to capture UX decisions.

Once the first surface lands, update this document with concrete examples and code
snippets.
