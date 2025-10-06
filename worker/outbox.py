"""Outbox worker CLI for executing queued envelopes via Composio."""

from __future__ import annotations

import argparse
import signal
import sys
import time
from typing import Any, Mapping, Optional, Sequence

import structlog
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from agent.schemas.envelope import Envelope
from agent.services import (
    AppSettings,
    OutboxService,
    OutboxStatus,
    SupabaseAuditLogger,
    SupabaseNotConfiguredError,
    SupabaseOutboxService,
    get_settings,
    get_supabase_client,
)

try:  # pragma: no cover - optional dependency during tests
    from composio import Composio
    from composio_google_adk import GoogleAdkProvider
except ImportError:  # pragma: no cover - graceful degradation when Composio not available
    Composio = None  # type: ignore[assignment]
    GoogleAdkProvider = None  # type: ignore[assignment]


logger = structlog.get_logger("outbox.worker")


class OutboxConflictError(RuntimeError):
    """Raised when Composio reports a provider conflict (HTTP 409)."""


def _should_retry(exception: BaseException) -> bool:
    return not isinstance(exception, OutboxConflictError)


class OutboxWorker:
    """Processes pending envelopes and executes them via Composio."""

    def __init__(
        self,
        *,
        settings: AppSettings,
        outbox_service: OutboxService,
        audit_logger: SupabaseAuditLogger,
        composio_client: Any | None,
    ) -> None:
        self._settings = settings
        self._outbox = outbox_service
        self._audit = audit_logger
        self._composio = composio_client
        self._poll_interval = settings.outbox_poll_interval_seconds
        self._batch_size = settings.outbox_batch_size
        self._max_attempts = max(1, settings.outbox_max_attempts)

    def run_forever(self) -> None:
        logger.info("worker.start", poll_interval=self._poll_interval)
        stop = False

        def _handle_signal(signum, _frame):
            nonlocal stop
            logger.info("worker.stop_requested", signal=signum)
            stop = True

        signal.signal(signal.SIGINT, _handle_signal)
        signal.signal(signal.SIGTERM, _handle_signal)

        while not stop:
            processed = self.process_once()
            if processed == 0:
                time.sleep(self._poll_interval)

        logger.info("worker.stopped")

    def process_once(self) -> int:
        records = self._outbox.list_pending(limit=self._batch_size)
        count = 0
        for record in records:
            self._process_record(record)
            count += 1
        return count

    def status(self, *, tenant_id: Optional[str] = None) -> Mapping[str, int]:
        pending = self._outbox.list_pending(tenant_id=tenant_id, limit=1000)
        dlq = self._outbox.list_dlq(tenant_id=tenant_id, limit=1000)
        stats = {
            "pending": len(pending),
            "dlq": len(dlq),
        }
        logger.info("worker.status", tenant_id=tenant_id, **stats)
        return stats

    def drain_dlq(self, *, tenant_id: Optional[str], limit: int) -> int:
        drained = 0
        records = self._outbox.list_dlq(tenant_id=tenant_id, limit=limit)
        for record in records:
            if self._outbox.requeue_from_dlq(record.envelope.envelope_id):
                drained += 1
        logger.info("worker.drain", tenant_id=tenant_id, drained=drained)
        return drained

    def retry_dlq(self, *, tenant_id: str, envelope_id: str) -> bool:
        record = self._outbox.requeue_from_dlq(envelope_id)
        if record is None:
            logger.warning("worker.retry_dlq_missing", tenant_id=tenant_id, envelope_id=envelope_id)
            return False
        logger.info("worker.retry_dlq", tenant_id=tenant_id, envelope_id=envelope_id)
        return True

    def _process_record(self, record) -> None:
        envelope_id = record.envelope.envelope_id
        self._outbox.mark_in_progress(envelope_id)
        logger.info(
            "worker.process",
            envelope_id=envelope_id,
            tool=record.envelope.tool_slug,
            tenant=record.tenant_id,
        )
        try:
            result = self._execute_with_retry(record)
        except OutboxConflictError as exc:
            reason = str(exc)
            self._outbox.mark_conflict(envelope_id, reason=reason)
            self._audit.log_envelope(
                tenant_id=record.tenant_id,
                envelope_id=envelope_id,
                tool_slug=record.envelope.tool_slug,
                status=OutboxStatus.CONFLICT,
                metadata={"reason": reason},
            )
            logger.warning("worker.conflict", envelope_id=envelope_id, reason=reason)
        except Exception as exc:  # pragma: no cover - defensive path
            reason = str(exc)
            self._outbox.mark_failure(
                envelope_id,
                error=reason,
                retry_in=None,
                move_to_dlq=True,
            )
            self._audit.log_envelope(
                tenant_id=record.tenant_id,
                envelope_id=envelope_id,
                tool_slug=record.envelope.tool_slug,
                status=OutboxStatus.DLQ,
                metadata={"error": reason},
            )
            logger.exception("worker.failure", envelope_id=envelope_id)
        else:
            metadata = result if isinstance(result, Mapping) else {"result": result}
            self._outbox.mark_success(envelope_id, result=metadata)
            self._audit.log_envelope(
                tenant_id=record.tenant_id,
                envelope_id=envelope_id,
                tool_slug=record.envelope.tool_slug,
                status=OutboxStatus.SUCCESS,
                metadata=metadata,
            )
            logger.info("worker.success", envelope_id=envelope_id)

    def _execute_once(self, record) -> Mapping[str, Any] | Any:
        if self._composio is None:
            raise RuntimeError("Composio client is not configured")

        kwargs: dict[str, Any] = {
            "user_id": record.tenant_id,
            "tool_slug": record.envelope.tool_slug,
            "arguments": dict(record.envelope.arguments),
            "external_id": record.envelope.external_id,
        }
        if record.envelope.connected_account_id:
            kwargs["connected_account_id"] = record.envelope.connected_account_id

        try:
            return self._composio.tools.execute(**kwargs)
        except Exception as exc:  # pragma: no cover - real execution depends on Composio
            if _is_conflict(exc):
                raise OutboxConflictError(str(exc)) from exc
            raise

    def _execute_with_retry(self, record):
        @retry(
            reraise=True,
            retry=retry_if_exception(_should_retry),
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_exponential(multiplier=1, min=1, max=30),
        )
        def _runner():
            return self._execute_once(record)

        return _runner()


