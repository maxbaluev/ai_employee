"""Actions history projection for executed envelopes (universal envelope).

On successful execution by the worker, we persist a row in the `actions` table
for analytics and history views.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from .outbox import OutboxRecord


class ActionsService:
    def record_success(self, *, tenant_id: str, record: OutboxRecord, result: Mapping[str, Any] | None) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class SupabaseActionsService(ActionsService):
    def __init__(self, client, *, schema: str = "public", table: str = "actions") -> None:
        self._client = client
        self._schema = schema
        self._table = table

    def record_success(self, *, tenant_id: str, record: OutboxRecord, result: Mapping[str, Any] | None) -> None:
        tool = {
            "name": record.envelope.tool_slug.split("__", 1)[-1] if "__" in record.envelope.tool_slug else record.envelope.tool_slug,
            "composio_app": record.envelope.tool_slug.split("__", 1)[0] if "__" in record.envelope.tool_slug else None,
        }
        payload = {
            "tenant_id": tenant_id,
            "task_id": None,
            "employee_id": None,
            "external_id": record.envelope.external_id,
            "type": "mcp.exec",
            "tool": tool,
            "args": dict(record.envelope.arguments),
            "risk": record.envelope.risk,
            "approval": "granted",
            "constraints": {},
            "result": dict(result or {"status": "sent"}),
        }
        try:
            table = self._client.table(self._table, schema=self._schema)
        except TypeError:  # pragma: no cover
            table = self._client.table(self._table)
        # Upsert on external_id to preserve idempotency
        table.upsert(payload, on_conflict="external_id").execute()

