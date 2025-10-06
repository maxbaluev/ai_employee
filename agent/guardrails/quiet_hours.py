"""Quiet hours guardrail implementation."""

from __future__ import annotations

from datetime import datetime, time, timezone
from typing import Callable, Optional, Tuple

try:  # pragma: no cover - optional dependency during unit tests
    from google.adk.agents.callback_context import CallbackContext
except ImportError:  # pragma: no cover
    CallbackContext = object  # type: ignore[misc]

from .shared import (
    GuardrailResult,
    ensure_aware,
    format_quiet_window,
    in_quiet_window,
)


QuietWindow = Optional[Tuple[time, time]]


def check(
    ctx: CallbackContext,
    quiet_window: QuietWindow,
    *,
    clock: Optional[Callable[[], datetime]] = None,
    configuration_message: Optional[str] = None,
) -> GuardrailResult:
    """Evaluate the quiet hours guardrail for the current invocation."""

    _ = ctx  # reserved for future context-dependent logic
    if quiet_window is None:
        message = configuration_message or "quiet hours not configured; allowing"
        return GuardrailResult(
            "quiet_hours",
            allowed=True,
            reason=message,
            metadata={"configured": False},
        )

    now = ensure_aware((clock or _utc_now)())
    window_label = format_quiet_window(quiet_window)

    if in_quiet_window(now, quiet_window):
        reason = (
            f"Quiet hours active ({window_label}); current time {now.strftime('%H:%M UTC')}"
        )
        return GuardrailResult(
            "quiet_hours",
            allowed=False,
            reason=reason,
            metadata={
                "configured": True,
                "window": window_label,
                "currentTime": now.strftime("%H:%M:%S UTC"),
            },
        )

    reason = (
        f"Outside quiet hours ({window_label}); current time {now.strftime('%H:%M UTC')}"
    )
    return GuardrailResult(
        "quiet_hours",
        allowed=True,
        reason=reason,
        metadata={
            "configured": True,
            "window": window_label,
            "currentTime": now.strftime("%H:%M:%S UTC"),
        },
    )


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
