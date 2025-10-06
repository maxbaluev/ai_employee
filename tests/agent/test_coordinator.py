"""Tests for the multi-surface agent coordinator."""

from collections import Counter

import pytest
from ag_ui_adk import ADKAgent

from agent.agents.blueprints import DeskBlueprint
from agent.agents.coordinator import AgentCoordinator, CoordinatorDependencies, SurfaceRegistration
from agent.services import (
    AppSettings,
    InMemoryCatalogService,
    InMemoryObjectivesService,
    InMemoryOutboxService,
    StructlogAuditLogger,
)


def _dependencies() -> CoordinatorDependencies:
    settings = AppSettings()
    catalog = InMemoryCatalogService(entries_by_tenant={settings.tenant_id: ()})
    objectives = InMemoryObjectivesService(objectives_by_tenant={settings.tenant_id: ()})
    outbox = InMemoryOutboxService()
    audit = StructlogAuditLogger()
    return CoordinatorDependencies(
        settings=settings,
        catalog_service=catalog,
        objectives_service=objectives,
        outbox_service=outbox,
        audit_logger=audit,
    )


def test_coordinator_builds_llm_agent_with_registration() -> None:
    deps = _dependencies()
    factory_calls = Counter()

    def blueprint_factory() -> DeskBlueprint:
        factory_calls["desk"] += 1
        return DeskBlueprint()

    coordinator = AgentCoordinator(deps)
    coordinator.register_surface(
        SurfaceRegistration(
            key="desk",
            name="DeskAgent",
            blueprint_factory=blueprint_factory,
            tools_factory=lambda *_: (),
            instruction="Coordinate multiple employees.",
            model="gemini-test",
        )
    )

    agent = coordinator.build_llm_agent("desk")

    assert agent.name == "DeskAgent"
    assert agent.instruction == "Coordinate multiple employees."
    assert agent.model == "gemini-test"
    assert factory_calls["desk"] == 1

    coordinator.build_llm_agent("desk")
    assert factory_calls["desk"] == 2


def test_register_surface_duplicate_key_raises() -> None:
    deps = _dependencies()
    coordinator = AgentCoordinator(deps)
    registration = SurfaceRegistration(
        key="desk",
        name="DeskAgent",
        blueprint_factory=DeskBlueprint,
        tools_factory=lambda *_: (),
        instruction="Duplicate",
    )
    coordinator.register_surface(registration)

    with pytest.raises(ValueError):
        coordinator.register_surface(registration)


def test_build_adk_agent_wraps_llm_agent() -> None:
    deps = _dependencies()
    coordinator = AgentCoordinator(deps)
    coordinator.register_surface(
        SurfaceRegistration(
            key="desk",
            name="DeskAgent",
            blueprint_factory=DeskBlueprint,
            tools_factory=lambda *_: (),
            instruction="Coordinate multiple employees.",
        )
    )

    adk_agent = coordinator.build_adk_agent("desk")
    assert isinstance(adk_agent, ADKAgent)
