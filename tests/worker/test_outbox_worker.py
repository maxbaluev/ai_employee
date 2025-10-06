"""Unit tests for the Outbox worker."""

from types import SimpleNamespace

from agent.schemas.envelope import Envelope
from agent.services import AppSettings
from agent.services.outbox import InMemoryOutboxService, OutboxStatus
from worker.outbox import OutboxWorker


class DummyAuditLogger:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict]] = []

    def log_envelope(self, *, tenant_id: str, envelope_id: str, tool_slug: str, status: str, metadata):
        self.events.append((status, {
            "tenant_id": tenant_id,
            "envelope_id": envelope_id,
            "tool_slug": tool_slug,
            "metadata": metadata,
        }))


class DummyComposioClient:
    def __init__(self, *, raise_conflict: bool = False, raise_error: bool = False) -> None:
        self.raise_conflict = raise_conflict
        self.raise_error = raise_error
        self.executed = []

        self.tools = SimpleNamespace(execute=self._execute)

    def _execute(self, **kwargs):
        self.executed.append(kwargs)
        if self.raise_conflict:
            raise RuntimeError("409 Conflict")
        if self.raise_error:
            raise RuntimeError("Composio unavailable")
        return {"status": "ok"}


def _enqueue_sample(outbox: InMemoryOutboxService, tenant_id: str = "tenant-demo") -> Envelope:
    payload = {
        "tool_slug": "GMAIL__drafts.create",
        "arguments": {"to": "user@example.com", "subject": "Hello", "body": "Hi"},
        "external_id": "ext-123",
    }
    envelope = Envelope.from_payload(payload=payload, tenant_id=tenant_id)
    outbox.enqueue(envelope)
    return envelope


def test_worker_process_success() -> None:
    settings = AppSettings()
    outbox = InMemoryOutboxService()
    audit = DummyAuditLogger()
    composio = DummyComposioClient()

    envelope = _enqueue_sample(outbox, tenant_id=settings.tenant_id)

    worker = OutboxWorker(
        settings=settings,
        outbox_service=outbox,
        audit_logger=audit,
        composio_client=composio,
    )

    processed = worker.process_once()

    assert processed == 1
    record = outbox.get(envelope.envelope_id)
    assert record is not None
    assert record.status == OutboxStatus.SUCCESS
    assert composio.executed != []


def test_worker_process_conflict_routes_to_conflict() -> None:
    settings = AppSettings()
    outbox = InMemoryOutboxService()
    audit = DummyAuditLogger()
    composio = DummyComposioClient(raise_conflict=True)

    envelope = _enqueue_sample(outbox, tenant_id=settings.tenant_id)

    worker = OutboxWorker(
        settings=settings,
        outbox_service=outbox,
        audit_logger=audit,
        composio_client=composio,
    )

    worker.process_once()

    record = outbox.get(envelope.envelope_id)
    assert record is not None
    assert record.status == OutboxStatus.CONFLICT


def test_worker_retry_dlq_requeues() -> None:
    settings = AppSettings()
    outbox = InMemoryOutboxService()
    audit = DummyAuditLogger()
    composio = DummyComposioClient(raise_error=True)

    envelope = _enqueue_sample(outbox, tenant_id=settings.tenant_id)
    worker = OutboxWorker(
        settings=settings,
        outbox_service=outbox,
        audit_logger=audit,
        composio_client=composio,
    )

    worker.process_once()
    record = outbox.get(envelope.envelope_id)
    assert record is not None
    assert record.status == OutboxStatus.DLQ

    assert worker.retry_dlq(tenant_id=settings.tenant_id, envelope_id=envelope.envelope_id)
    record = outbox.get(envelope.envelope_id)
    assert record is not None
    assert record.status == OutboxStatus.PENDING
