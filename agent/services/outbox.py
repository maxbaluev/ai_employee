"""Outbox service implementations for queuing and executing envelopes."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping, MutableMapping, Optional, Protocol, Sequence

from agent.schemas.envelope import Envelope


class OutboxStatus:
    """Enumeration of outbox statuses used across the control plane."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CONFLICT = "conflict"
    DLQ = "dlq"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class OutboxRecord:
    """Represents an envelope persisted to the outbox queue."""

    envelope: Envelope
    status: str = OutboxStatus.PENDING
    attempts: int = 0
    last_error: Optional[str] = None
    queued_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)
    next_run_at: Optional[datetime] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    dlq: bool = False

    @property
    def tenant_id(self) -> str:
        return self.envelope.tenant_id

    def mark_attempt(self, *, error: Optional[str] = None, retry_at: Optional[datetime] = None) -> None:
        self.attempts += 1
        self.last_error = error
        self.next_run_at = retry_at
        self.updated_at = _utc_now()

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "OutboxRecord":
        envelope = Envelope.from_record(record.get("envelope") or record)
        status = str(record.get("status") or OutboxStatus.PENDING)
        attempts = int(record.get("attempts") or 0)
        last_error = record.get("last_error")
        queued_at = record.get("queued_at") or record.get("created_at")
        updated_at = record.get("updated_at") or queued_at
        next_run_at = record.get("next_run_at")
        metadata = record.get("metadata") or {}
        dlq = str(record.get("status") or "").lower() == OutboxStatus.DLQ or bool(record.get("dlq"))

        def _parse(value: Any) -> datetime:
            if isinstance(value, datetime):
                return value.astimezone(timezone.utc)
            if isinstance(value, str) and value:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
            return _utc_now()

        return cls(
            envelope=envelope,
            status=status,
            attempts=attempts,
            last_error=last_error,
            queued_at=_parse(queued_at),
            updated_at=_parse(updated_at),
            next_run_at=_parse(next_run_at) if next_run_at else None,
            metadata=metadata,
            dlq=dlq,
        )

    def to_shared_state(self) -> Mapping[str, Any]:
        evidence: list[str] = []
        evidence.append(f"Tool: {self.envelope.tool_slug}")
        evidence.append(f"Risk: {self.envelope.risk}")
        evidence.append(f"Queued: {self.queued_at.isoformat()}")
        if self.attempts:
            evidence.append(f"Attempts: {self.attempts}")
        if self.last_error:
            evidence.append(f"Error: {self.last_error}")

        status = _map_outbox_status(self.status)

        title = (
            str(self.metadata.get("title"))
            if isinstance(self.metadata, Mapping) and self.metadata.get("title")
            else _humanise_slug(self.envelope.tool_slug)
        )

        return {
            "id": self.envelope.envelope_id,
            "title": title,
            "status": status,
            "evidence": evidence,
        }


def _map_outbox_status(status: str) -> str:
    if status == OutboxStatus.SUCCESS:
        return "approved"
    if status in {OutboxStatus.FAILED, OutboxStatus.DLQ, OutboxStatus.CONFLICT}:
        return "rejected"
    return "pending"


def _humanise_slug(slug: str) -> str:
    if not slug:
        return "Queued Envelope"

    if "__" in slug:
        provider, remainder = slug.split("__", 1)
        provider_label = provider.replace("_", " ").title()
        action_label = remainder.replace(".", " ").replace("_", " ").title()
        return f"{provider_label} · {action_label}".strip()

    return slug.replace(".", " ").replace("_", " ").title() or "Queued Envelope"


class OutboxService(Protocol):
    """Interface for queueing envelopes and tracking their lifecycle."""

    def enqueue(self, envelope: Envelope, *, metadata: Mapping[str, Any] | None = None) -> OutboxRecord:
        ...

    def get(self, envelope_id: str) -> Optional[OutboxRecord]:
        ...

    def list_pending(self, *, tenant_id: str | None = None, limit: int = 50) -> Sequence[OutboxRecord]:
        ...

    def list_dlq(self, *, tenant_id: str | None = None, limit: int = 50) -> Sequence[OutboxRecord]:
        ...

    def mark_in_progress(self, envelope_id: str) -> None:
        ...

    def mark_success(self, envelope_id: str, *, result: Mapping[str, Any] | None = None) -> None:
        ...

    def mark_failure(
        self,
        envelope_id: str,
        *,
        error: str,
        retry_in: Optional[int] = None,
        move_to_dlq: bool = False,
    ) -> None:
        ...

    def mark_conflict(self, envelope_id: str, *, reason: str) -> None:
        ...

    def requeue_from_dlq(self, envelope_id: str) -> Optional[OutboxRecord]:
        ...

    def defer(self, envelope_id: str, *, retry_in: int) -> None:
        """Reschedule a pending envelope without marking it as a failure.

        Implementations should set `next_run_at = now + retry_in` and keep status
        as `pending` so normal polling logic will pick it up later.
        """
        ...


