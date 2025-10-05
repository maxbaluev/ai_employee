"""Stub guardrail callbacks for the agent control plane."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Tuple

try:  # pragma: no cover - optional dependency during unit tests
    from google.adk.agents.callback_context import CallbackContext
except ImportError:  # pragma: no cover
    CallbackContext = Any  # type: ignore

from ..services.settings import get_settings


@dataclass(slots=True)
class GuardrailResult:
    """Outcome of evaluating a guardrail."""

    name: str
    allowed: bool
    reason: Optional[str] = None


def enforce_quiet_hours(callback_context: CallbackContext) -> GuardrailResult:
    """Placeholder quiet-hours guardrail that currently always allows."""

    settings = get_settings()
    _ = callback_context  # reserved for future context inspection
    if settings.quiet_hours_start_hour is None or settings.quiet_hours_end_hour is None:
        reason = "quiet hours not configured; allowing"
    else:
        reason = "quiet hours enforcement pending implementation"
    return GuardrailResult("quiet_hours", allowed=True, reason=reason)


def enforce_trust_threshold(callback_context: CallbackContext) -> GuardrailResult:
    """Placeholder trust threshold guardrail that always allows."""

    settings = get_settings()
    _ = callback_context
    reason = f"trust threshold stub accepts (threshold={settings.trust_threshold})"
    return GuardrailResult("trust_threshold", allowed=True, reason=reason)


def enforce_scope_validation(callback_context: CallbackContext) -> GuardrailResult:
    """Placeholder scope validation guardrail that always allows."""

    settings = get_settings()
    _ = callback_context
    if settings.enforce_scope_validation:
        reason = "scope validation stub allows while enforcement is pending"
    else:
        reason = "scope validation disabled via settings"
    return GuardrailResult("scope_validation", allowed=True, reason=reason)


def ensure_evidence_present(callback_context: CallbackContext) -> GuardrailResult:
    """Placeholder evidence requirement guardrail that always allows."""

    settings = get_settings()
    _ = callback_context
    if settings.require_evidence:
        reason = "evidence requirement stub allows until implemented"
    else:
        reason = "evidence requirement disabled via settings"
    return GuardrailResult("evidence_requirement", allowed=True, reason=reason)


def run_guardrails(callback_context: CallbackContext) -> Tuple[GuardrailResult, ...]:
    """Evaluate all guardrails for the current invocation."""

    evaluations: Tuple[GuardrailResult, ...] = (
        enforce_quiet_hours(callback_context),
        enforce_trust_threshold(callback_context),
        enforce_scope_validation(callback_context),
        ensure_evidence_present(callback_context),
    )
    return evaluations
