"""Tests for serialising guardrail results into shared state."""

from __future__ import annotations

from agent.guardrails.shared import GuardrailResult
from agent.services.state import ensure_guardrail_state, write_guardrail_results


def test_write_guardrail_results_normalises_payload() -> None:
    state: dict[str, object] = {}
    evaluations = (
        GuardrailResult(
            "quiet_hours",
            allowed=True,
            reason="Outside quiet hours",
            metadata={"configured": True, "window": "08:00-17:00 UTC"},
        ),
        GuardrailResult(
            "trust_threshold",
            allowed=False,
            reason="Trust score 0.50 below threshold 0.80",
            metadata={
                "score": 0.5,
                "threshold": 0.8,
                "missingSignal": False,
                "source": "metrics",
            },
        ),
        GuardrailResult(
            "scope_validation",
            allowed=False,
            reason="missing scopes: crm.write",
            metadata={
                "missingScopes": ["crm.write"],
                "requestedScopes": ["crm.write"],
                "enabledScopes": ["crm.read"],
            },
        ),
        GuardrailResult(
            "evidence_requirement",
            allowed=False,
            reason="missing supporting evidence",
            metadata={
                "required": True,
                "missingEvidence": ["example"],
            },
        ),
        GuardrailResult("unknown_guardrail", allowed=True),
    )

    write_guardrail_results(state, evaluations=evaluations)
    guardrail_state = ensure_guardrail_state(state)

    assert guardrail_state["quietHours"]["allowed"] is True
    assert guardrail_state["quietHours"]["window"] == "08:00-17:00 UTC"

    trust = guardrail_state["trust"]
    assert trust["allowed"] is False
    assert trust["score"] == 0.5
    assert trust["threshold"] == 0.8
    assert trust["source"] == "metrics"

    scope = guardrail_state["scopeValidation"]
    assert scope["allowed"] is False
    assert scope["missingScopes"] == ["crm.write"]

    evidence = guardrail_state["evidence"]
    assert evidence["allowed"] is False
    assert evidence["missingEvidence"] == ["example"]

    assert "unknown_guardrail" not in guardrail_state
