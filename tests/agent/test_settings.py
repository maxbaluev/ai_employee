"""Tests for the pydantic-settings loader."""

from agent.services.settings import AppSettings, get_settings, reset_settings_cache


def test_settings_parse_environment(monkeypatch) -> None:
    monkeypatch.setenv("AI_EMPLOYEE_APP_NAME", "prod_app")
    monkeypatch.setenv("AI_EMPLOYEE_USER_ID", "user-42")
    monkeypatch.setenv("AI_EMPLOYEE_API_PORT", "9000")

    reset_settings_cache()
    settings = get_settings()

    assert isinstance(settings, AppSettings)
    assert settings.app_name == "prod_app"
    assert settings.user_id == "user-42"
    assert settings.api_port == 9000


def test_settings_cache_and_override(monkeypatch) -> None:
    monkeypatch.setenv("AI_EMPLOYEE_DEFAULT_MODEL", "gemini-3.0")

    reset_settings_cache()
    first = get_settings()
    second = get_settings()

    assert first is second
    assert first.default_model == "gemini-3.0"

    override = get_settings(default_model="override-model")
    assert override.default_model == "override-model"
    # cached instance remains unchanged
    assert get_settings().default_model == "gemini-3.0"
