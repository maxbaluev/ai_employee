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


class _QueryRecorder:
    def __init__(self) -> None:
        self.operations: list[tuple[str, object]] = []

    def select(self, columns: str):
        self.operations.append(("select", columns))
        return self

    def eq(self, column: str, value: object):
        self.operations.append(("eq", (column, value)))
        return self

    def or_(self, expression: str):
        self.operations.append(("or", expression))
        return self

    def order(self, column: str, desc: bool = False, nullsfirst: bool = False):
        self.operations.append(("order", (column, desc, nullsfirst)))
        return self

    def limit(self, value: int):
        self.operations.append(("limit", value))
        return self

    def execute(self):
        self.operations.append(("execute", None))
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


class _QueryRecordingOutbox(SupabaseOutboxService):
    def __init__(self):
        self._client = object()
        self._schema = "public"
        self._table = "outbox"
        self._dlq_table = "outbox_dlq"
        self.recorder = _QueryRecorder()

    def _table_ref(self):  # type: ignore[override]
        return self.recorder

    def _dlq_table_ref(self):  # type: ignore[override]
        return _DummyTable([])


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


def test_list_pending_filters_next_run_and_orders():
    service = _QueryRecordingOutbox()

    result = service.list_pending(tenant_id="tenant-demo", limit=25)

    assert result == ()
    ops = service.recorder.operations
    assert ("select", "*") in ops
    assert ("eq", ("status", OutboxStatus.PENDING)) in ops
    assert ("eq", ("tenant_id", "tenant-demo")) in ops

    or_ops = [value for op, value in ops if op == "or"]
    assert any(value.startswith("next_run_at.is.null") for value in or_ops)

    order_ops = [value for op, value in ops if op == "order"]
    assert ("next_run_at", False, True) in order_ops
    assert any(entry[0] == "created_at" for entry in order_ops)

    assert ("limit", 25) in ops
