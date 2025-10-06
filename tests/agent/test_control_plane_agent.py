"""Tests for the control plane agent factory and tools."""

from types import SimpleNamespace

from agent.agents.blueprints import DeskBlueprint
from agent.agents.coordinator import CoordinatorDependencies
from agent.agents.control_plane import _build_enqueue_envelope_tool
from agent.services import (
    AppSettings,
    InMemoryCatalogService,
    InMemoryObjectivesService,
    InMemoryOutboxService,
    StructlogAuditLogger,
    ToolCatalogEntry,
)


def _build_dependencies(**settings_overrides) -> tuple[CoordinatorDependencies, DeskBlueprint]:
    base_settings = AppSettings()
    settings = base_settings.model_copy(update=settings_overrides) if settings_overrides else base_settings
    blueprint = DeskBlueprint()
    catalog = InMemoryCatalogService(
        entries_by_tenant={
            settings.tenant_id: (
                ToolCatalogEntry(
                    slug="GMAIL__drafts.create",
                    name="Draft Email",
                    description="Draft an email for later approval",
                    version="1.0",
                    schema={
                        "type": "object",
                        "properties": {
                            "to": {"type": "string"},
                            "subject": {"type": "string"},
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
    outbox = InMemoryOutboxService()
    audit = StructlogAuditLogger()

    return (
        CoordinatorDependencies(
            settings=settings,
            catalog_service=catalog,
            objectives_service=objectives,
            outbox_service=outbox,
            audit_logger=audit,
        ),
        blueprint,
    )


def test_enqueue_envelope_tool_enqueues_record() -> None:
    deps, blueprint = _build_dependencies()
    enqueue_tool = _build_enqueue_envelope_tool(deps, blueprint)

    tool_context = SimpleNamespace(state={})
    payload = {
        "tool_slug": "GMAIL__drafts.create",
        "arguments": {"to": "customer@example.com", "subject": "Renewal"},
    }
    result = enqueue_tool(
        tool_context,
        payload,
        proposal={"summary": "Draft renewal email", "evidence": ["ticket#123"]},
    )

    assert result["status"] == "queued"
    pending = tuple(deps.outbox_service.list_pending())
    assert len(pending) == 1
    assert pending[0].envelope.tool_slug == "GMAIL__drafts.create"
    assert tool_context.state.get("outbox", {}).get("last_envelope_id") == pending[0].envelope.envelope_id


def test_enqueue_envelope_includes_default_scopes() -> None:
    deps, blueprint = _build_dependencies(default_scopes=("GLOBAL_SCOPE",))
    enqueue_tool = _build_enqueue_envelope_tool(deps, blueprint)

    tool_context = SimpleNamespace(state={})
    payload = {
        "tool_slug": "GMAIL__drafts.create",
        "arguments": {"to": "customer@example.com", "subject": "Renewal"},
    }
    enqueue_tool(tool_context, payload)

    modal = tool_context.state.get("approvalModal", {})
    required_scopes = modal.get("requiredScopes") if isinstance(modal, dict) else None
    assert required_scopes is not None
    assert "GLOBAL_SCOPE" in required_scopes
