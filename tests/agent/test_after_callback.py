"""Regression tests for after-invocation callbacks."""

from types import SimpleNamespace

from agent.callbacks.after import simple_after_model_modifier


def test_simple_after_model_modifier_sets_invocation_context_flag() -> None:
    """Ensure we stop the Proverbs agent by mutating the invocation context."""

    invocation_context = SimpleNamespace(end_invocation=False)
    callback_context = SimpleNamespace(
        agent_name="ProverbsAgent",
        _invocation_context=invocation_context,
    )

    llm_response = SimpleNamespace(content=SimpleNamespace(parts=[object()]))

    simple_after_model_modifier(callback_context, llm_response)

    assert invocation_context.end_invocation is True
