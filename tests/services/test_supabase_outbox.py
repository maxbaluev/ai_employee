"""Behavioural tests for Supabase-backed outbox mutations."""

from __future__ import annotations

from types import SimpleNamespace

from agent.schemas.envelope import Envelope
from agent.services.outbox import OutboxRecord, OutboxStatus, SupabaseOutboxService


def _envelope() -> Envelope:
    return Envelope(
        envelope_id="env-123",
        tenant_id="tenant-demo",
        tool_slug="GMAIL__drafts.create",
        arguments={"to": "user@example.com"},
        connected_account_id=None,
        risk="medium",
        external_id="ext-1",
        trust_context={},
        metadata={"title": "Draft outreach"},
    )


class _DummyTable:
    def __init__(self, sink: list[dict[str, object]]):
        self._sink = sink

    def upsert(self, payload: dict[str, object]):
        self._sink.append(payload)
        return self

    def execute(self):
        return SimpleNamespace(data=[])


class _RecordingSupabaseOutbox(SupabaseOutboxService):
    def __init__(self, record: OutboxRecord | None):
        # Bypass parent initialiser; we inject stubs directly.
        self._client = object()
        self._schema = "public"
        self._table = "outbox"
        self._dlq_table = "outbox_dlq"
        self._record = record
        self.updated: list[tuple[str, dict[str, object]]] = []
        self.dlq: list[dict[str, object]] = []

    def get(self, envelope_id: str) -> OutboxRecord | None:  # type: ignore[override]
        return self._record

    def _update(self, envelope_id: str, payload: dict[str, object]) -> None:  # type: ignore[override]
        self.updated.append((envelope_id, payload))

    def _table_ref(self):  # type: ignore[override]
        return _DummyTable([])

    def _dlq_table_ref(self):  # type: ignore[override]
        return _DummyTable(self.dlq)


def test_mark_success_merges_metadata() -> None:
    record = OutboxRecord(
        envelope=_envelope(),
        status=OutboxStatus.PENDING,
        attempts=1,
        metadata={"seed": "value"},
    )
    service = _RecordingSupabaseOutbox(record)

    service.mark_success("env-123", result={"result": "ok"})

    assert service.updated
    _, payload = service.updated[-1]
    assert payload["status"] == OutboxStatus.SUCCESS
    assert payload["metadata"] == {"seed": "value", "result": "ok"}
    assert payload["attempts"] == 1
    assert payload["next_run_at"] is None


def test_mark_failure_increments_attempts_and_preserves_metadata() -> None:
    record = OutboxRecord(
        envelope=_envelope(),
        status=OutboxStatus.PENDING,
        attempts=2,
        metadata={"seed": "value"},
    )
    service = _RecordingSupabaseOutbox(record)

    service.mark_failure("env-123", error="boom", retry_in=30, move_to_dlq=False)

    assert service.updated
    _, payload = service.updated[-1]
    assert payload["status"] == OutboxStatus.FAILED
    assert payload["attempts"] == 3
    assert payload["metadata"] == {"seed": "value"}
    assert payload["next_run_at"] is not None


def test_mark_failure_moves_to_dlq() -> None:
    record = OutboxRecord(
        envelope=_envelope(),
        status=OutboxStatus.PENDING,
        attempts=0,
        metadata={"seed": "value"},
    )
    service = _RecordingSupabaseOutbox(record)

    service.mark_failure("env-123", error="conflict", retry_in=None, move_to_dlq=True)

    assert service.updated
    _, payload = service.updated[-1]
    assert payload["status"] == OutboxStatus.DLQ
    assert payload["attempts"] == 1
    assert payload["metadata"] == {"seed": "value"}
    assert not payload.get("next_run_at")

    assert service.dlq
    dlq_payload = service.dlq[-1]
    assert dlq_payload["status"] == OutboxStatus.DLQ
    assert dlq_payload["attempts"] == 1
    assert dlq_payload["metadata"] == {"seed": "value"}
