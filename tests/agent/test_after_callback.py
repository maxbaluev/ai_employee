"""Regression tests for after-invocation callbacks."""

from types import SimpleNamespace

from agent.agents.blueprints import DeskBlueprint
from agent.callbacks.after import build_after_model_modifier


def test_after_model_modifier_sets_invocation_flag() -> None:
    """Ensure the callback ends the invocation when an envelope was enqueued."""

    blueprint = DeskBlueprint()
    after_callback = build_after_model_modifier(blueprint=blueprint)

    invocation_context = SimpleNamespace(end_invocation=False)
    callback_context = SimpleNamespace(
        state={"outbox": {"last_envelope_id": "env_123"}},
        end_invocation=False,
        _invocation_context=invocation_context,
    )

    llm_response = SimpleNamespace(content=None)

    after_callback(callback_context, llm_response)

    assert callback_context.end_invocation is True
