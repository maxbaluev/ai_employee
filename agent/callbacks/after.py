"""After-invocation callback logic."""

from __future__ import annotations

from typing import Any, Optional

try:  # pragma: no cover - optional dependency during unit tests
    from google.adk.agents.callback_context import CallbackContext
    from google.adk.models import LlmResponse
except ImportError:  # pragma: no cover
    CallbackContext = Any  # type: ignore
    LlmResponse = Any  # type: ignore


def simple_after_model_modifier(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Stop consecutive tool calls for the demo agent."""

    if callback_context.agent_name != "ProverbsAgent":
        return None

    if llm_response.content and llm_response.content.parts:
        callback_context._invocation_context.end_invocation = True

    return None
