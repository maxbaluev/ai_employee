"""Tests for analytics endpoints backed by Supabase."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from agent.app import app
from agent.services.settings import AppSettings


class FakeTable:
    def __init__(self, rows):
        self._rows = list(rows)

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, column: str, value):
        self._rows = [row for row in self._rows if row.get(column) == value]
        return self

    def order(self, column: str, desc: bool = False):
        self._rows.sort(key=lambda row: row.get(column), reverse=desc)
        return self

    def limit(self, value: int):
        self._rows = self._rows[:value]
        return self

    def execute(self):
        return SimpleNamespace(data=list(self._rows))


class FakeSupabaseClient:
    def __init__(self, tables):
        # tables: dict[(schema, name)] -> rows
        self._tables = tables

    def table(self, name: str, schema: str | None = None):
        key = (schema or "public", name)
        rows = self._tables.get(key, [])
        return FakeTable(rows)


@pytest.fixture(autouse=True)
def _restore_settings():
    from agent import analytics

    original_get_settings = analytics.get_settings
    yield
    analytics.get_settings = original_get_settings


def _configure(fake_tables):
    from agent import analytics

    settings = AppSettings(
        supabase_url="https://example.supabase.co",
        supabase_service_key="service-key",
    )

    analytics.get_settings = lambda: settings
    analytics.get_supabase_client = lambda _settings: FakeSupabaseClient(fake_tables)


def test_outbox_status_counts():
    _configure({
        ("public", "outbox"): [
            {"status": "pending", "tenant_id": "tenant-demo"},
            {"status": "pending", "tenant_id": "tenant-demo"},
            {"status": "success", "tenant_id": "tenant-demo"},
        ],
        ("public", "outbox_dlq"): [
            {"status": "dlq", "tenant_id": "tenant-demo"},
            {"status": "dlq", "tenant_id": "tenant-demo"},
        ],
    })

    client = TestClient(app)
    response = client.get("/analytics/outbox/status", params={"tenant": "tenant-demo"})

    assert response.status_code == 200
    data = response.json()
    assert data["outbox"] == {"pending": 2, "success": 1}
    assert data["dlq"] == 2


def test_guardrail_events_returns_recent_rows():
    _configure({
        ("public", "audit_log"): [
            {"created_at": "2025-10-06T09:00:00Z", "tenant_id": "tenant-demo", "guardrail": "trust", "allowed": False, "reason": "low score", "actor_type": "agent"},
            {"created_at": "2025-10-05T09:00:00Z", "tenant_id": "tenant-demo", "guardrail": "scopes", "allowed": True, "reason": "", "actor_type": "agent"},
            {"created_at": "2025-10-06T08:59:00Z", "tenant_id": "other", "guardrail": "trust", "allowed": True, "reason": "", "actor_type": "agent"},
        ],
    })

    client = TestClient(app)
    response = client.get("/analytics/guardrails/recent", params={"tenant": "tenant-demo", "limit": 10})

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 2
    assert items[0]["guardrail"] == "trust"


def test_cron_runs_query():
    _configure({
        ("cron", "job_run_details"): [
            {"job_name": "catalog-sync-nightly", "status": "success", "started_at": "2025-10-06T02:00:00Z", "finished_at": "2025-10-06T02:00:05Z", "attempt": 1},
            {"job_name": "catalog-sync-nightly", "status": "failure", "started_at": "2025-10-05T02:00:00Z", "finished_at": "2025-10-05T02:00:02Z", "attempt": 1},
        ],
    })

    client = TestClient(app)
    response = client.get("/analytics/cron/jobs", params={"limit": 1})

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["status"] == "success"


def test_returns_503_when_supabase_missing():
    from agent import analytics

    analytics.get_settings = lambda: AppSettings()

    client = TestClient(app)
    response = client.get("/analytics/outbox/status")
    assert response.status_code == 503
