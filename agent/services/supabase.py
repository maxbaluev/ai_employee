"""Supabase client helpers for the control plane services."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

try:  # pragma: no cover - optional during unit tests without Supabase
    from supabase import Client, create_client
except ImportError:  # pragma: no cover - fail fast when dependency missing
    Client = object  # type: ignore[misc, assignment]
    create_client = None  # type: ignore[assignment]

from .settings import AppSettings


class SupabaseNotConfiguredError(RuntimeError):
    """Raised when Supabase interactions are attempted without configuration."""


@lru_cache(maxsize=1)
def get_supabase_client(settings: AppSettings) -> Client:
    """Instantiate and cache a Supabase client using the provided settings."""

    if not settings.supabase_enabled():
        raise SupabaseNotConfiguredError("Supabase credentials are not configured.")

    if create_client is None:  # pragma: no cover - runtime guard when dependency missing
        raise SupabaseNotConfiguredError(
            "supabase client library is not installed. Add 'supabase' to dependencies."
        )

    return create_client(settings.supabase_url, settings.supabase_service_key)


def reset_supabase_client_cache() -> None:
    """Clear the cached Supabase client (primarily for tests)."""

    get_supabase_client.cache_clear()

