"""Tests for the trust threshold guardrail."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from agent.guardrails import trust
from agent.callbacks.guardrails import enforce_trust_threshold


@pytest.fixture
def callback_context() -> SimpleNamespace:
    """Minimal CallbackContext double used by guardrail helpers."""

    return SimpleNamespace(shared_state={})


def _check(callback_context, *, approvals_ratio: float | None, threshold: float, source: str | None = None):
    return trust.check(
        callback_context,
        approvals_ratio=approvals_ratio,
        threshold=threshold,
        source=source,
    )


def test_trust_blocks_below_threshold(callback_context):
    result = _check(callback_context, approvals_ratio=0.55, threshold=0.80)
    assert result.allowed is False
    assert "below" in (result.reason or "").lower()


def test_trust_allows_at_exact_threshold(callback_context):
    result = _check(callback_context, approvals_ratio=0.80, threshold=0.80)
    assert result.allowed is True


def test_trust_allows_above_threshold(callback_context):
    result = _check(callback_context, approvals_ratio=0.95, threshold=0.80)
    assert result.allowed is True


def test_trust_treats_missing_score_as_zero(callback_context):
    result = _check(callback_context, approvals_ratio=None, threshold=0.75)
    assert result.allowed is False
    assert "missing" in (result.reason or "").lower()


def test_trust_rejects_threshold_below_zero(callback_context):
    with pytest.raises(ValueError):
        trust.check(callback_context, approvals_ratio=0.5, threshold=-0.1)


def test_trust_rejects_threshold_above_one(callback_context):
    with pytest.raises(ValueError):
        trust.check(callback_context, approvals_ratio=0.5, threshold=1.2)


def test_trust_blocks_rounding_boundary(callback_context):
    result = _check(callback_context, approvals_ratio=0.7999, threshold=0.80)
    assert result.allowed is False
    assert "below" in (result.reason or "").lower()


def test_trust_allows_when_source_provided(callback_context):
    result = _check(callback_context, approvals_ratio=0.90, threshold=0.80, source="tenant_metrics")
    assert result.allowed is True
    assert "source=tenant_metrics" in (result.reason or "")


def test_enforce_trust_blocks_when_score_missing():
    ctx = SimpleNamespace(state={})
    result = enforce_trust_threshold(ctx)
    assert result.allowed is False
    assert "missing" in (result.reason or "").lower()
