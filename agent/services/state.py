"""Helpers for working with shared ADK state."""

from __future__ import annotations

from typing import Any, MutableMapping


STATE_KEY = "proverbs"


def ensure_proverbs_state(state: MutableMapping[str, Any]) -> list[str]:
    """Ensure the proverbs list exists within the shared state mapping."""

    if STATE_KEY not in state or state[STATE_KEY] is None:
        state[STATE_KEY] = []
    return state[STATE_KEY]


def get_proverbs_state(state: MutableMapping[str, Any]) -> list[str]:
    """Fetch the proverbs list, initialising it when missing."""

    return ensure_proverbs_state(state)


def set_proverbs_state(state: MutableMapping[str, Any], new_proverbs: list[str]) -> None:
    """Persist a new list of proverbs in shared state."""

    state[STATE_KEY] = list(new_proverbs)
