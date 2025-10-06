"""Catalog service abstractions for Composio tool metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Iterable, Mapping, Optional, Protocol, Sequence

import jsonschema
from composio import Composio
from composio_google_adk import GoogleAdkProvider


@dataclass(slots=True)
class ToolCatalogEntry:
    """Normalised representation of a Composio tool."""

    slug: str
    name: str
    description: str
    version: str
    schema: Mapping[str, Any]
    required_scopes: Sequence[str]
    risk: str = "medium"

    def validate_arguments(self, arguments: Mapping[str, Any]) -> None:
        """Validate tool arguments against the stored JSON schema."""

        jsonschema.validate(instance=arguments, schema=self.schema)

    def prompt_snippet(self) -> str:
        """Return a human-readable snippet embedded in the system prompt."""

        scope_label = ", ".join(self.required_scopes) or "none"
        schema_excerpt = json.dumps(self.schema.get("properties", {}), sort_keys=True)[:400]
        return (
            f"Tool `{self.slug}` (v{self.version}, risk={self.risk})\n"
            f"Scopes: {scope_label}\n"
            f"Description: {self.description}\n"
            f"Schema properties: {schema_excerpt}\n"
        )

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "ToolCatalogEntry":
        """Create an entry from a Supabase row."""

        required_scopes = record.get("required_scopes") or record.get("scopes") or []
        if not isinstance(required_scopes, Sequence):
            required_scopes = []

        schema_value = record.get("schema") or {}
        if not isinstance(schema_value, Mapping):
            schema_value = {}

        return cls(
            slug=str(record.get("tool_slug") or record.get("slug") or ""),
            name=str(record.get("display_name") or record.get("name") or record.get("tool_slug")),
            description=str(record.get("description") or ""),
            version=str(record.get("version") or "latest"),
            schema=dict(schema_value),
            required_scopes=list(required_scopes),
            risk=str(record.get("risk") or "medium"),
        )

    def to_record(self, *, tenant_id: str) -> dict[str, Any]:
        """Serialise the entry for persistence."""

        return {
            "tenant_id": tenant_id,
            "tool_slug": self.slug,
            "display_name": self.name,
            "description": self.description,
            "version": self.version,
            "risk": self.risk,
            "schema": self.schema,
            "required_scopes": list(self.required_scopes),
        }


class CatalogService(Protocol):
    """Contract for retrieving catalog entries."""

    def list_tools(self, tenant_id: str) -> Sequence[ToolCatalogEntry]:
        ...

    def get_tool(self, tenant_id: str, slug: str) -> Optional[ToolCatalogEntry]:
        ...


class InMemoryCatalogService:
    """Simple catalog implementation backed by an in-memory dictionary."""

    def __init__(
        self,
        *,
        entries_by_tenant: Optional[Mapping[str, Sequence[ToolCatalogEntry]]] = None,
    ) -> None:
        self._entries_by_tenant = {
            tenant: list(entries)
            for tenant, entries in (entries_by_tenant or {}).items()
        }

    def list_tools(self, tenant_id: str) -> Sequence[ToolCatalogEntry]:
        return list(self._entries_by_tenant.get(tenant_id, ()))

    def get_tool(self, tenant_id: str, slug: str) -> Optional[ToolCatalogEntry]:
        slug_lower = slug.lower()
        for entry in self.list_tools(tenant_id):
            if entry.slug.lower() == slug_lower:
                return entry
        return None

    def upsert_tool(self, tenant_id: str, entry: ToolCatalogEntry) -> None:
        entries = list(self._entries_by_tenant.get(tenant_id, ()))
        for idx, existing in enumerate(entries):
            if existing.slug.lower() == entry.slug.lower():
                entries[idx] = entry
                break
        else:
            entries.append(entry)
        self._entries_by_tenant[tenant_id] = entries


class ComposioCatalogService(CatalogService):
    """Catalog implementation backed by the Composio SDK."""

    def __init__(
        self,
        *,
        api_key: str,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_url: Optional[str] = None,
        toolkits: Sequence[str] = (),
    ) -> None:
        self._provider = GoogleAdkProvider()
        self._client = Composio(provider=self._provider, api_key=api_key)
        self._toolkits = tuple(toolkits)
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_url = redirect_url

    def list_tools(self, tenant_id: str) -> Sequence[ToolCatalogEntry]:
        entries = [_normalise_tool(tool) for tool in self._fetch_tools(tenant_id)]
        return [entry for entry in entries if entry is not None]

    def get_tool(self, tenant_id: str, slug: str) -> Optional[ToolCatalogEntry]:
        slug_lower = slug.lower()
        for entry in self.list_tools(tenant_id):
            if entry.slug.lower() == slug_lower:
                return entry
        return None

    @lru_cache(maxsize=32)
    def _fetch_tools(self, tenant_id: str) -> Sequence[Any]:
        """Retrieve tools from Composio and cache the response per tenant."""

        user_id = tenant_id
        toolkits = list(self._toolkits) if self._toolkits else None
        response = self._client.tools.get(user_id=user_id, toolkits=toolkits)
        if isinstance(response, Mapping) and "tools" in response:
            return list(response["tools"])  # type: ignore[index]
        if isinstance(response, Iterable):
            return list(response)
        return []


class SupabaseCatalogService(CatalogService):
    """Catalog implementation backed by the Supabase tool_catalog table."""

    def __init__(self, client, *, schema: str = "public", table: str = "tool_catalog") -> None:
        self._client = client
        self._schema = schema
        self._table = table

    def list_tools(self, tenant_id: str) -> Sequence[ToolCatalogEntry]:
        response = (
            self._table_ref()
            .select("tool_slug, display_name, description, version, risk, schema, required_scopes")
            .eq("tenant_id", tenant_id)
            .order("updated_at", desc=True)
            .execute()
        )
        rows = getattr(response, "data", []) or []
        return [ToolCatalogEntry.from_record(row) for row in rows if row.get("tool_slug")]

    def get_tool(self, tenant_id: str, slug: str) -> Optional[ToolCatalogEntry]:
        response = (
            self._table_ref()
            .select("tool_slug, display_name, description, version, risk, schema, required_scopes")
            .eq("tenant_id", tenant_id)
            .eq("tool_slug", slug)
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = getattr(response, "data", []) or []
        if not rows:
            return None
        return ToolCatalogEntry.from_record(rows[0])

    def upsert_tool(self, tenant_id: str, entry: ToolCatalogEntry) -> None:
        record = entry.to_record(tenant_id=tenant_id)
        self._table_ref().upsert(record).execute()

    def sync_entries(self, tenant_id: str, entries: Sequence[ToolCatalogEntry]) -> None:
        if not entries:
            return
        payload = [entry.to_record(tenant_id=tenant_id) for entry in entries]
        self._table_ref().upsert(payload).execute()

    def _table_ref(self):
        # The Supabase Python client accepts a schema kwarg; retain compatibility with older versions.
        try:
            return self._client.table(self._table, schema=self._schema)
        except TypeError:  # pragma: no cover - older client versions
            return self._client.table(self._table)


def _normalise_tool(tool: Any) -> Optional[ToolCatalogEntry]:
    """Convert a Composio tool payload into a `ToolCatalogEntry`."""

    if tool is None:
        return None

    getter = tool.get if isinstance(tool, Mapping) else getattr

    def _get(attr: str, default: Any = None) -> Any:
        if callable(getter):
            return getter(attr, default)  # type: ignore[misc]
        return getattr(tool, attr, default)

    slug = str(_get("slug", _get("tool_slug", "")))
    if not slug:
        return None

    name = str(_get("name", slug))
    description = str(_get("description", ""))
    version = str(_get("version", "1"))
    risk = str(_get("risk", "medium"))

    schema = _get("schema", {}) or _get("input_schema", {}) or {}
    if not isinstance(schema, Mapping):
        schema = {}

    scopes = _get("scopes", []) or _get("required_scopes", []) or []
    if not isinstance(scopes, Sequence):
        scopes = []

    return ToolCatalogEntry(
        slug=slug,
        name=name,
        description=description,
        version=version,
        schema=dict(schema),
        required_scopes=list(scopes),
        risk=risk,
    )
