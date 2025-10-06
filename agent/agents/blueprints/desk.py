"""Desk blueprint containing shared-state scaffolding and prompt helpers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping

from agent.schemas.envelope import stash_last_envelope
from agent.services import (
    append_queue_item,
    ensure_desk_state,
    ensure_guardrail_state,
    seed_queue,
    set_approval_modal,
)
from agent.services.objectives import Objective
from agent.services.outbox import OutboxRecord
from agent.services.catalog import ToolCatalogEntry


@dataclass(slots=True)
class DeskBlueprint:
    """Blueprint for the desk surface used in the control plane."""

    name: str = "DeskBlueprint"

    def seed_state(
        self,
        state: MutableMapping[str, Any],
        *,
        objectives: Sequence[Objective],
    ) -> None:
        """Ensure the desk queue is initialised from tenant objectives."""

        desk_state = ensure_desk_state(state)
        queue = desk_state.get("queue")
        if isinstance(queue, list) and queue:
            return

        queue_items = [
            {
                "id": objective.objective_id,
                "title": objective.title,
                "status": "pending",
                "evidence": [objective.summary],
            }
            for objective in objectives
        ]
        seed_queue(state, queue=queue_items)

    def ensure_shared_state(
        self,
        state: MutableMapping[str, Any],
        *,
        objectives: Sequence[Objective],
        pending: Sequence[OutboxRecord] = (),
    ) -> None:
        """Idempotently seed state when invoked by the callback pipeline."""

        self.seed_state(state, objectives=objectives)
        ensure_guardrail_state(state)
        self.hydrate_pending(state, pending=pending)

    def hydrate_pending(
        self,
        state: MutableMapping[str, Any],
        *,
        pending: Sequence[OutboxRecord],
    ) -> None:
        """Merge pending outbox records into the desk queue."""

        if not pending:
            return

        desk_state = ensure_desk_state(state)
        queue = desk_state.setdefault("queue", [])
        seen_ids = {
            item.get("id")
            for item in queue
            if isinstance(item, Mapping)
        }
        for record in pending:
            if record.envelope.envelope_id in seen_ids:
                continue
            append_queue_item(state, record.to_shared_state())

    def guardrail_block_message(self, result) -> str:
        reason = result.reason or f"Request blocked by {result.name} guardrail."
        return (
            "Guardrail prevented this action. "
            f"{reason} Please adjust the request or submit for approval later."
        )

    def prompt_prefix(
        self,
        *,
        objectives: Sequence[Objective],
        catalog_entries: Sequence[ToolCatalogEntry],
    ) -> str:
        objective_lines = [
            f"- {obj.title} (metric: {obj.metric}, target: {obj.target}, horizon: {obj.horizon})"
            for obj in objectives
        ] or ["- No objectives configured"]

        tool_lines = [entry.prompt_snippet() for entry in catalog_entries] or [
            "Tool catalog is empty; request catalog sync before executing envelopes."
        ]

        instructions = (
            "You orchestrate tenant actions via Composio."
            " Before executing, construct an envelope using the `enqueue_envelope` tool." 
            " Always provide arguments that satisfy the catalog JSON Schema and include supporting evidence."
        )

        return (
            "Tenant objectives:\n"
            + "\n".join(objective_lines)
            + "\n\nAvailable Composio tools:\n"
            + "\n".join(tool_lines)
            + "\n\n"
            + instructions
        )

    def register_envelope(
        self,
        state: MutableMapping[str, Any],
        *,
        record: OutboxRecord,
        required_scopes,
        proposal: Mapping[str, Any] | None,
    ) -> None:
        """Persist envelope metadata in shared state after queuing."""

        append_queue_item(state, record.to_shared_state())

        if proposal is None:
            proposal = {
                "summary": "Autonomous envelope queued",
                "evidence": ["No additional evidence provided"],
            }
        set_approval_modal(
            state,
            envelope=record.envelope,
            required_scopes=list(required_scopes or []),
            proposal=proposal,
        )
        stash_last_envelope(state, record.envelope)

    def post_model(self, state: MutableMapping[str, Any], *, response) -> None:  # noqa: D401 - behaviour documented inline
        """Hook for after-model modifier (reserved for future summarisation)."""

        _ = state, response  # no-op for now; kept for future shared-state updates
