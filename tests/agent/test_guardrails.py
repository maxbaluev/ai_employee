"""Tests for guardrail stubs and callback integration."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from google.genai.types import Content, Part

from agent.callbacks import before_model_modifier
from agent.callbacks.guardrails import (
    GuardrailResult,
    enforce_quiet_hours,
    enforce_scope_validation,
    enforce_trust_threshold,
    ensure_evidence_present,
    run_guardrails,
)


def _fake_context() -> CallbackContext:
    context = MagicMock(spec=CallbackContext)
    context.state = {
        "trust": {
            "score": 0.95,
            "source": "test_fixture",
        },
        "proposal": {"evidence": ["doc://example"]},
        "requested_scopes": {"crm.write"},
        "enabled_scopes": {"crm.write"},
    }
    return context


def test_guardrail_stubs_allow_by_default() -> None:
    context = _fake_context()
    results = run_guardrails(context)

    names = {result.name for result in results}
    assert {"quiet_hours", "trust_threshold", "scope_validation", "evidence_requirement"} == names
    assert all(result.allowed for result in results)


def test_individual_stubs_return_guardrail_results() -> None:
    context = _fake_context()

    for fn in (
        enforce_quiet_hours,
        enforce_trust_threshold,
        enforce_scope_validation,
        ensure_evidence_present,
    ):
        result = fn(context)
        assert isinstance(result, GuardrailResult)
        assert result.allowed is True
        assert result.name


def test_before_model_modifier_blocks_on_guardrail(monkeypatch) -> None:
    context = _fake_context()
    llm_request = SimpleNamespace(
        config=SimpleNamespace(
            system_instruction=Content(role="system", parts=[Part(text="base")])
        )
    )

    blocked = GuardrailResult("quiet_hours", allowed=False, reason="quiet hours active")
    monkeypatch.setattr(
        "agent.callbacks.before.run_guardrails",
        lambda _: (blocked,),
    )

    response = before_model_modifier(context, llm_request)
    assert isinstance(response, LlmResponse)
    assert response.content.parts[0].text == "quiet hours active"


def test_before_model_modifier_appends_state() -> None:
    context = _fake_context()
    llm_request = SimpleNamespace(
        config=SimpleNamespace(
            system_instruction=Content(role="system", parts=[Part(text="")])
        )
    )

    response = before_model_modifier(context, llm_request)
    assert response is None
    # After running the callback, the state should be initialised.
    assert context.state.get("proverbs") == []
