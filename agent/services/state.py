"""Shared state helpers used by the control plane callbacks."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, MutableMapping, Sequence

from agent.schemas.envelope import Envelope
from agent.guardrails.shared import GuardrailResult


DESK_STATE_KEY = "desk"
GUARDRAIL_STATE_KEY = "guardrails"
APPROVAL_MODAL_KEY = "approvalModal"


def ensure_desk_state(state: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Ensure the desk surface state exists."""

    desk = state.get(DESK_STATE_KEY)
    if not isinstance(desk, MutableMapping):
        desk = {
            "queue": [],
            "lastUpdated": _utc_now(),
        }
        state[DESK_STATE_KEY] = desk
    else:
        desk.setdefault("queue", [])
        desk.setdefault("lastUpdated", _utc_now())
    return desk


def seed_queue(
    state: MutableMapping[str, Any],
    *,
    queue: Sequence[Mapping[str, Any]],
) -> None:
    """Replace the desk queue with the provided items."""

    desk = ensure_desk_state(state)
    desk["queue"] = [dict(item) for item in queue]
    desk["lastUpdated"] = _utc_now()


def append_queue_item(state: MutableMapping[str, Any], item: Mapping[str, Any]) -> None:
    """Append an item to the desk queue and update the timestamp."""

    desk = ensure_desk_state(state)
    queue = desk.setdefault("queue", [])
    if isinstance(queue, list):
        queue.append(dict(item))
    desk["lastUpdated"] = _utc_now()


def ensure_guardrail_state(state: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Ensure guardrail outcomes are tracked within shared state."""

    guardrail_state = state.get(GUARDRAIL_STATE_KEY)
    if not isinstance(guardrail_state, MutableMapping):
        guardrail_state = {}
        state[GUARDRAIL_STATE_KEY] = guardrail_state
    return guardrail_state


def write_guardrail_results(
    state: MutableMapping[str, Any],
    *,
    evaluations: Iterable[GuardrailResult],
) -> None:
    """Persist guardrail evaluations to shared state for UI consumption."""

    guardrails = ensure_guardrail_state(state)
    for evaluation in evaluations:
        key, payload = _normalise_guardrail_result(evaluation)
        if key is None or payload is None:
            continue
        guardrails[key] = payload


def _normalise_guardrail_result(
    result: GuardrailResult,
) -> tuple[str | None, Mapping[str, Any] | None]:
    name = result.name
    metadata = dict(result.metadata or {})

    if name == "quiet_hours":
        payload: dict[str, Any] = {
            "allowed": result.allowed,
            "message": result.reason or "",
        }
        if "window" in metadata:
            payload["window"] = metadata["window"]
        if "currentTime" in metadata:
            payload["currentTime"] = metadata["currentTime"]
        if "configured" in metadata:
            payload["configured"] = bool(metadata["configured"])
        return "quietHours", payload

    if name == "trust_threshold":
        payload = {
            "allowed": result.allowed,
            "score": metadata.get("score"),
            "threshold": metadata.get("threshold"),
        }
        if metadata.get("source"):
            payload["source"] = metadata["source"]
        if result.reason:
            payload["message"] = result.reason
        if metadata.get("missingSignal") is not None:
            payload["missingSignal"] = bool(metadata["missingSignal"])
        return "trust", payload

    if name == "scope_validation":
        payload = {
            "allowed": result.allowed,
            "missingScopes": list(metadata.get("missingScopes", [])),
            "requestedScopes": list(metadata.get("requestedScopes", [])),
            "enabledScopes": list(metadata.get("enabledScopes", [])),
        }
        if result.reason:
            payload["message"] = result.reason
        return "scopeValidation", payload

    if name == "evidence_requirement":
        payload = {
            "required": bool(metadata.get("required", True)),
            "allowed": result.allowed,
            "missingEvidence": list(metadata.get("missingEvidence", [])),
        }
        if result.reason:
            payload["message"] = result.reason
        return "evidence", payload

    return None, None


def ensure_approval_modal(state: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Ensure the approval modal state scaffold exists."""

    modal = state.get(APPROVAL_MODAL_KEY)
    if not isinstance(modal, MutableMapping):
        modal = {
            "envelopeId": None,
            "proposal": None,
            "requiredScopes": [],
            "approvalState": "pending",
        }
        state[APPROVAL_MODAL_KEY] = modal
    return modal


def set_approval_modal(
    state: MutableMapping[str, Any],
    *,
    envelope: Envelope,
    required_scopes: Sequence[str],
    proposal: Mapping[str, Any],
) -> None:
    """Populate the approval modal shared state."""

    modal = ensure_approval_modal(state)
    modal.update(
        {
            "envelopeId": envelope.envelope_id,
            "proposal": dict(proposal),
            "requiredScopes": list(required_scopes),
            "approvalState": "pending",
        }
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
