"""Before-invocation callback logic."""

from __future__ import annotations

import json
from typing import Any, Optional

try:  # pragma: no cover - optional dependency during unit tests
    from google.adk.agents.callback_context import CallbackContext
    from google.adk.models import LlmRequest, LlmResponse
except ImportError:  # pragma: no cover
    CallbackContext = Any  # type: ignore
    LlmRequest = Any  # type: ignore
    LlmResponse = Any  # type: ignore
from google.genai import types
from google.genai.types import Content, Part

from ..services.state import ensure_proverbs_state
from .guardrails import GuardrailResult, run_guardrails


def on_before_agent(callback_context: CallbackContext) -> None:
    """Seed shared state for the session."""

    ensure_proverbs_state(callback_context.state)


def before_model_modifier(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Inject shared state and enforce guardrails before the model runs."""

    guardrail_response = _evaluate_guardrails(callback_context)
    if guardrail_response is not None:
        return guardrail_response

    proverbs = ensure_proverbs_state(callback_context.state)
    proverbs_json = "No proverbs yet"
    if proverbs:
        try:
            proverbs_json = json.dumps(proverbs, indent=2)
        except (TypeError, ValueError):  # pragma: no cover - defensive fallback
            proverbs_json = "Error serialising proverbs state"

    original_instruction = (
        llm_request.config.system_instruction
        or types.Content(role="system", parts=[])
    )

    if not isinstance(original_instruction, Content):
        original_instruction = Content(
            role="system",
            parts=[Part(text=str(original_instruction))],
        )

    if not original_instruction.parts:
        original_instruction.parts.append(Part(text=""))

    prompt_prefix = (
        "You are a helpful assistant for maintaining a list of proverbs.\n"
        f"Current proverbs state: {proverbs_json}\n"
        "Use the set_proverbs tool whenever you modify the list."
    )

    existing_text = original_instruction.parts[0].text or ""
    original_instruction.parts[0].text = prompt_prefix + existing_text
    llm_request.config.system_instruction = original_instruction

    return None


def _evaluate_guardrails(
    callback_context: CallbackContext,
) -> Optional[LlmResponse]:
    """Run configured guardrails and return a synthetic response when blocked."""

    evaluations = run_guardrails(callback_context)
    blocking: Optional[GuardrailResult] = next(
        (result for result in evaluations if not result.allowed),
        None,
    )

    if blocking is None:
        return None

    message = blocking.reason or f"Request blocked by {blocking.name} guardrail."
    content = Content(role="model", parts=[Part(text=message)])
    return LlmResponse(content=content)
