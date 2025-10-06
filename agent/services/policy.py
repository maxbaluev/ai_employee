"""Policy service for effective tool write permissions and rate buckets.

Backed by the `catalog_tools_view` created in the universal initial migration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class EffectiveToolPolicy:
    write_allowed: bool
    rate_bucket: Optional[str]
    risk: Optional[str] = None
    approval: Optional[str] = None


class PolicyService:
    def get_effective_policy(self, *, tenant_id: str, tool_slug: str) -> EffectiveToolPolicy | None:  # pragma: no cover - interface
        raise NotImplementedError


class SupabasePolicyService(PolicyService):
    def __init__(self, client, *, schema: str = "public", view: str = "catalog_tools_view") -> None:
        self._client = client
        self._schema = schema
        self._view = view

    def get_effective_policy(self, *, tenant_id: str, tool_slug: str) -> EffectiveToolPolicy | None:
        try:
            table = self._client.table(self._view, schema=self._schema)
        except TypeError:  # pragma: no cover - compat with older client
            table = self._client.table(self._view)

        resp = (
            table.select(
                "effective_write_allowed, effective_rate_bucket, effective_risk, effective_approval"
            )
            .eq("tenant_id", tenant_id)
            .eq("tool_slug", tool_slug)
            .limit(1)
            .execute()
        )
        rows = getattr(resp, "data", []) or []
        if not rows:
            return None

        row = rows[0]
        return EffectiveToolPolicy(
            write_allowed=bool(row.get("effective_write_allowed", False)),
            rate_bucket=row.get("effective_rate_bucket"),
            risk=row.get("effective_risk"),
            approval=row.get("effective_approval"),
        )

