"""Utilities for synchronising the Composio catalog into Supabase."""

from __future__ import annotations

import json
import time
from typing import Iterable, Mapping, Sequence

import structlog
from tenacity import RetryError, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .catalog import (
    CatalogService,
    ComposioCatalogService,
    ToolCatalogEntry,
)
from .settings import AppSettings, get_settings
from .supabase import SupabaseNotConfiguredError, get_supabase_client


logger = structlog.get_logger(__name__)


class CatalogSyncError(RuntimeError):
    """Raised when the catalog sync cannot be completed."""


def sync_catalog(
    *,
    settings: AppSettings | None = None,
    catalog_service: CatalogService | None = None,
    remote_service: CatalogService | None = None,
) -> Mapping[str, object]:
    """Synchronise Composio catalog entries into Supabase.

    When `catalog_service` is omitted a Supabase-backed service is created automatically.
    Provide a custom `catalog_service` (for example in unit tests) to bypass Supabase.
    """

    active_settings = settings or get_settings()
    bound_logger = logger.bind(tenant_id=active_settings.tenant_id)

    target_service = catalog_service
    if target_service is None:
        if not active_settings.supabase_enabled():
            raise CatalogSyncError("Supabase credentials missing; cannot persist catalog entries")
        try:
            supabase_client = get_supabase_client(active_settings)
        except SupabaseNotConfiguredError as exc:  # pragma: no cover - defensive
            raise CatalogSyncError("Supabase misconfigured; see logs for details") from exc
        target_service = _build_supabase_catalog_service(supabase_client, active_settings)

    source_service = remote_service
    if source_service is None:
        if not active_settings.composio_api_key:
            bound_logger.warning("Skipping catalog sync; Composio API key missing")
            return {"synced": 0, "skipped": True, "reason": "missing_api_key"}

        source_service = ComposioCatalogService(
            api_key=active_settings.composio_api_key,
            client_id=active_settings.composio_client_id,
            client_secret=active_settings.composio_client_secret,
            redirect_url=active_settings.composio_redirect_url,
            toolkits=active_settings.default_toolkits,
        )

    start = time.perf_counter()

    try:
        entries = tuple(_fetch_entries(source_service, active_settings.tenant_id))
    except RetryError as exc:
        bound_logger.error("Catalog sync failed after retries", error=str(exc.last_attempt.exception()))
        raise CatalogSyncError("Failed to fetch catalog entries from Composio") from exc.last_attempt.exception()

    fetched = len(entries)
    if fetched == 0:
        bound_logger.info("No catalog entries returned from Composio; skipping persistence")
        return {"synced": 0, "skipped": False, "duration_seconds": round(time.perf_counter() - start, 3)}

    _persist_entries(target_service, active_settings.tenant_id, entries)
    duration = round(time.perf_counter() - start, 3)

    bound_logger.info(
        "Catalog sync completed",
        fetched=fetched,
        duration_seconds=duration,
        toolkits=list(active_settings.default_toolkits),
    )

    return {"synced": fetched, "skipped": False, "duration_seconds": duration}


def _build_supabase_catalog_service(client, settings: AppSettings) -> CatalogService:
    from .catalog import SupabaseCatalogService

    return SupabaseCatalogService(client, schema=settings.supabase_schema)


@retry(  # pragma: no cover - behaviour exercised via sync_catalog tests
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=8),
    reraise=True,
)
def _fetch_entries(source: CatalogService, tenant_id: str) -> Sequence[ToolCatalogEntry]:
    _clear_remote_cache(source)
    return tuple(source.list_tools(tenant_id))


def _clear_remote_cache(source: CatalogService) -> None:
    fetcher = getattr(source, "_fetch_tools", None)
    if fetcher is not None and hasattr(fetcher, "cache_clear"):
        fetcher.cache_clear()


def _persist_entries(
    target: CatalogService,
    tenant_id: str,
    entries: Iterable[ToolCatalogEntry],
) -> None:
    sync_fn = getattr(target, "sync_entries", None)
    if callable(sync_fn):
        sync_fn(tenant_id, tuple(entries))
        return

    upsert_fn = getattr(target, "upsert_tool", None)
    if callable(upsert_fn):
        for entry in entries:
            upsert_fn(tenant_id, entry)
        return

    raise CatalogSyncError("Target catalog service does not support persistence operations")


def main() -> None:
    """CLI entrypoint for Supabase Cron / manual catalog syncs."""

    result = sync_catalog()
    print(json.dumps(result, default=str))


if __name__ == "__main__":  # pragma: no cover - manual execution path
    main()

