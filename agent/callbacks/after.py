"""After-invocation callback logic."""

from __future__ import annotations

from typing import Optional

try:  # pragma: no cover - fail fast when google-adk is missing
    from google.adk.agents.callback_context import CallbackContext
    from google.adk.models import LlmResponse
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "google-adk must be installed to use the agent callbacks. "
        "Install the vendor package and retry."
    ) from exc


def simple_after_model_modifier(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Stop consecutive tool calls for the demo agent."""

    if callback_context.agent_name != "ProverbsAgent":
        return None

    if llm_response.content and llm_response.content.parts:
        invocation_context = getattr(callback_context, "_invocation_context", None)
        if invocation_context is not None and hasattr(invocation_context, "end_invocation"):
            invocation_context.end_invocation = True

    return None