def _is_conflict(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    if status == 409:
        return True
    message = str(exc).lower()
    return "conflict" in message or "409" in message


def build_composio_client(settings: AppSettings) -> Any | None:
    if not settings.composio_api_key or Composio is None or GoogleAdkProvider is None:
        if not settings.composio_api_key:
            logger.warning("worker.composio_not_configured")
        return None

    provider = GoogleAdkProvider()
    return Composio(provider=provider, api_key=settings.composio_api_key)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Outbox worker CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start", help="Run the worker loop")
    start_parser.add_argument("--once", action="store_true", help="Process a single batch then exit")

    status_parser = subparsers.add_parser("status", help="Print queue statistics")
    status_parser.add_argument("--tenant", help="Filter by tenant id", default=None)

    drain_parser = subparsers.add_parser("drain", help="Requeue envelopes from the DLQ")
    drain_parser.add_argument("--tenant", default=None)
    drain_parser.add_argument("--limit", type=int, default=50)

    retry_parser = subparsers.add_parser("retry-dlq", help="Retry a specific DLQ envelope")
    retry_parser.add_argument("--tenant", required=True)
    retry_parser.add_argument("--envelope", required=True)

    return parser.parse_args(argv)


def build_worker(settings: AppSettings) -> OutboxWorker:
    if not settings.supabase_enabled():
        raise SupabaseNotConfiguredError("Supabase credentials are required for the worker")

    client = get_supabase_client(settings)
    outbox_service = SupabaseOutboxService(client, schema=settings.supabase_schema)
    audit_logger = SupabaseAuditLogger(client, schema=settings.supabase_schema, actor_type="worker", actor_id="outbox")
    composio_client = build_composio_client(settings)

    return OutboxWorker(
        settings=settings,
        outbox_service=outbox_service,
        audit_logger=audit_logger,
        composio_client=composio_client,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    settings = get_settings()

    try:
        worker = build_worker(settings)
    except SupabaseNotConfiguredError as exc:
        logger.error("worker.supabase_missing", error=str(exc))
        return 1

    if args.command == "start":
        if args.once:
            processed = worker.process_once()
            logger.info("worker.batch_complete", processed=processed)
        else:
            worker.run_forever()
        return 0

    if args.command == "status":
        stats = worker.status(tenant_id=getattr(args, "tenant", None))
        print(f"pending={stats['pending']} dlq={stats['dlq']}")
        return 0

    if args.command == "drain":
        drained = worker.drain_dlq(tenant_id=getattr(args, "tenant", None), limit=args.limit)
        print(f"drained={drained}")
        return 0

    if args.command == "retry-dlq":
        success = worker.retry_dlq(tenant_id=args.tenant, envelope_id=args.envelope)
        return 0 if success else 2

    logger.error("worker.unknown_command", command=args.command)
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
