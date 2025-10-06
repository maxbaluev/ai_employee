"""Coordinator for composing control plane ADK agents across surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, Mapping, MutableMapping, Optional, Sequence, TypeVar

try:  # pragma: no cover - fail fast when vendor SDKs are absent
    from ag_ui_adk import ADKAgent
    from google.adk.agents import LlmAgent
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "google-adk and ag-ui-adk must be installed to use the agent coordinator."
    ) from exc

from agent.callbacks import (
    build_after_model_modifier,
    build_before_model_modifier,
    build_on_before_agent,
)
from agent.services import (
    AppSettings,
    AuditLogger,
    CatalogService,
    InMemoryOutboxService,
    ObjectivesService,
    OutboxService,
)


BlueprintT = TypeVar("BlueprintT", bound="BlueprintProtocol")


class BlueprintProtocol:
    """Protocol describing the expected blueprint surface interface."""

    name: str

    def ensure_shared_state(
        self,
        state: MutableMapping[str, Any],
        *,
        objectives: Sequence[Any],
        pending: Sequence[Any] = (),
    ) -> None: ...

    def guardrail_block_message(self, result: Any) -> str: ...

    def prompt_prefix(
        self,
        *,
        objectives: Sequence[Any],
        catalog_entries: Sequence[Any],
    ) -> str: ...

    def register_envelope(
        self,
        state: MutableMapping[str, Any],
        *,
        record: Any,
        required_scopes: Sequence[str] | None,
        proposal: Mapping[str, Any] | None,
    ) -> None: ...

    def post_model(self, state: MutableMapping[str, Any], *, response: Any) -> None: ...


@dataclass(slots=True)
class CoordinatorDependencies:
    """Resolved services shared across registered agent surfaces."""

    settings: AppSettings
    catalog_service: CatalogService
    objectives_service: ObjectivesService
    outbox_service: OutboxService
    audit_logger: AuditLogger


# Backwards compatibility alias for existing imports.
ControlPlaneDependencies = CoordinatorDependencies


@dataclass(slots=True)
class SurfaceRegistration(Generic[BlueprintT]):
    """Represents an agent surface managed by the coordinator."""

    key: str
    name: str
    blueprint_factory: Callable[[], BlueprintT]
    tools_factory: Callable[[CoordinatorDependencies, BlueprintT], Sequence[Any]]
    instruction: str
    model: Optional[str] = None


class AgentCoordinator:
    """Centralises orchestration for desk and multi-employee surfaces."""

    def __init__(self, dependencies: CoordinatorDependencies) -> None:
        self._dependencies = dependencies
        self._surfaces: Dict[str, SurfaceRegistration[Any]] = {}

    def register_surface(self, registration: SurfaceRegistration[Any]) -> None:
        """Register a new surface that can produce an ADK agent."""

        if registration.key in self._surfaces:
            raise ValueError(f"Surface {registration.key!r} already registered")
        self._surfaces[registration.key] = registration

    def build_adk_agent(self, key: str) -> ADKAgent:
        """Return an `ADKAgent` for the requested surface."""

        registration = self._require(key)
        blueprint = registration.blueprint_factory()
        llm_agent = self._build_llm_agent(registration, blueprint)
        settings = self._dependencies.settings
        use_in_memory = isinstance(self._dependencies.outbox_service, InMemoryOutboxService)

        return ADKAgent(
            adk_agent=llm_agent,
            app_name=settings.app_name,
            user_id=settings.user_id,
            session_timeout_seconds=3600,
            use_in_memory_services=use_in_memory,
        )

    def build_llm_agent(self, key: str) -> LlmAgent:
        """Return the bare `LlmAgent` for advanced orchestration scenarios."""

        registration = self._require(key)
        blueprint = registration.blueprint_factory()
        return self._build_llm_agent(registration, blueprint)

    def _build_llm_agent(
        self,
        registration: SurfaceRegistration[BlueprintT],
        blueprint: BlueprintT,
    ) -> LlmAgent:
        deps = self._dependencies
        tools = [*registration.tools_factory(deps, blueprint)]

        before_agent = build_on_before_agent(
            blueprint=blueprint,
            objectives_service=deps.objectives_service,
            outbox_service=deps.outbox_service,
            settings=deps.settings,
        )
        before_model = build_before_model_modifier(
            blueprint=blueprint,
            settings=deps.settings,
            catalog_service=deps.catalog_service,
            objectives_service=deps.objectives_service,
            audit_logger=deps.audit_logger,
            outbox_service=deps.outbox_service,
        )
        after_model = build_after_model_modifier(blueprint=blueprint)

        return LlmAgent(
            name=registration.name,
            model=registration.model or deps.settings.default_model,
            instruction=registration.instruction,
            tools=tools,
            before_agent_callback=before_agent,
            before_model_callback=before_model,
            after_model_callback=after_model,
        )

    def _require(self, key: str) -> SurfaceRegistration[Any]:
        if key not in self._surfaces:
            raise KeyError(f"Surface {key!r} is not registered with the coordinator")
        return self._surfaces[key]


__all__ = [
    "AgentCoordinator",
    "BlueprintProtocol",
    "CoordinatorDependencies",
    "ControlPlaneDependencies",
    "SurfaceRegistration",
]

