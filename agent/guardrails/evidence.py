"""Evidence requirement guardrail."""

from __future__ import annotations

from typing import Any, Iterable, Optional

try:  # pragma: no cover - optional dependency during unit tests
    from google.adk.agents.callback_context import CallbackContext
except ImportError:  # pragma: no cover
    CallbackContext = object  # type: ignore[misc]

from .shared import GuardrailResult


def check(ctx: CallbackContext, proposal: Optional[dict[str, Any]]) -> GuardrailResult:
    """Validate that the proposal contains usable evidence."""

    _ = ctx  # Reserved for future audit hooks

    if _has_evidence(proposal):
        return GuardrailResult(
            "evidence_requirement",
            allowed=True,
            reason="supporting evidence present",
        )

    return GuardrailResult(
        "evidence_requirement",
        allowed=False,
        reason="missing supporting evidence",
    )


def _has_evidence(proposal: Optional[dict[str, Any]]) -> bool:
    if not proposal or not isinstance(proposal, dict):
        return False

    evidence = proposal.get("evidence")
    if evidence is None:
        return False

    if isinstance(evidence, str):
        return bool(evidence.strip())

    if isinstance(evidence, Iterable):
        for item in evidence:
            if isinstance(item, str):
                if item.strip():
                    return True
                continue
            if item not in (None, "", b""):
                return True
        return False

    # Fallback: treat other truthy types as evidence
    return bool(evidence)
