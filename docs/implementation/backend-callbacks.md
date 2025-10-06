# Agent Callbacks & Guardrails

**Status:** Implemented (control plane callbacks + Supabase services) · In progress
(approvals orchestration)

Callbacks are where we inject business logic into the ADK agent. The control plane
agent now relies on dedicated callback builders and guardrail modules; this guide
explains how to extend them safely as more surfaces come online.

## Current Structure (`agent/callbacks/`)

| Builder | Purpose | Notes |
|---------|---------|-------|
| `build_on_before_agent` | Seeds desk shared state using tenant objectives and pending outbox envelopes. | Runs once per session. |
| `build_before_model_modifier` | Injects catalog context, evaluates guardrails, enriches prompts. | Logs guardrail outcomes, short-circuits on block, refreshes shared state. |
| `build_after_model_modifier` | Updates shared state after an LLM response and ends the invocation once an envelope is queued. | Keeps the run deterministic by avoiding additional tool calls. |

> The upstream ADK samples in `libs_docs/copilotkit_docs/adk/` demonstrate
> short-circuiting requests by setting `callback_context.end_invocation = True`. Avoid
> touching private attributes such as `_invocation_context` when ending a run.

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

Import ADK primitives directly (`from google.adk.agents.callback_context import
CallbackContext`) and fail fast when the vendor SDK is missing. The examples in
`libs_docs/copilotkit_examples/` follow the same pattern so runtime errors surface early
during local development.

## Suggested Module Layout

```
agent/
 ├─ agents/
 │   ├─ control_plane.py     # Composio-enabled ADK agent wiring
 │   └─ blueprints/
 │       └─ desk.py          # Shared-state + prompt helpers for the desk surface
 ├─ callbacks/
 │   ├─ before.py            # Guardrail evaluation + prompt enrichment (builders)
 │   ├─ after.py             # Post-run shared state updates (builders)
 │   └─ guardrails.py        # Glue that orchestrates guardrail modules
 ├─ guardrails/
 │   ├─ quiet_hours.py
 │   ├─ trust.py
 │   ├─ scopes.py
 │   └─ evidence.py
 └─ services/
     ├─ catalog.py          # Supabase + Composio catalog adapters
     ├─ objectives.py       # Supabase tenant objectives (in-memory fixtures for tests)
     ├─ outbox.py           # Supabase queue + in-memory fixtures
     ├─ audit.py            # structlog + Supabase audit loggers
     └─ supabase.py         # Supabase client factory/cache helpers
```

## Guardrail Module Scaffold

See `libs_docs/adk/full_llm_docs.txt` for ADK guardrail composition patterns—mirror the
samples so callbacks stay declarative and thin. Each guardrail module should expose a
pure `check` helper that returns a `GuardrailResult`, accepts injected dependencies (like
clocks or catalog lookups), and never mutates global state.

- Keep modules framework-agnostic by passing in the `CallbackContext` and any
  pre-resolved services instead of importing FastAPI or database clients directly.
- Share dataclasses or utilities (for example a `Threshold` helper) via a
  `guardrails/shared.py` module so each guardrail stays focused on a single policy.
- Treat guardrail responses as user-facing artefacts; reuse the refusal tone described in
  `libs_docs/adk/full_llm_docs.txt` when crafting `reason` messages.

```python
# agent/guardrails/quiet_hours.py
from datetime import time
from typing import Callable, Optional, Tuple

from google.adk.agents.callback_context import CallbackContext

from agent.callbacks.guardrails import GuardrailResult


def check(
    ctx: CallbackContext,
    quiet_window: Optional[Tuple[time, time]],
    clock: Callable[[], time],
) -> GuardrailResult:
    if not quiet_window:
        return GuardrailResult("quiet_hours", allowed=True, reason="quiet hours disabled")

    start, end = quiet_window
    now = clock()
    in_window = start <= now <= end if start <= end else now >= start or now <= end
    if in_window:
        return GuardrailResult(
            "quiet_hours",
            allowed=False,
            reason="Quiet hours are in effect; deferring until the window closes.",
        )

    return GuardrailResult("quiet_hours", allowed=True, reason="outside quiet hours")


# agent/guardrails/trust.py
def check(ctx: CallbackContext, approvals_ratio: float | None, threshold: float) -> GuardrailResult:
    ratio = approvals_ratio if approvals_ratio is not None else 0.0
    allowed = ratio >= threshold
    reason = None if allowed else (
        f"Trust score {ratio:.2f} below {threshold:.2f}; human approval required."
    )
    return GuardrailResult("trust_threshold", allowed=allowed, reason=reason)


# agent/guardrails/scopes.py
def check(
    ctx: CallbackContext,
    requested_scopes: set[str],
    enabled_scopes: set[str],
) -> GuardrailResult:
    missing = requested_scopes - enabled_scopes
    if missing:
        return GuardrailResult(
            "scope_validation",
            allowed=False,
            reason=f"Scopes missing on connected account: {sorted(missing)}",
        )
    return GuardrailResult("scope_validation", allowed=True)


# agent/guardrails/evidence.py
def check(ctx: CallbackContext, proposal: dict[str, object]) -> GuardrailResult:
    evidence = proposal.get("evidence", []) if proposal else []
    if not evidence:
        return GuardrailResult(
            "evidence_requirement",
            allowed=False,
            reason="No supporting evidence attached to the proposal.",
        )
    return GuardrailResult("evidence_requirement", allowed=True)


# agent/callbacks/before.py
from agent.guardrails import quiet_hours, trust, scopes, evidence


def before_model_modifier(ctx: CallbackContext) -> CallbackContext:
    tenant = ctx.shared_state.get("tenant", {})
    evaluations = (
        quiet_hours.check(
            ctx,
            quiet_window=tenant.get("quiet_hours"),
            clock=ctx.dependencies["clock"],
        ),
        trust.check(
            ctx,
            approvals_ratio=tenant.get("approvals_ratio", 1.0),
            threshold=ctx.settings.trust_threshold,
        ),
        scopes.check(
            ctx,
            requested_scopes=ctx.intent.requested_scopes,
            enabled_scopes=tenant.get("enabled_scopes", set()),
        ),
        evidence.check(ctx, proposal=ctx.intent.proposal),
    )

    for result in evaluations:
        if not result.allowed:
            ctx.responses.add_refusal(result.reason or "Action blocked by guardrail.")
            ctx.audit.log_guardrail(name=result.name, reason=result.reason)
            ctx.end_invocation = True
            return ctx

    ctx.shared_state["guardrail_summary"] = [r.name for r in evaluations]
    return ctx
```

