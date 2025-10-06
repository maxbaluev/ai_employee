"""Trust threshold guardrail implementation."""

from __future__ import annotations

from typing import Any, Optional

try:  # pragma: no cover - optional dependency during unit tests
    from google.adk.agents.callback_context import CallbackContext
except ImportError:  # pragma: no cover
    CallbackContext = Any  # type: ignore[misc]

from .shared import GuardrailResult


def check(
    ctx: CallbackContext,
    approvals_ratio: Optional[float],
    threshold: float,
    *,
    source: Optional[str] = None,
) -> GuardrailResult:
    """Evaluate the configured trust threshold.

    Args:
        ctx: The ADK callback context (currently unused, reserved for future signals).
        approvals_ratio: Historical approval ratio expressed as 0–1. ``None`` is treated
            as ``0.0`` so we fail closed until data is available.
        threshold: Minimum ratio (0–1) required to auto-run without human approval.
        source: Optional descriptor for the trust signal source, surfaced in the reason.
    """

    _ = ctx  # Reserved for future use, e.g. audit hooks

    if not 0.0 <= threshold <= 1.0:
        raise ValueError("trust threshold must be between 0.0 and 1.0 inclusive")

    missing_signal = approvals_ratio is None
    ratio = approvals_ratio if approvals_ratio is not None else 0.0

    # Clamp extreme values defensively so messaging stays sane.
    if ratio < 0.0:
        ratio = 0.0
    elif ratio > 1.0:
        ratio = 1.0

    if ratio < threshold:
        reason = _format_reason(
            f"Trust score {ratio:.4f} below threshold {threshold:.4f}",
            source,
            missing=missing_signal,
        )
        return GuardrailResult("trust_threshold", allowed=False, reason=reason)

    reason = _format_reason(
        f"Trust score {ratio:.4f} meets threshold {threshold:.4f}",
        source,
        missing=missing_signal,
    )
    return GuardrailResult("trust_threshold", allowed=True, reason=reason)


def _format_reason(message: str, source: Optional[str], *, missing: bool) -> str:
    suffix_parts: list[str] = []
    if missing:
        suffix_parts.append("original score missing; treated as 0.0")
    if source:
        suffix_parts.append(f"source={source}")

    if suffix_parts:
        return f"{message} ({'; '.join(suffix_parts)})"
    return message
