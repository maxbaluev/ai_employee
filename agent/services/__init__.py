"""Service layer exports for the agent control plane."""

from .audit import AuditLogger, StructlogAuditLogger, SupabaseAuditLogger
from .catalog import (
    CatalogService,
    ComposioCatalogService,
    InMemoryCatalogService,
    SupabaseCatalogService,
    ToolCatalogEntry,
)
from .catalog_sync import CatalogSyncError, sync_catalog
from .objectives import (
    DEFAULT_OBJECTIVES,
    InMemoryObjectivesService,
    Objective,
    ObjectivesService,
    SupabaseObjectivesService,
)
from .outbox import (
    InMemoryOutboxService,
    OutboxRecord,
    OutboxService,
    OutboxStatus,
    SupabaseOutboxService,
)
from .settings import AppSettings, get_settings, reset_settings_cache
from .state import (
    APPROVAL_MODAL_KEY,
    DESK_STATE_KEY,
    GUARDRAIL_STATE_KEY,
    append_queue_item,
    ensure_approval_modal,
    ensure_desk_state,
    ensure_guardrail_state,
    seed_queue,
    set_approval_modal,
    write_guardrail_results,
)
from .supabase import SupabaseNotConfiguredError, get_supabase_client, reset_supabase_client_cache

__all__ = [
    "AppSettings",
    "get_settings",
    "reset_settings_cache",
    "AuditLogger",
    "StructlogAuditLogger",
    "SupabaseAuditLogger",
    "CatalogService",
    "ComposioCatalogService",
    "InMemoryCatalogService",
    "SupabaseCatalogService",
    "ToolCatalogEntry",
    "sync_catalog",
    "CatalogSyncError",
    "ObjectivesService",
    "InMemoryObjectivesService",
    "SupabaseObjectivesService",
    "Objective",
    "DEFAULT_OBJECTIVES",
    "OutboxService",
    "InMemoryOutboxService",
    "SupabaseOutboxService",
    "OutboxRecord",
    "OutboxStatus",
    "DESK_STATE_KEY",
    "GUARDRAIL_STATE_KEY",
    "APPROVAL_MODAL_KEY",
    "ensure_desk_state",
    "seed_queue",
    "append_queue_item",
    "ensure_guardrail_state",
    "write_guardrail_results",
    "ensure_approval_modal",
    "set_approval_modal",
    "get_supabase_client",
    "reset_supabase_client_cache",
    "SupabaseNotConfiguredError",
]
