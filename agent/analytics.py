"""Analytics endpoints backed by Supabase data."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from fastapi import APIRouter, HTTPException, Query

from agent.services import SupabaseNotConfiguredError, get_supabase_client
from agent.services.settings import AppSettings, get_settings


router = APIRouter(prefix="/analytics", tags=["analytics"])


def _require_supabase(settings: AppSettings):
    if not settings.supabase_enabled():
        raise HTTPException(status_code=503, detail="Supabase is not configured")
    try:
        return get_supabase_client(settings)
    except SupabaseNotConfiguredError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=503, detail="Supabase configuration invalid") from exc


@router.get("/outbox/status")
def outbox_status(
    tenant: str | None = Query(default=None, description="Filter results to a specific tenant"),
) -> Mapping[str, Any]:
    """Return counts for outbox statuses and DLQ backlog."""

    settings = get_settings()
    client = _require_supabase(settings)

    outbox_counts = _aggregate_statuses(
        client.table("outbox", schema=settings.supabase_schema),
        tenant=tenant,
    )
    dlq_counts = _aggregate_statuses(
        client.table("outbox_dlq", schema=settings.supabase_schema),
        tenant=tenant,
    )

    return {
        "tenantId": tenant,
        "outbox": outbox_counts,
        "dlq": sum(dlq_counts.values()),
    }


@router.get("/guardrails/recent")
def guardrail_events(
    tenant: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
) -> Mapping[str, Any]:
    """Return the most recent guardrail audit events emitted by the agent."""

    settings = get_settings()
    client = _require_supabase(settings)

    table = client.table("audit_log", schema=settings.supabase_schema)
    query = table.select("created_at, tenant_id, guardrail, allowed, reason").eq("actor_type", "agent")
    if tenant:
        query = query.eq("tenant_id", tenant)
    rows = query.order("created_at", desc=True).limit(limit).execute().data or []

    return {
        "tenantId": tenant,
        "items": rows,
    }


@router.get("/cron/jobs")
def cron_runs(
    limit: int = Query(default=20, ge=1, le=200),
) -> Mapping[str, Any]:
    """Return recent Supabase Cron job runs."""

    settings = get_settings()
    client = _require_supabase(settings)

    rows = (
        client.table("job_run_details", schema="cron")
        .select("job_name, status, started_at, finished_at, attempt")
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
        .data
        or []
    )
    return {"items": rows}


def _aggregate_statuses(table, *, tenant: str | None) -> Mapping[str, int]:
    query = table.select("status")
    if tenant:
        query = query.eq("tenant_id", tenant)
    rows = query.execute().data or []
    counter = Counter(str(row.get("status") or "unknown") for row in rows)
    return dict(counter)
