"""FastAPI application wiring for the ADK agent."""

from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI
from ag_ui_adk import add_adk_fastapi_endpoint

from .agents import build_control_plane_agent
from .analytics import router as analytics_router
from .services.settings import get_settings


load_dotenv()

settings = get_settings()

app = FastAPI(title="AI Employee Control Plane")

adk_agent = build_control_plane_agent(settings=settings)
add_adk_fastapi_endpoint(app, adk_agent, path="/")
app.include_router(analytics_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Basic readiness probe for the control plane."""

    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    """Liveness probe: returns ok when the app is serving requests."""

    return {"status": "ok"}


@app.get("/metrics", response_class=None)
def metrics() -> str:
    """Minimal metrics stub (Phase 5: Supabase-only analytics)."""

    # Keep this stub lightweight; full Prometheus wiring is optional and deferred.
    return "# metrics disabled; use /analytics/* and Supabase dashboards"  # type: ignore[return-value]


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
