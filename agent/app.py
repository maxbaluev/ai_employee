"""FastAPI application wiring for the ADK agent."""

from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI

try:  # pragma: no cover - optional dependency during unit tests
    from ag_ui_adk import add_adk_fastapi_endpoint
except ImportError:  # pragma: no cover
    add_adk_fastapi_endpoint = None  # type: ignore

from .agents.proverbs import build_proverbs_adk_agent
from .services.settings import get_settings


load_dotenv()

settings = get_settings()

app = FastAPI(title="ADK Middleware Proverbs Agent")

_adk_agent = None
if add_adk_fastapi_endpoint is not None:
    try:
        _adk_agent = build_proverbs_adk_agent(settings=settings)
    except RuntimeError:  # pragma: no cover - surfaced in environments without vendor SDK
        _adk_agent = None

if add_adk_fastapi_endpoint is not None and _adk_agent is not None:
    add_adk_fastapi_endpoint(app, _adk_agent, path="/")
else:  # pragma: no cover - fallback for environments without AG UI bridge
    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}


def main() -> None:
    """Serve the ASGI app with Uvicorn."""

    import uvicorn

    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level="info",
    )


if __name__ == "__main__":  # pragma: no cover - convenience entrypoint
    main()
