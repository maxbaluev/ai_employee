"""Shared primitives for guardrail implementations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timezone
from typing import Optional, Tuple


@dataclass(slots=True)
class GuardrailResult:
    """Represents the outcome of evaluating a guardrail."""

    name: str
    allowed: bool
    reason: Optional[str] = None


def resolve_quiet_hours_window(
    start_hour: Optional[int],
    end_hour: Optional[int],
) -> Tuple[Optional[Tuple[time, time]], Optional[str]]:
    """Normalise quiet hours configuration and capture validation errors."""

    if start_hour is None or end_hour is None:
        return None, "quiet hours not configured; allowing"

    if not _valid_hour(start_hour) or not _valid_hour(end_hour):
        return None, "invalid quiet hours configuration; allowing"

    if start_hour == end_hour:
        return None, "quiet hours start and end match; allowing"

    start = time(start_hour, tzinfo=timezone.utc)
    end = time(end_hour, tzinfo=timezone.utc)
    return (start, end), None


def ensure_aware(moment: datetime) -> datetime:
    """Return a timezone-aware datetime (defaults to UTC)."""

    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def format_quiet_window(window: Tuple[time, time]) -> str:
    start, end = window
    label = f"{start.hour:02d}:00-{end.hour:02d}:00 UTC"
    if start.hour > end.hour:
        return f"{label} (overnight)"
    return label


def in_quiet_window(moment: datetime, window: Tuple[time, time]) -> bool:
    """Check whether the provided moment falls within the quiet window."""

    start, end = window
    hour = moment.hour
    if start.hour < end.hour:
        return start.hour <= hour < end.hour
    return hour >= start.hour or hour < end.hour


def _valid_hour(hour: int) -> bool:
    return 0 <= hour <= 23

