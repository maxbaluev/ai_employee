"""Tests for the scopes guardrail."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from agent.guardrails.scopes import check


@pytest.fixture
def callback_context() -> SimpleNamespace:
    """Minimal CallbackContext double reused across scenarios."""

    return SimpleNamespace(shared_state={})


def test_scopes_blocks_missing_scope(callback_context):
    result = check(callback_context, {"crm.write", "crm.read"}, {"crm.read"})
    assert result.allowed is False
    assert "missing" in (result.reason or "").lower()


def test_scopes_allows_when_all_present(callback_context):
    result = check(callback_context, {"crm.write"}, {"crm.write", "crm.read"})
    assert result.allowed is True


def test_scopes_allows_when_requested_empty(callback_context):
    result = check(callback_context, set(), {"crm.write"})
    assert result.allowed is True


def test_scopes_allows_when_requested_none(callback_context):
    result = check(callback_context, None, {"crm.write"})
    assert result.allowed is True


def test_scopes_allows_when_enabled_none(callback_context):
    result = check(callback_context, {"crm.write"}, None)
    assert result.allowed is False
    assert "missing" in (result.reason or "").lower()


def test_scopes_case_sensitivity(callback_context):
    result = check(callback_context, {"CRM.WRITE"}, {"crm.write"})
    assert result.allowed is True


def test_scopes_trims_whitespace(callback_context):
    result = check(callback_context, {" crm.write "}, {"crm.write"})
    assert result.allowed is True
