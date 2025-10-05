"""Agent package exposing lazy accessors for the FastAPI app."""

from __future__ import annotations

from typing import Any

__all__ = ["app", "main"]


def __getattr__(name: str) -> Any:
    if name == "app":
        from .app import app as _app

        return _app
    if name == "main":
        from .app import main as _main

        return _main
    raise AttributeError(f"module 'agent' has no attribute {name!r}")
