"""Focused tests for the quiet hours guardrail."""

from __future__ import annotations

from datetime import datetime, time, timezone
from types import SimpleNamespace

from agent.guardrails.quiet_hours import check
from agent.guardrails.shared import resolve_quiet_hours_window


def _context() -> SimpleNamespace:
    """Minimum callback context double."""

    return SimpleNamespace(shared_state={})


def _clock(hour: int) -> datetime:
    return datetime(2024, 1, 1, hour, 0, tzinfo=timezone.utc)


def test_quiet_hours_blocks_inside_window() -> None:
    window, reason = resolve_quiet_hours_window(22, 6)
    result = check(
        _context(),
        quiet_window=window,
        clock=lambda: _clock(23),
        fallback_reason=reason,
    )

    assert result.allowed is False
    assert result.reason is not None
    assert "Quiet hours" in result.reason


def test_quiet_hours_allows_outside_window() -> None:
    window, reason = resolve_quiet_hours_window(8, 12)
    result = check(
        _context(),
        quiet_window=window,
        clock=lambda: _clock(7),
        fallback_reason=reason,
    )

    assert result.allowed is True
    assert result.reason is not None
    assert "Outside quiet hours" in result.reason


def test_quiet_hours_allows_when_not_configured() -> None:
    window, reason = resolve_quiet_hours_window(None, None)
    result = check(
        _context(),
        quiet_window=window,
        clock=lambda: _clock(12),
        fallback_reason=reason,
    )

    assert result.allowed is True
    assert (result.reason or "").startswith("quiet hours")


def test_quiet_hours_handles_invalid_configuration() -> None:
    window, reason = resolve_quiet_hours_window(26, 3)
    result = check(
        _context(),
        quiet_window=window,
        clock=lambda: _clock(3),
        fallback_reason=reason,
    )

    assert result.allowed is True
    assert "invalid" in (result.reason or "").lower()
