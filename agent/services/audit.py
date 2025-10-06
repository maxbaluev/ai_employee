"""Audit logging utilities used by the control plane."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Protocol

import structlog


class AuditLogger(Protocol):
    """Surface audit events for guardrail decisions and envelope changes."""

    def log_guardrail(
        self,
        *,
        tenant_id: str,
        name: str,
        allowed: bool,
        reason: Optional[str],
    ) -> None:
        ...

    def log_envelope(
        self,
        *,
        tenant_id: str,
        envelope_id: str,
        tool_slug: str,
        status: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        ...


class StructlogAuditLogger(AuditLogger):
    """Audit logger backed by structlog."""

    def __init__(self, *, logger: Optional[structlog.BoundLogger] = None) -> None:
        self._logger = logger or structlog.get_logger("audit")

    def log_guardrail(
        self,
        *,
        tenant_id: str,
        name: str,
        allowed: bool,
        reason: Optional[str],
    ) -> None:
        self._logger.bind(tenant_id=tenant_id, guardrail=name).info(
            "guardrail.evaluated",
            allowed=allowed,
            reason=reason,
        )

    def log_envelope(
        self,
        *,
        tenant_id: str,
        envelope_id: str,
        tool_slug: str,
        status: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        self._logger.bind(tenant_id=tenant_id, envelope_id=envelope_id, tool_slug=tool_slug).info(
            "outbox.envelope",
            status=status,
            metadata=dict(metadata or {}),
        )


class SupabaseAuditLogger(AuditLogger):
    """Persist audit trail entries to Supabase."""

    def __init__(
        self,
        client,
        *,
        schema: str = "public",
        table: str = "audit_log",
        actor_type: str = "agent",
        actor_id: str = "control-plane",
    ) -> None:
        self._client = client
        self._schema = schema
        self._table = table
        self._actor_type = actor_type
        self._actor_id = actor_id

    def log_guardrail(
        self,
        *,
        tenant_id: str,
        name: str,
        allowed: bool,
        reason: Optional[str],
    ) -> None:
        payload = {
            "guardrail": name,
            "allowed": allowed,
            "reason": reason,
        }
        self._insert(
            tenant_id=tenant_id,
            category="guardrail",
            payload=payload,
        )

    def log_envelope(
        self,
        *,
        tenant_id: str,
        envelope_id: str,
        tool_slug: str,
        status: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        payload = {
            "envelope_id": envelope_id,
            "tool_slug": tool_slug,
            "status": status,
            "metadata": dict(metadata or {}),
        }
        self._insert(
            tenant_id=tenant_id,
            category="outbox",
            payload=payload,
        )

    def _insert(self, *, tenant_id: str, category: str, payload: Mapping[str, Any]) -> None:
        record = {
            "tenant_id": tenant_id,
            "category": category,
            "payload": dict(payload),
            "actor_type": self._actor_type,
            "actor_id": self._actor_id,
        }
        self._table_ref().insert(record).execute()

    def _table_ref(self):
        try:
            return self._client.table(self._table, schema=self._schema)
        except TypeError:  # pragma: no cover
            return self._client.table(self._table)
