"""FastAPI application wiring for the ADK agent."""

from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI
from ag_ui_adk import add_adk_fastapi_endpoint

from .agents import build_control_plane_agent
from .services.settings import get_settings


load_dotenv()

settings = get_settings()

app = FastAPI(title="AI Employee Control Plane")

adk_agent = build_control_plane_agent(settings=settings)
add_adk_fastapi_endpoint(app, adk_agent, path="/")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Basic readiness probe for the control plane."""

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
