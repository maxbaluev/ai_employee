"""Before-invocation callback builders for the control plane agent."""

from __future__ import annotations

from typing import Sequence

try:  # pragma: no cover - fail fast when google-adk is missing
    from google.adk.agents.callback_context import CallbackContext
    from google.adk.models import LlmRequest, LlmResponse
    from google.genai.types import Content, Part
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "google-adk must be installed to use the agent callbacks. "
        "Install the vendor package and retry."
    ) from exc

from agent.callbacks.guardrails import GuardrailResult, run_guardrails
from agent.services import (
    AuditLogger,
    CatalogService,
    ObjectivesService,
    OutboxService,
    write_guardrail_results,
)
from agent.services.settings import AppSettings


def build_on_before_agent(
    *,
    blueprint,
    objectives_service: ObjectivesService,
    outbox_service: OutboxService,
    settings: AppSettings,
):
    """Return a callback that seeds shared state before the agent runs."""

    def on_before_agent(callback_context: CallbackContext) -> None:
        objectives = objectives_service.list_objectives(settings.tenant_id)
        pending = outbox_service.list_pending(tenant_id=settings.tenant_id, limit=25)
        blueprint.ensure_shared_state(
            callback_context.state,
            objectives=objectives,
            pending=pending,
        )

    return on_before_agent


def build_before_model_modifier(
    *,
    blueprint,
    settings: AppSettings,
    catalog_service: CatalogService,
    objectives_service: ObjectivesService,
    audit_logger: AuditLogger,
    outbox_service: OutboxService,
):
    """Return the before-model modifier bound to the configured dependencies."""

    def before_model_modifier(
        callback_context: CallbackContext, llm_request: LlmRequest
    ) -> LlmResponse | None:
        evaluations = run_guardrails(callback_context, settings=settings)
        write_guardrail_results(callback_context.state, evaluations=evaluations)

        for evaluation in evaluations:
            audit_logger.log_guardrail(
                tenant_id=settings.tenant_id,
                name=evaluation.name,
                allowed=evaluation.allowed,
                reason=evaluation.reason,
            )

        blocking = _find_blocking_guardrail(evaluations)
        if blocking is not None:
            _end_invocation(callback_context)
            message = blueprint.guardrail_block_message(blocking)
            return _synthetic_response(message)

        objectives = objectives_service.list_objectives(settings.tenant_id)
        entries = catalog_service.list_tools(settings.tenant_id)
        pending = outbox_service.list_pending(tenant_id=settings.tenant_id, limit=25)
        prompt_prefix = blueprint.prompt_prefix(objectives=objectives, catalog_entries=entries)
        if prompt_prefix:
            _prepend_instruction(llm_request, prompt_prefix)

        blueprint.ensure_shared_state(
            callback_context.state,
            objectives=objectives,
            pending=pending,
        )
        return None

    return before_model_modifier


def _find_blocking_guardrail(evaluations: Sequence[GuardrailResult]) -> GuardrailResult | None:
    return next((result for result in evaluations if not result.allowed), None)


def _synthetic_response(message: str) -> LlmResponse:
    content = Content(role="model", parts=[Part(text=message)])
    return LlmResponse(content=content)


def _prepend_instruction(llm_request: LlmRequest, prefix: str) -> None:
    system_instruction = llm_request.config.system_instruction
    if not isinstance(system_instruction, Content):
        system_instruction = Content(role="system", parts=[Part(text="")])

    if not system_instruction.parts:
        system_instruction.parts.append(Part(text=""))

    existing = system_instruction.parts[0].text or ""
    system_instruction.parts[0].text = prefix + "\n\n" + existing
    llm_request.config.system_instruction = system_instruction


def _end_invocation(callback_context: CallbackContext) -> None:
    if hasattr(callback_context, "end_invocation"):
        setattr(callback_context, "end_invocation", True)
