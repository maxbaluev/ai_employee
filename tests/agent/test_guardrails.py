"""Tests for guardrail stubs and callback integration."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from google.genai.types import Content, Part

from agent.agents.blueprints import DeskBlueprint
from agent.callbacks import build_before_model_modifier
from agent.callbacks.guardrails import (
    GuardrailResult,
    enforce_quiet_hours,
    enforce_scope_validation,
    enforce_trust_threshold,
    ensure_evidence_present,
    run_guardrails,
)
from agent.services import (
    InMemoryCatalogService,
    InMemoryObjectivesService,
    InMemoryOutboxService,
    StructlogAuditLogger,
    ToolCatalogEntry,
)
from agent.services.settings import AppSettings


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
    callback = _build_before_callback()
    context = _fake_context()
    llm_request = SimpleNamespace(
        config=SimpleNamespace(
            system_instruction=Content(role="system", parts=[Part(text="base")])
        )
    )

    blocked = GuardrailResult("quiet_hours", allowed=False, reason="quiet hours active")
    monkeypatch.setattr(
        "agent.callbacks.before.run_guardrails",
        lambda *_, **__: (blocked,),
    )

    response = callback(context, llm_request)
    assert isinstance(response, LlmResponse)
    assert response.content.parts[0].text.startswith("Guardrail prevented")


def test_before_model_modifier_appends_state() -> None:
    callback = _build_before_callback()
    context = _fake_context()
    llm_request = SimpleNamespace(
        config=SimpleNamespace(
            system_instruction=Content(role="system", parts=[Part(text="")])
        )
    )

    response = callback(context, llm_request)
    assert response is None
    assert "desk" in context.state
    desk_state = context.state["desk"]
    assert isinstance(desk_state, dict)
    assert "queue" in desk_state


def _build_before_callback():
    settings = AppSettings()
    blueprint = DeskBlueprint()
    catalog = InMemoryCatalogService(
        entries_by_tenant={
            settings.tenant_id: (
                ToolCatalogEntry(
                    slug="GMAIL__drafts.create",
                    name="Draft Email",
                    description="Drafts an email",
                    version="1.0",
                    schema={
                        "type": "object",
                        "properties": {
                            "to": {"type": "string"},
                        },
                        "required": ["to"],
                    },
                    required_scopes=["GMAIL.SMTP"],
                    risk="medium",
                ),
            )
        }
    )
    objectives = InMemoryObjectivesService(objectives_by_tenant={settings.tenant_id: ()})
    audit_logger = StructlogAuditLogger()
    outbox = InMemoryOutboxService()

    return build_before_model_modifier(
        blueprint=blueprint,
        settings=settings,
        catalog_service=catalog,
        objectives_service=objectives,
        audit_logger=audit_logger,
        outbox_service=outbox,
    )
