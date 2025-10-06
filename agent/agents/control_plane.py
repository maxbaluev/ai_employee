"""Factory for the Composio-enabled control plane agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

try:  # pragma: no cover - fail fast when google-adk is missing
    from ag_ui_adk import ADKAgent
    from google.adk.agents import LlmAgent
    from google.adk.tools import ToolContext
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "google-adk and ag-ui-adk must be installed to build the control plane agent."
    ) from exc

import structlog

from agent.agents.blueprints import DeskBlueprint
from agent.callbacks import (
    build_after_model_modifier,
    build_before_model_modifier,
    build_on_before_agent,
)
from agent.schemas.envelope import Envelope
from agent.services import (
    AppSettings,
    AuditLogger,
    CatalogService,
    ComposioCatalogService,
    InMemoryCatalogService,
    InMemoryObjectivesService,
    InMemoryOutboxService,
    ObjectivesService,
    OutboxService,
    SupabaseAuditLogger,
    SupabaseCatalogService,
    SupabaseObjectivesService,
    SupabaseOutboxService,
    SupabaseNotConfiguredError,
    StructlogAuditLogger,
    ToolCatalogEntry,
    DEFAULT_OBJECTIVES,
    get_settings,
    get_supabase_client,
)


logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class ControlPlaneDependencies:
    """Container for the services backing the control plane agent."""

    settings: AppSettings
    catalog_service: CatalogService
    objectives_service: ObjectivesService
    outbox_service: OutboxService
    audit_logger: AuditLogger
    blueprint: DeskBlueprint


def build_control_plane_agent(
    *,
    settings: Optional[AppSettings] = None,
    catalog_service: CatalogService | None = None,
    objectives_service: ObjectivesService | None = None,
    outbox_service: OutboxService | None = None,
    audit_logger: AuditLogger | None = None,
) -> Any:
    """Create an ADKAgent wired with Composio-aware callbacks and tools."""

    app_settings = settings or get_settings()

    dependencies = _resolve_dependencies(
        app_settings,
        catalog_service=catalog_service,
        objectives_service=objectives_service,
        outbox_service=outbox_service,
        audit_logger=audit_logger,
    )

    agent = _build_agent(dependencies)
    return ADKAgent(
        adk_agent=agent,
        app_name=app_settings.app_name,
        user_id=app_settings.user_id,
        session_timeout_seconds=3600,
        use_in_memory_services=isinstance(dependencies.outbox_service, InMemoryOutboxService),
    )


def _resolve_dependencies(
    settings: AppSettings,
    *,
    catalog_service: CatalogService | None,
    objectives_service: ObjectivesService | None,
    outbox_service: OutboxService | None,
    audit_logger: AuditLogger | None,
) -> ControlPlaneDependencies:
    blueprint = DeskBlueprint()

    supabase_client = None
    if settings.supabase_enabled():
        try:
            supabase_client = get_supabase_client(settings)
        except SupabaseNotConfiguredError as exc:
            logger.warning("Supabase misconfigured; falling back to in-memory services", exc_info=exc)

    if supabase_client is not None:
        resolved_catalog = catalog_service or SupabaseCatalogService(
            supabase_client, schema=settings.supabase_schema
        )
        resolved_objectives = objectives_service or SupabaseObjectivesService(
            supabase_client, schema=settings.supabase_schema
        )
        resolved_outbox = outbox_service or SupabaseOutboxService(
            supabase_client, schema=settings.supabase_schema
        )
        resolved_audit = audit_logger or SupabaseAuditLogger(
            supabase_client, schema=settings.supabase_schema
        )
        _sync_catalog_from_composio(settings, resolved_catalog)

        return ControlPlaneDependencies(
            settings=settings,
            catalog_service=resolved_catalog,
            objectives_service=resolved_objectives,
            outbox_service=resolved_outbox,
            audit_logger=resolved_audit,
            blueprint=blueprint,
        )

    resolved_catalog = catalog_service or _resolve_in_memory_catalog(settings)
    resolved_objectives = objectives_service or InMemoryObjectivesService(
        objectives_by_tenant={settings.tenant_id: DEFAULT_OBJECTIVES}
    )
    resolved_outbox = outbox_service or InMemoryOutboxService()
    resolved_audit = audit_logger or StructlogAuditLogger()

    return ControlPlaneDependencies(
        settings=settings,
        catalog_service=resolved_catalog,
        objectives_service=resolved_objectives,
        outbox_service=resolved_outbox,
        audit_logger=resolved_audit,
        blueprint=blueprint,
    )


def _build_agent(dependencies: ControlPlaneDependencies) -> LlmAgent:
    instruction = (
        "You are the control plane agent coordinating tenants' SaaS actions via Composio.\n"
        "Use the `enqueue_envelope` tool to stage actions for the Outbox worker."
    )

    tools = [
        _build_enqueue_envelope_tool(dependencies),
    ]

    before_agent = build_on_before_agent(
        blueprint=dependencies.blueprint,
        objectives_service=dependencies.objectives_service,
        outbox_service=dependencies.outbox_service,
        settings=dependencies.settings,
    )
    before_model = build_before_model_modifier(
        blueprint=dependencies.blueprint,
        settings=dependencies.settings,
        catalog_service=dependencies.catalog_service,
        objectives_service=dependencies.objectives_service,
        audit_logger=dependencies.audit_logger,
        outbox_service=dependencies.outbox_service,
    )
    after_model = build_after_model_modifier(blueprint=dependencies.blueprint)

    return LlmAgent(
        name="ControlPlaneAgent",
        model=dependencies.settings.default_model,
        instruction=instruction,
        tools=tools,
        before_agent_callback=before_agent,
        before_model_callback=before_model,
        after_model_callback=after_model,
    )


def _build_enqueue_envelope_tool(dependencies: ControlPlaneDependencies):
    catalog_service = dependencies.catalog_service
    outbox_service = dependencies.outbox_service
    audit_logger = dependencies.audit_logger
    blueprint = dependencies.blueprint
    settings = dependencies.settings

    def enqueue_envelope(
        tool_context: ToolContext,
        envelope: Mapping[str, Any],
        required_scopes: Sequence[str] | None = None,
        proposal: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        try:
            slug = str(envelope.get("tool_slug") or envelope.get("slug") or "").strip()
            if not slug:
                raise ValueError("tool_slug is required to enqueue an envelope")

            catalog_entry = catalog_service.get_tool(settings.tenant_id, slug)
            if catalog_entry is None:
                raise ValueError(f"Tool {slug!r} not found in catalog")

            arguments = envelope.get("arguments")
            if not isinstance(arguments, Mapping):
                raise TypeError("Envelope arguments must be a mapping")
            catalog_entry.validate_arguments(arguments)

            normalised_envelope = Envelope.from_payload(
                payload=envelope,
                tenant_id=settings.tenant_id,
                default_risk=catalog_entry.risk,
            )
            record = outbox_service.enqueue(normalised_envelope)
            audit_logger.log_envelope(
                tenant_id=settings.tenant_id,
                envelope_id=record.envelope.envelope_id,
                tool_slug=record.envelope.tool_slug,
                status=record.status,
            )

            scopes = list(required_scopes or catalog_entry.required_scopes)
            blueprint.register_envelope(
                tool_context.state,
                record=record,
                required_scopes=scopes,
                proposal=proposal,
            )

            return {
                "status": "queued",
                "envelopeId": record.envelope.envelope_id,
                "risk": record.envelope.risk,
            }
        except Exception as exc:  # pragma: no cover - defensive path
            return {"status": "error", "message": str(exc)}

    enqueue_envelope.__name__ = "enqueue_envelope"
    return enqueue_envelope


def _resolve_in_memory_catalog(settings: AppSettings) -> CatalogService:
    if settings.composio_api_key:
        try:
            remote_service = ComposioCatalogService(
                api_key=settings.composio_api_key,
                client_id=settings.composio_client_id,
                client_secret=settings.composio_client_secret,
                redirect_url=settings.composio_redirect_url,
                toolkits=settings.default_toolkits,
            )
            entries = remote_service.list_tools(settings.tenant_id)
            if entries:
                return InMemoryCatalogService(entries_by_tenant={settings.tenant_id: entries})
        except RuntimeError as exc:
            logger.warning("Composio SDK unavailable; using demo catalog", exc_info=exc)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to hydrate catalog from Composio", exc_info=exc)

    entries = _build_demo_catalog_entries()
    return InMemoryCatalogService(entries_by_tenant={settings.tenant_id: entries})


def _sync_catalog_from_composio(settings: AppSettings, catalog_service: CatalogService) -> None:
    if not settings.composio_api_key:
        return

    if not hasattr(catalog_service, "sync_entries"):
        return

    try:
        remote_service = ComposioCatalogService(
            api_key=settings.composio_api_key,
            client_id=settings.composio_client_id,
            client_secret=settings.composio_client_secret,
            redirect_url=settings.composio_redirect_url,
            toolkits=settings.default_toolkits,
        )
        entries = remote_service.list_tools(settings.tenant_id)
        if entries:
            catalog_service.sync_entries(settings.tenant_id, entries)  # type: ignore[attr-defined]
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Failed to sync catalog from Composio", exc_info=exc)


def _build_demo_catalog_entries() -> Sequence[ToolCatalogEntry]:
    return (
        ToolCatalogEntry(
            slug="GMAIL__drafts.create",
            name="Create Gmail Draft",
            description="Prepare a Gmail draft message for user review.",
            version="1.0",
            schema={
                "type": "object",
                "required": ["to", "subject", "body"],
                "properties": {
                    "to": {"type": "string", "description": "Recipient email"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
            },
            required_scopes=["GMAIL.SMTP"],
            risk="medium",
        ),
        ToolCatalogEntry(
            slug="SLACK__chat.postMessage",
            name="Post Slack Message",
            description="Send a message to a Slack channel on behalf of the tenant.",
            version="1.0",
            schema={
                "type": "object",
                "required": ["channel", "text"],
                "properties": {
                    "channel": {"type": "string"},
                    "text": {"type": "string"},
                },
            },
            required_scopes=["SLACK.CHAT:WRITE"],
            risk="low",
        ),
    )
