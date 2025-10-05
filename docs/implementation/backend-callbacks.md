# Agent Callbacks & Guardrails

**Status:** Implemented (demo callbacks) · In progress (guardrails) · Planned (trust,
quiet hours, approvals)

Callbacks are where we inject business logic into the ADK agent. Today they only power
the proverbs demo; this guide explains how to evolve them responsibly.

## Current Structure (`agent/agent.py`)

| Callback | Purpose | Notes |
|----------|---------|-------|
| `on_before_agent` | Seed shared state with default proverbs. | Runs once per session. |
| `before_model_modifier` | Injects state into the system prompt. | Should become the
  place where we stitch objectives + guardrails. |
| `simple_after_model_modifier` | Ends invocation after a single tool call. | Replace
  when adding multi-step plans. |

## Guardrail Patterns to Introduce

1. **Quiet hours / DNC** – check tenant config before executing tools; if blocked, emit a
   refusal response and log to audit.
2. **Trust thresholds** – evaluate historical approval metrics to decide whether an
   action should auto-run or require human approval.
3. **Scope enforcement** – ensure the requested tool scopes are enabled on the connected
   account; if not, trigger JIT upgrade flow.
4. **Evidence requirement** – fail proposals that do not reference supporting signals or
   tool output.

Implement these as separate modules (e.g. `guardrails/quiet_hours.py`) and call them from
within the callbacks to keep the agent readable.

## Suggested Module Layout

```
agent/
 ├─ app.py              # FastAPI wiring
 ├─ agents/
 │   └─ main.py         # LlmAgent definition
 ├─ callbacks/
 │   ├─ before.py       # prompt + guardrail synthesis
 │   └─ after.py        # tool chaining, run summary
 ├─ guardrails/
 │   ├─ quiet_hours.py
 │   ├─ trust.py
 │   └─ scopes.py
 └─ services/
     ├─ catalog.py      # Composio metadata
     ├─ objectives.py
     └─ audit.py
```

## Testing Guidance

- Callbacks should be pure functions where possible. Feed them mock `CallbackContext`
  objects and assert on returned mutations.
- Add integration tests that spin up the FastAPI app with a fake Composio client to
  ensure guardrails prevent unsafe executions.

Document every new guardrail in `docs/governance/security-and-guardrails.md` and surface
the customer-facing behaviour in the relevant UI doc.