## Testing Guidance

- Callbacks should be pure functions where possible. Feed them mock `CallbackContext`
  objects and assert on returned mutations.
- Add integration tests that spin up the FastAPI app with a fake Composio client to
  ensure guardrails prevent unsafe executions.

## Pytest Snippets

Keep guardrail tests lightweight: use factory fixtures inspired by
`libs_docs/adk/full_llm_docs.txt` to build `CallbackContext` doubles, inject dependency
shims, and assert on the returned `GuardrailResult` instead of global side-effects.

```python
# tests/guardrails/test_quiet_hours.py
import datetime as dt

from agent.guardrails import quiet_hours


def test_quiet_hours_blocks_inside_window(callback_context_factory):
    ctx = callback_context_factory(now=dt.time(23, 0))
    result = quiet_hours.check(
        ctx,
        quiet_window=(dt.time(22, 0), dt.time(6, 0)),
        clock=lambda: dt.time(23, 0),
    )
    assert not result.allowed
    assert "Quiet hours" in (result.reason or "")
```

```python
# tests/guardrails/test_trust_threshold.py
from agent.guardrails import trust


def test_trust_threshold_requires_manual_review(callback_context_factory):
    ctx = callback_context_factory()
    result = trust.check(ctx, approvals_ratio=0.55, threshold=0.80)
    assert not result.allowed
    assert "Trust score" in (result.reason or "")
```

```python
# tests/guardrails/test_scopes.py
from agent.guardrails import scopes


def test_scope_validation_reports_missing_scopes(callback_context_factory):
    ctx = callback_context_factory()
    result = scopes.check(
        ctx,
        requested_scopes={"crm.write"},
        enabled_scopes={"crm.read"},
    )
    assert not result.allowed
    assert "Scopes missing" in (result.reason or "")
```

```python
# tests/guardrails/test_evidence.py
from agent.guardrails import evidence


def test_evidence_requirement_blocks_empty_payload(callback_context_factory):
    ctx = callback_context_factory()
    result = evidence.check(ctx, proposal={"summary": "Send email", "evidence": []})
    assert not result.allowed
    assert "No supporting evidence" in (result.reason or "")
```

Document every new guardrail in `docs/governance/security-and-guardrails.md` and surface
the customer-facing behaviour in the relevant UI doc.

## Implemented Guardrails (October 2025)

All four production guardrails now live in `agent/guardrails/` with pytest coverage in
`tests/guardrails/`. The table below summarises behaviour and blocking criteria.

| Guardrail | Function Signature | Allows When | Blocks When | Tests |
|-----------|-------------------|-------------|-------------|-------|
| Quiet hours / DNC | `quiet_hours.check(ctx, quiet_window, clock)` | Quiet window not configured or `clock()` returns a time outside the configured range. | `clock()` falls inside the configured quiet-hour window. | `tests/guardrails/test_quiet_hours.py` |
| Trust threshold | `trust.check(ctx, approvals_ratio, threshold, source=None)` | Trust score ≥ threshold (missing scores treated as `0.0`). | Trust score < threshold (including missing score) | `tests/guardrails/test_trust.py` |
| Scope validation | `scopes.check(ctx, requested_scopes, enabled_scopes)` | Normalised requested scopes are a subset of normalised enabled scopes. | Any required scope is missing after normalising (strip + lower). | `tests/guardrails/test_scopes.py` |
| Evidence requirement | `evidence.check(ctx, proposal)` | Proposal contains at least one non-empty evidence entry. | Proposal missing, empty, or evidence whitespace-only. `ensure_evidence_present` bypasses this when no proposal exists. | `tests/guardrails/test_evidence.py` |

The callback integration remains declarative—`agent/callbacks/guardrails.py` simply
delegates to these helpers:

```python
def enforce_scope_validation(ctx: CallbackContext) -> GuardrailResult:
    settings = get_settings()
    if not settings.enforce_scope_validation:
        return GuardrailResult("scope_validation", True, "scope validation disabled via settings")

    state = getattr(ctx, "state", {})
    requested = state.get("requested_scopes") if isinstance(state, dict) else None
    enabled = state.get("enabled_scopes") if isinstance(state, dict) else None
    return scopes_check(ctx, requested_scopes=requested, enabled_scopes=enabled)


def ensure_evidence_present(ctx: CallbackContext) -> GuardrailResult:
    settings = get_settings()
    if not settings.require_evidence:
        return GuardrailResult("evidence_requirement", True, "evidence requirement disabled via settings")

    proposal = None
    state = getattr(ctx, "state", {})
    if isinstance(state, dict):
        proposal = state.get("proposal")
    if proposal is None:
        return GuardrailResult("evidence_requirement", True, "no proposal to evaluate; allowing")

    return evidence_check(ctx, proposal)
```

`agent/callbacks/before.py` still short-circuits the invocation whenever any guardrail
returns `allowed=False`, surfacing the guardrail reason back to the UI.
