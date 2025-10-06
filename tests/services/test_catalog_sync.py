"""Tests for the catalog synchronisation job."""

import pytest

from agent.services.catalog import CatalogService, ToolCatalogEntry
from agent.services.catalog_sync import CatalogSyncError, sync_catalog
from agent.services.settings import AppSettings


class _RecordingCatalogService:
    def __init__(self) -> None:
        self.synced: list[tuple[str, tuple[ToolCatalogEntry, ...]]] = []

    def list_tools(self, tenant_id: str):  # pragma: no cover - not used in tests
        return []

    def get_tool(self, tenant_id: str, slug: str):  # pragma: no cover - not used
        return None

    def sync_entries(self, tenant_id: str, entries: tuple[ToolCatalogEntry, ...]) -> None:
        self.synced.append((tenant_id, entries))


class _UpsertOnlyCatalogService:
    def __init__(self) -> None:
        self.upserts: list[tuple[str, ToolCatalogEntry]] = []

    def list_tools(self, tenant_id: str):  # pragma: no cover - not used
        return []

    def get_tool(self, tenant_id: str, slug: str):  # pragma: no cover - not used
        return None

    def upsert_tool(self, tenant_id: str, entry: ToolCatalogEntry) -> None:
        self.upserts.append((tenant_id, entry))


class _StaticRemoteCatalog(CatalogService):
    def __init__(self, entries: list[ToolCatalogEntry]) -> None:
        self._entries = entries

    def list_tools(self, tenant_id: str):
        return list(self._entries)

    def get_tool(self, tenant_id: str, slug: str):  # pragma: no cover - not used
        for entry in self._entries:
            if entry.slug == slug:
                return entry
        return None


def _entry(slug: str) -> ToolCatalogEntry:
    return ToolCatalogEntry(
        slug=slug,
        name=f"Tool {slug}",
        description="desc",
        version="1",
        schema={"type": "object"},
        required_scopes=("scope",),
        risk="low",
    )


def test_sync_catalog_uses_sync_entries_when_available() -> None:
    target = _RecordingCatalogService()
    remote = _StaticRemoteCatalog([_entry("foo"), _entry("bar")])

    result = sync_catalog(settings=AppSettings(), catalog_service=target, remote_service=remote)

    assert result["synced"] == 2
    assert target.synced
    tenant, entries = target.synced[0]
    assert tenant == AppSettings().tenant_id
    assert {entry.slug for entry in entries} == {"foo", "bar"}


def test_sync_catalog_falls_back_to_upsert() -> None:
    target = _UpsertOnlyCatalogService()
    remote = _StaticRemoteCatalog([_entry("foo")])

    result = sync_catalog(settings=AppSettings(), catalog_service=target, remote_service=remote)

    assert result["synced"] == 1
    assert target.upserts[0][1].slug == "foo"


def test_sync_catalog_skips_when_api_key_missing() -> None:
    target = _RecordingCatalogService()

    result = sync_catalog(settings=AppSettings(), catalog_service=target)

    assert result["skipped"] is True
    assert result["synced"] == 0


def test_sync_catalog_requires_supabase_when_target_missing() -> None:
    remote = _StaticRemoteCatalog([_entry("foo")])

    with pytest.raises(CatalogSyncError):
        sync_catalog(settings=AppSettings(), remote_service=remote)

