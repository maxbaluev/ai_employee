"""Definition for the demo Proverbs ADK agent."""

from __future__ import annotations

from typing import Any, Dict, Optional

from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext
from ..callbacks import (
    before_model_modifier,
    on_before_agent,
    simple_after_model_modifier,
)
from ..services.settings import AppSettings, get_settings
from ..services.state import set_proverbs_state


def set_proverbs(tool_context: ToolContext, new_proverbs: list[str]) -> Dict[str, str]:
    """Persist the provided proverbs in shared state."""

    try:
        set_proverbs_state(tool_context.state, new_proverbs)
        return {"status": "success", "message": "Proverbs updated successfully"}
    except Exception as exc:  # pragma: no cover - defensive path
        return {"status": "error", "message": f"Error updating proverbs: {exc}"}


def get_weather(tool_context: ToolContext, location: str) -> Dict[str, str]:
    """Mock implementation used to demonstrate tool wiring."""

    _ = tool_context
    return {"status": "success", "message": f"The weather in {location} is sunny."}


def build_proverbs_adk_agent(settings: Optional[AppSettings] = None) -> Any:
    """Create an ADKAgent using the shared callback modules."""

    app_settings = settings or get_settings()

    from ag_ui_adk import ADKAgent

    proverbs_agent = LlmAgent(
        name="ProverbsAgent",
        model=app_settings.default_model,
        instruction="""
        When a user asks you to do anything regarding proverbs, you MUST use the set_proverbs tool.

        IMPORTANT RULES ABOUT PROVERBS AND THE SET_PROVERBS TOOL:
        1. Always use the set_proverbs tool for any proverbs-related requests.
        2. Always pass the COMPLETE LIST of proverbs to the set_proverbs tool.
        3. You can use existing proverbs if one is relevant to the user's request, but you can also create new proverbs as required.
        4. Be creative and helpful in generating complete, practical proverbs.
        5. After using the tool, provide a brief summary of what you created, removed, or changed.

        IMPORTANT RULES ABOUT WEATHER AND THE GET_WEATHER TOOL:
        1. Only call the get_weather tool if the user asks you for the weather in a given location.
        2. If the user does not specify a location, you can use the location "Everywhere ever in the whole wide world".
        """,
        tools=[set_proverbs, get_weather],
        before_agent_callback=on_before_agent,
        before_model_callback=before_model_modifier,
        after_model_callback=simple_after_model_modifier,
    )

    return ADKAgent(
        adk_agent=proverbs_agent,
        app_name=app_settings.app_name,
        user_id=app_settings.user_id,
        session_timeout_seconds=3600,
        use_in_memory_services=True,
    )
