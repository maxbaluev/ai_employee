"""Objectives service for tenant-specific goals surfaced in prompts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Optional, Protocol, Sequence


@dataclass(slots=True)
class Objective:
    """Represents a tenant objective that guides the agent's behaviour."""

    objective_id: str
    title: str
    metric: str
    target: str
    horizon: str
    summary: str

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> "Objective":
        return cls(
            objective_id=str(record.get("id") or record.get("objective_id") or ""),
            title=str(record.get("title") or ""),
            metric=str(record.get("metric") or ""),
            target=str(record.get("target") or ""),
            horizon=str(record.get("horizon") or ""),
            summary=str(record.get("summary") or record.get("description") or ""),
        )


class ObjectivesService(Protocol):
    """Contract for fetching tenant objectives."""

    def list_objectives(self, tenant_id: str) -> Sequence[Objective]:
        ...


class InMemoryObjectivesService:
    """Static objectives used for demos and unit tests."""

    def __init__(
        self,
        *,
        objectives_by_tenant: Optional[Mapping[str, Iterable[Objective]]] = None,
    ) -> None:
        self._objectives_by_tenant = {
            tenant: tuple(objs)
            for tenant, objs in (objectives_by_tenant or {}).items()
        }

    def list_objectives(self, tenant_id: str) -> Sequence[Objective]:
        return self._objectives_by_tenant.get(tenant_id, ())


class SupabaseObjectivesService(ObjectivesService):
    """Objectives service backed by Supabase."""

    def __init__(self, client, *, schema: str = "public", table: str = "objectives") -> None:
        self._client = client
        self._schema = schema
        self._table = table

    def list_objectives(self, tenant_id: str) -> Sequence[Objective]:
        response = (
            self._table_ref()
            .select("id, title, metric, target, horizon, summary")
            .eq("tenant_id", tenant_id)
            .order("created_at", desc=True)
            .execute()
        )
        rows = getattr(response, "data", []) or []
        if not rows:
            return ()
        return tuple(Objective.from_record(row) for row in rows)

    def _table_ref(self):
        try:
            return self._client.table(self._table, schema=self._schema)
        except TypeError:  # pragma: no cover - compatibility for older client versions
            return self._client.table(self._table)


DEFAULT_OBJECTIVES = (
    Objective(
        objective_id="obj-increase-renewals",
        title="Increase renewal rate",
        metric="renewal_rate",
        target="+5% QoQ",
        horizon="Q4",
        summary="Partner with CSMs to contact at-risk customers before renewal milestones.",
    ),
    Objective(
        objective_id="obj-improve-sla",
        title="Improve support SLA",
        metric="sla_achieved",
        target=">= 95%",
        horizon="Monthly",
        summary="Ensure all priority incidents receive responses under 30 minutes.",
    ),
)