class InMemoryOutboxService(OutboxService):
    """Queues envelopes in memory for local development and unit tests."""

    def __init__(self) -> None:
        self._records: "OrderedDict[str, OutboxRecord]" = OrderedDict()

    def enqueue(self, envelope: Envelope, *, metadata: Mapping[str, Any] | None = None) -> OutboxRecord:
        record = OutboxRecord(envelope=envelope, metadata=dict(metadata or {}))
        self._records[record.envelope.envelope_id] = record
        return record

    def get(self, envelope_id: str) -> Optional[OutboxRecord]:
        return self._records.get(envelope_id)

    def list_pending(self, *, tenant_id: str | None = None, limit: int = 50) -> Sequence[OutboxRecord]:
        items = [
            record
            for record in self._records.values()
            if record.status == OutboxStatus.PENDING and (tenant_id is None or record.tenant_id == tenant_id)
        ]
        return tuple(items[:limit])

    def list_dlq(self, *, tenant_id: str | None = None, limit: int = 50) -> Sequence[OutboxRecord]:
        items = [
            record
            for record in self._records.values()
            if record.dlq and (tenant_id is None or record.tenant_id == tenant_id)
        ]
        return tuple(items[:limit])

    def mark_in_progress(self, envelope_id: str) -> None:
        record = self._require(envelope_id)
        record.status = OutboxStatus.IN_PROGRESS
        record.updated_at = _utc_now()

    def mark_success(self, envelope_id: str, *, result: Mapping[str, Any] | None = None) -> None:
        record = self._require(envelope_id)
        record.status = OutboxStatus.SUCCESS
        record.metadata = {**record.metadata, "result": dict(result or {})}
        record.updated_at = _utc_now()
        record.next_run_at = None

    def mark_failure(
        self,
        envelope_id: str,
        *,
        error: str,
        retry_in: Optional[int] = None,
        move_to_dlq: bool = False,
    ) -> None:
        record = self._require(envelope_id)
        record.status = OutboxStatus.DLQ if move_to_dlq else OutboxStatus.FAILED
        record.mark_attempt(error=error, retry_at=self._retry_time(retry_in))
        record.dlq = move_to_dlq

    def mark_conflict(self, envelope_id: str, *, reason: str) -> None:
        record = self._require(envelope_id)
        record.status = OutboxStatus.CONFLICT
        record.last_error = reason
        record.updated_at = _utc_now()

    def clear(self) -> None:
        self._records.clear()

    def _require(self, envelope_id: str) -> OutboxRecord:
        if envelope_id not in self._records:
            raise KeyError(f"Envelope {envelope_id} not found in outbox")
        return self._records[envelope_id]

    @staticmethod
    def _retry_time(retry_in: Optional[int]) -> Optional[datetime]:
        if retry_in is None:
            return None
        return _utc_now() + timedelta(seconds=retry_in)

    def requeue_from_dlq(self, envelope_id: str) -> Optional[OutboxRecord]:
        record = self._records.get(envelope_id)
        if record is None:
            return None
        record.status = OutboxStatus.PENDING
        record.dlq = False
        record.last_error = None
        record.next_run_at = None
        record.attempts = 0
        record.updated_at = _utc_now()
        return record

    def defer(self, envelope_id: str, *, retry_in: int) -> None:
        record = self._require(envelope_id)
        # Keep status pending; set next attempt after the delay
        record.next_run_at = _utc_now() + timedelta(seconds=retry_in)
        record.updated_at = _utc_now()


