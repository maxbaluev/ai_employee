"""Envelope schema definitions shared between the agent and worker layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, MutableMapping, Optional
from uuid import uuid4


def _as_utc(timestamp: Optional[datetime] = None) -> datetime:
    """Return a timezone-aware UTC timestamp."""

    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


@dataclass(slots=True)
class Envelope:
    """Represents a unit of work to be executed by the Outbox worker."""

    envelope_id: str
    tenant_id: str
    tool_slug: str
    arguments: Mapping[str, Any]
    connected_account_id: Optional[str]
    risk: str
    external_id: str
    trust_context: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_record(self) -> dict[str, Any]:
        """Serialise the envelope for persistence."""

        return {
            "id": self.envelope_id,
            "tenant_id": self.tenant_id,
            "tool_slug": self.tool_slug,
            "arguments": dict(self.arguments),
            "connected_account_id": self.connected_account_id,
            "risk": self.risk,
            "external_id": self.external_id,
            "trust_context": dict(self.trust_context),
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "Envelope":
        """Instantiate an envelope from a Supabase row."""

        created_at = record.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elif created_at is None:
            created_at = datetime.now(timezone.utc)
        return cls(
            envelope_id=str(record.get("id") or record.get("envelope_id") or uuid4()),
            tenant_id=str(record.get("tenant_id") or ""),
            tool_slug=str(record.get("tool_slug") or ""),
            arguments=record.get("arguments") or {},
            connected_account_id=record.get("connected_account_id"),
            risk=str(record.get("risk") or "medium"),
            external_id=str(record.get("external_id") or uuid4()),
            trust_context=record.get("trust_context") or {},
            metadata=record.get("metadata") or {},
            created_at=_as_utc(created_at),
        )

    @classmethod
    def from_payload(
        cls,
        *,
        payload: Mapping[str, Any],
        tenant_id: str,
        default_risk: str = "medium",
    ) -> "Envelope":
        """Create an envelope from a raw payload produced by the agent."""

        if not isinstance(payload, Mapping):
            raise TypeError("Envelope payload must be a mapping")

        slug = str(payload.get("tool_slug") or payload.get("slug") or "").strip()
        if not slug:
            raise ValueError("Envelope payload missing 'tool_slug'")

        arguments = payload.get("arguments")
        if not isinstance(arguments, Mapping):
            raise TypeError("Envelope payload must include 'arguments' mapping")

        connected_account_id = payload.get("connected_account_id")
        if connected_account_id is not None:
            connected_account_id = str(connected_account_id)

        risk = str(payload.get("risk") or default_risk)
        external_id = str(payload.get("external_id") or uuid4())

        trust_context = payload.get("trust_context")
        if not isinstance(trust_context, Mapping):
            trust_context = {}

        metadata = payload.get("metadata")
        if not isinstance(metadata, Mapping):
            metadata = {}

        envelope_id = str(payload.get("envelope_id") or uuid4())

        created_at = payload.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError as exc:  # pragma: no cover - defensive
                raise ValueError("Invalid ISO timestamp for 'created_at'") from exc

        timestamp = _as_utc(created_at)

        return cls(
            envelope_id=envelope_id,
            tenant_id=tenant_id,
            tool_slug=slug,
            arguments=dict(arguments),
            connected_account_id=connected_account_id,
            risk=risk,
            external_id=external_id,
            trust_context=dict(trust_context),
            metadata=dict(metadata),
            created_at=timestamp,
        )


def stash_last_envelope(state: MutableMapping[str, Any], envelope: Envelope) -> None:
    """Persist metadata about the most recent envelope to shared state."""

    outbox_state = state.setdefault("outbox", {})
    if isinstance(outbox_state, MutableMapping):
        outbox_state["last_envelope_id"] = envelope.envelope_id
        outbox_state["last_envelope_slug"] = envelope.tool_slug
        outbox_state["last_envelope_created_at"] = envelope.created_at.isoformat()
