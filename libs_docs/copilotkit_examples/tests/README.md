# Playwright Smoke Patterns

These reference tests mirror the smoke scenarios we expect every product surface to
cover. They are not wired into CI; instead, treat them as reusable starting points when
building real Playwright test suites for the Desk and Approvals routes.

Run them with the standard Playwright runner once the Next.js shell is available:

```bash
pnpm dlx playwright test libs_docs/copilotkit_examples/tests
```

## Covered Scenarios

1. **Sidebar boot** – verifies CopilotKit sidebar initialises against the mocked runtime.
2. **Desk queue render** – ensures desk queue items appear after a `StateDeltaEvent`.
3. **Approval submit/cancel** – exercises schema-driven form submission handlers.
4. **Guardrail banner** – surfaces guardrail deltas emitted by the agent callbacks.

See the individual spec files for fixture helpers and request mocks.