class SupabaseOutboxService(OutboxService):
    """Supabase-backed outbox implementation."""

    def __init__(
        self,
        client,
        *,
        schema: str = "public",
        table: str = "outbox",
        dlq_table: str = "outbox_dlq",
    ) -> None:
        self._client = client
        self._schema = schema
        self._table = table
        self._dlq_table = dlq_table

    def enqueue(self, envelope: Envelope, *, metadata: Mapping[str, Any] | None = None) -> OutboxRecord:
        record = {
            **envelope.to_record(),
            "status": OutboxStatus.PENDING,
            "attempts": 0,
            "metadata": dict(metadata or {}),
            "dlq": False,
        }
        response = self._table_ref().insert(record).execute()
        inserted = (getattr(response, "data", None) or [record])[0]
        return OutboxRecord.from_record(inserted)

    def get(self, envelope_id: str) -> Optional[OutboxRecord]:
        response = self._table_ref().select("*").eq("id", envelope_id).limit(1).execute()
        rows = getattr(response, "data", []) or []
        if not rows:
            return None
        return OutboxRecord.from_record(rows[0])

    def list_pending(self, *, tenant_id: str | None = None, limit: int = 50) -> Sequence[OutboxRecord]:
        now_iso = _utc_now().isoformat()
        query = (
            self._table_ref()
            .select("*")
            .eq("status", OutboxStatus.PENDING)
        )
        if tenant_id:
            query = query.eq("tenant_id", tenant_id)

        query = (
            query
            .or_(f"next_run_at.is.null,next_run_at.lte.{now_iso}")
            .order("next_run_at", nullsfirst=True)
            .order("created_at")
            .limit(limit)
        )
        response = query.execute()
        rows = getattr(response, "data", []) or []
        return tuple(OutboxRecord.from_record(row) for row in rows)

    def list_dlq(self, *, tenant_id: str | None = None, limit: int = 50) -> Sequence[OutboxRecord]:
        query = self._dlq_table_ref().select("*")
        if tenant_id:
            query = query.eq("tenant_id", tenant_id)
        response = query.order("created_at", desc=True).limit(limit).execute()
        rows = getattr(response, "data", []) or []
        return tuple(OutboxRecord.from_record(row) for row in rows)

    def mark_in_progress(self, envelope_id: str) -> None:
        self._update(envelope_id, {"status": OutboxStatus.IN_PROGRESS, "updated_at": _utc_now().isoformat()})

    def mark_success(self, envelope_id: str, *, result: Mapping[str, Any] | None = None) -> None:
        record = self.get(envelope_id)
        metadata: dict[str, Any] = {}
        if record is not None and isinstance(record.metadata, Mapping):
            metadata.update(dict(record.metadata))
        if result is not None:
            metadata.update(dict(result))

        payload = {
            "status": OutboxStatus.SUCCESS,
            "metadata": metadata,
            "attempts": record.attempts if record is not None else 0,
            "next_run_at": None,
            "updated_at": _utc_now().isoformat(),
        }
        self._update(envelope_id, payload)

    def mark_failure(
        self,
        envelope_id: str,
        *,
        error: str,
        retry_in: Optional[int] = None,
        move_to_dlq: bool = False,
    ) -> None:
        record = self.get(envelope_id)
        attempts = 1
        metadata: dict[str, Any] = {}
        if record is not None:
            attempts = record.attempts + 1
            if isinstance(record.metadata, Mapping):
                metadata.update(dict(record.metadata))

        payload = {
            "status": OutboxStatus.DLQ if move_to_dlq else OutboxStatus.FAILED,
            "last_error": error,
            "attempts": attempts,
            "metadata": metadata,
            "updated_at": _utc_now().isoformat(),
        }
        if retry_in is not None and not move_to_dlq:
            payload["next_run_at"] = (_utc_now() + timedelta(seconds=retry_in)).isoformat()
        else:
            payload["next_run_at"] = None

        if move_to_dlq and record is not None:
            self._dlq_table_ref().upsert(
                {
                    **record.envelope.to_record(),
                    "status": OutboxStatus.DLQ,
                    "last_error": error,
                    "attempts": attempts,
                    "metadata": metadata,
                }
            ).execute()

        self._update(envelope_id, payload)

    def mark_conflict(self, envelope_id: str, *, reason: str) -> None:
        self._update(
            envelope_id,
            {
                "status": OutboxStatus.CONFLICT,
                "last_error": reason,
                "updated_at": _utc_now().isoformat(),
            },
        )

    def requeue_from_dlq(self, envelope_id: str) -> Optional[OutboxRecord]:
        dlq_response = (
            self._dlq_table_ref()
            .select("*")
            .eq("id", envelope_id)
            .limit(1)
            .execute()
        )
        dlq_rows = getattr(dlq_response, "data", []) or []
        self._update(
            envelope_id,
            {
                "status": OutboxStatus.PENDING,
                "attempts": 0,
                "last_error": None,
                "next_run_at": None,
                "updated_at": _utc_now().isoformat(),
            },
        )
        if dlq_rows:
            self._dlq_table_ref().delete().eq("id", envelope_id).execute()
        return self.get(envelope_id)

    def _update(self, envelope_id: str, payload: Mapping[str, Any]) -> None:
        self._table_ref().update(payload).eq("id", envelope_id).execute()

    def _table_ref(self):
        try:
            return self._client.table(self._table, schema=self._schema)
        except TypeError:  # pragma: no cover
            return self._client.table(self._table)

    def _dlq_table_ref(self):
        try:
            return self._client.table(self._dlq_table, schema=self._schema)
        except TypeError:  # pragma: no cover
            return self._client.table(self._dlq_table)

    def defer(self, envelope_id: str, *, retry_in: int) -> None:
        self._update(
            envelope_id,
            {
                "status": OutboxStatus.PENDING,
                "next_run_at": (_utc_now() + timedelta(seconds=retry_in)).isoformat(),
                "updated_at": _utc_now().isoformat(),
            },
        )
