"""Guardrail callbacks for the agent control plane."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Tuple

try:  # pragma: no cover - fail fast when google-adk is missing
    from google.adk.agents.callback_context import CallbackContext
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "google-adk must be installed to evaluate guardrails. "
        "Install the vendor package and retry."
    ) from exc

from ..services.settings import AppSettings, get_settings

from ..guardrails import resolve_quiet_hours_window
from ..guardrails.evidence import check as evidence_check
from ..guardrails.quiet_hours import check as quiet_hours_check
from ..guardrails.scopes import check as scopes_check
from ..guardrails.shared import GuardrailResult
from ..guardrails.trust import check as trust_check


def enforce_quiet_hours(
    callback_context: CallbackContext,
    *,
    settings: AppSettings | None = None,
) -> GuardrailResult:
    """Evaluate quiet hours against the configured window."""

    active_settings = settings or get_settings()
    window, reason = resolve_quiet_hours_window(
        active_settings.quiet_hours_start_hour,
        active_settings.quiet_hours_end_hour,
    )
    return quiet_hours_check(
        callback_context,
        quiet_window=window,
        clock=_utc_now,
        configuration_message=reason,
    )


def enforce_trust_threshold(
    callback_context: CallbackContext,
    *,
    settings: AppSettings | None = None,
) -> GuardrailResult:
    """Evaluate trust signals against the configured threshold."""

    active_settings = settings or get_settings()
    tenant_state = getattr(callback_context, "state", {}) or {}
    trust_state = tenant_state.get("trust") if isinstance(tenant_state, dict) else None

    approvals_ratio = None
    source = None

    if isinstance(trust_state, dict):
        approvals_ratio = trust_state.get("score")
        source = trust_state.get("source")

    return trust_check(
        callback_context,
        approvals_ratio=approvals_ratio,
        threshold=active_settings.trust_threshold,
        source=source,
    )


def enforce_scope_validation(
    callback_context: CallbackContext,
    *,
    settings: AppSettings | None = None,
) -> GuardrailResult:
    """Ensure requested scopes are enabled when enforcement is active."""

    active_settings = settings or get_settings()
    if not active_settings.enforce_scope_validation:
        return GuardrailResult(
            "scope_validation",
            allowed=True,
            reason="scope validation disabled via settings",
            metadata={
                "requestedScopes": [],
                "enabledScopes": [],
                "missingScopes": [],
            },
        )

    state = getattr(callback_context, "state", {})
    requested = None
    enabled = None
    if isinstance(state, dict):
        requested = state.get("requested_scopes")
        enabled = state.get("enabled_scopes")

    return scopes_check(
        callback_context,
        requested_scopes=requested,
        enabled_scopes=enabled,
    )


def ensure_evidence_present(
    callback_context: CallbackContext,
    *,
    settings: AppSettings | None = None,
) -> GuardrailResult:
    """Ensure a proposal contains usable supporting evidence when required."""

    active_settings = settings or get_settings()
    if not active_settings.require_evidence:
        return GuardrailResult(
            "evidence_requirement",
            allowed=True,
            reason="evidence requirement disabled via settings",
            metadata={"required": False, "missingEvidence": []},
        )

    state = getattr(callback_context, "state", {})
    proposal = state.get("proposal") if isinstance(state, dict) else None

    if proposal is None:
        return GuardrailResult(
            "evidence_requirement",
            allowed=True,
            reason="no proposal to evaluate; allowing",
            metadata={"required": True, "missingEvidence": []},
        )

    return evidence_check(callback_context, proposal)


def run_guardrails(
    callback_context: CallbackContext,
    *,
    settings: AppSettings | None = None,
) -> Tuple[GuardrailResult, ...]:
    """Evaluate all guardrails for the current invocation."""

    evaluations: Tuple[GuardrailResult, ...] = (
        enforce_quiet_hours(callback_context, settings=settings),
        enforce_trust_threshold(callback_context, settings=settings),
        enforce_scope_validation(callback_context, settings=settings),
        ensure_evidence_present(callback_context, settings=settings),
    )
    return evaluations


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
