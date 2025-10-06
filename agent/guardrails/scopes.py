"""Scope validation guardrail."""

from __future__ import annotations

from typing import Iterable, Optional, Set

try:  # pragma: no cover - optional dependency during unit tests
    from google.adk.agents.callback_context import CallbackContext
except ImportError:  # pragma: no cover
    CallbackContext = object  # type: ignore[misc]

from .shared import GuardrailResult


def check(
    ctx: CallbackContext,
    requested_scopes: Optional[Iterable[str]],
    enabled_scopes: Optional[Iterable[str]],
) -> GuardrailResult:
    """Ensure all requested scopes are enabled for the connected account."""

    _ = ctx  # Reserved for future auditing hooks

    requested = _normalise(requested_scopes)
    enabled = _normalise(enabled_scopes)

    if not requested:
        return GuardrailResult(
            "scope_validation",
            allowed=True,
            reason="no scopes requested; allowing",
        )

    missing = sorted(requested - enabled)
    if missing:
        reason = "missing scopes: " + ", ".join(missing)
        return GuardrailResult("scope_validation", allowed=False, reason=reason)

    return GuardrailResult(
        "scope_validation",
        allowed=True,
        reason="requested scopes satisfied",
    )


def _normalise(scopes: Optional[Iterable[str]]) -> Set[str]:
    if not scopes:
        return set()

    normalised: Set[str] = set()
    for raw in scopes:
        if raw is None:
            continue
        value = str(raw).strip()
        if not value:
            continue
        normalised.add(value.lower())
    return normalised

