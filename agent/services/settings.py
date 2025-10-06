"""Application settings powered by pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import AliasChoices, Field
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Strongly-typed configuration for the agent control plane."""

    app_name: str = "control_plane_app"
    user_id: str = "demo_user"
    tenant_id: str = "tenant-demo"
    default_model: str = "gemini-2.5-flash"
    default_toolkits: tuple[str, ...] = Field(
        default=("GITHUB",),
        validation_alias=AliasChoices(
            "composio_default_toolkits",
            "AI_EMPLOYEE_COMPOSIO_DEFAULT_TOOLKITS",
            "COMPOSIO_DEFAULT_TOOLKITS",
        ),
    )
    default_scopes: tuple[str, ...] = Field(
        default=(),
        validation_alias=AliasChoices(
            "composio_default_scopes",
            "AI_EMPLOYEE_COMPOSIO_DEFAULT_SCOPES",
            "COMPOSIO_DEFAULT_SCOPES",
        ),
    )

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    quiet_hours_start_hour: Optional[int] = None
    quiet_hours_end_hour: Optional[int] = None
    trust_threshold: float = 0.8
    enforce_scope_validation: bool = True
    require_evidence: bool = True

    composio_api_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "composio_api_key",
            "AI_EMPLOYEE_COMPOSIO_API_KEY",
            "COMPOSIO_API_KEY",
        ),
    )
    composio_client_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "composio_client_id",
            "AI_EMPLOYEE_COMPOSIO_CLIENT_ID",
            "COMPOSIO_CLIENT_ID",
        ),
    )
    composio_client_secret: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "composio_client_secret",
            "AI_EMPLOYEE_COMPOSIO_CLIENT_SECRET",
            "COMPOSIO_CLIENT_SECRET",
        ),
    )
    composio_redirect_url: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "composio_redirect_url",
            "AI_EMPLOYEE_COMPOSIO_REDIRECT_URL",
            "COMPOSIO_REDIRECT_URL",
        ),
    )

    supabase_url: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "supabase_url",
            "AI_EMPLOYEE_SUPABASE_URL",
            "SUPABASE_URL",
        ),
    )
    supabase_service_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "supabase_service_key",
            "AI_EMPLOYEE_SUPABASE_SERVICE_KEY",
            "SUPABASE_SERVICE_KEY",
        ),
    )
    supabase_anon_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "supabase_anon_key",
            "AI_EMPLOYEE_SUPABASE_ANON_KEY",
            "SUPABASE_ANON_KEY",
        ),
    )
    supabase_schema: str = "public"

    outbox_poll_interval_seconds: int = 5
    outbox_batch_size: int = 5
    outbox_max_attempts: int = 3

    @field_validator("default_toolkits", "default_scopes", mode="before")
    @classmethod
    def _parse_csv_tuple(cls, value):
        if value is None or value == "":
            return ()
        if isinstance(value, str):
            items = [part.strip() for part in value.split(",") if part.strip()]
            return tuple(items)
        if isinstance(value, (list, tuple, set)):
            return tuple(str(item).strip() for item in value if str(item).strip())
        return value

    @property
    def composio_default_scopes(self) -> tuple[str, ...]:
        return self.default_scopes

    def supabase_enabled(self) -> bool:
        """Return `True` when Supabase credentials are configured."""

        return bool(self.supabase_url and self.supabase_service_key)

    model_config = SettingsConfigDict(
        env_prefix="AI_EMPLOYEE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def get_settings(**overrides: object) -> AppSettings:
    """Return cached application settings, optionally applying overrides."""

    settings = _get_cached_settings()
    if overrides:
        return settings.model_copy(update=overrides)
    return settings


@lru_cache(maxsize=1)
def _get_cached_settings() -> AppSettings:
    return AppSettings()


def reset_settings_cache() -> None:
    """Force the next `get_settings` call to reload from the environment."""

    _get_cached_settings.cache_clear()
