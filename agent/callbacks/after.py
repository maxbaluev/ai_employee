"""After-invocation callback builders for the control plane agent."""

from __future__ import annotations

try:  # pragma: no cover - fail fast when google-adk is missing
    from google.adk.agents.callback_context import CallbackContext
    from google.adk.models import LlmResponse
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "google-adk must be installed to use the agent callbacks. "
        "Install the vendor package and retry."
    ) from exc


def build_after_model_modifier(*, blueprint):
    """Bind the after-model callback to the provided blueprint."""

    def after_model_modifier(
        callback_context: CallbackContext, llm_response: LlmResponse
    ) -> LlmResponse | None:
        blueprint.post_model(callback_context.state, response=llm_response)

        outbox_state = getattr(callback_context, "state", {}).get("outbox")
        if isinstance(outbox_state, dict) and outbox_state.get("last_envelope_id"):
            if hasattr(callback_context, "end_invocation"):
                setattr(callback_context, "end_invocation", True)

        return None

    return after_model_modifier
