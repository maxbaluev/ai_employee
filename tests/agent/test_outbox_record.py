"""Tests for the shared-state projection of outbox records."""

from __future__ import annotations

from agent.schemas.envelope import Envelope
from agent.services.outbox import OutboxRecord, OutboxStatus


def _envelope(tool_slug: str = "GMAIL__drafts.create") -> Envelope:
    return Envelope(
        envelope_id="env-1",
        tenant_id="tenant-demo",
        tool_slug=tool_slug,
        arguments={"to": "user@example.com"},
        connected_account_id=None,
        risk="medium",
        external_id="ext-1",
        trust_context={},
        metadata={"title": "Compose renewal draft"},
    )


def test_outbox_record_produces_schema_compliant_queue_item() -> None:
    record = OutboxRecord(
        envelope=_envelope(),
        status=OutboxStatus.PENDING,
        attempts=2,
        last_error="previous retry failed",
        metadata={"title": "Compose renewal draft"},
    )

    shared = record.to_shared_state()

    assert set(shared.keys()) == {"id", "title", "status", "evidence"}
    assert shared["id"] == "env-1"
    assert shared["title"] == "Compose renewal draft"
    assert shared["status"] == "pending"
    assert any("Risk" in line for line in shared["evidence"])
    assert any("Queued" in line for line in shared["evidence"])


def test_outbox_record_humanises_slug_when_title_missing() -> None:
    record = OutboxRecord(
        envelope=_envelope(tool_slug="SLACK__chat.postMessage"),
        status=OutboxStatus.SUCCESS,
    )

    shared = record.to_shared_state()

    assert shared["status"] == "approved"
    assert shared["title"].startswith("Slack")
