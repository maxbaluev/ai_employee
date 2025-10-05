"""Backward-compatible entrypoint for running the ADK agent."""

from __future__ import annotations

from pathlib import Path
import sys


if __package__:
    from .app import app, main  # pragma: no cover
else:  # pragma: no cover - script execution path
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from agent.app import app, main  # type: ignore


__all__ = ["app", "main"]


if __name__ == "__main__":
    main()
