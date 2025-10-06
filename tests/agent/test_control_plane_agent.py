"""Tests for the control plane agent factory and tools."""

from types import SimpleNamespace

from agent.agents.blueprints import DeskBlueprint
from agent.agents.control_plane import (
    ControlPlaneDependencies,
    _build_enqueue_envelope_tool,
)
from agent.services import (
    AppSettings,
    InMemoryCatalogService,
    InMemoryObjectivesService,
    InMemoryOutboxService,
    StructlogAuditLogger,
    ToolCatalogEntry,
)


def _build_dependencies() -> ControlPlaneDependencies:
    settings = AppSettings()
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

    return ControlPlaneDependencies(
        settings=settings,
        catalog_service=catalog,
        objectives_service=objectives,
        outbox_service=outbox,
        audit_logger=audit,
        blueprint=blueprint,
    )


def test_enqueue_envelope_tool_enqueues_record() -> None:
    deps = _build_dependencies()
    enqueue_tool = _build_enqueue_envelope_tool(deps)

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
