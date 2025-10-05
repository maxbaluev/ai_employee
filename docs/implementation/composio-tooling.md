# Composio Tooling Integration Guide

**Status:** Planned (starter code only)

Follow this guide when replacing the demo tools in `agent/agent.py` with real Composio
toolkits. It draws on the vendor examples vendored in `libs_docs/`.

## 1. Bootstrap the Client

```python
# agents/services/composio_client.py
from composio import Composio
from composio_google_adk import GoogleAdkProvider

composio_client = Composio(provider=GoogleAdkProvider())
```

- Read `COMPOSIO_API_KEY` from settings (see `pydantic-settings`).
- Pass the active `user_id` and toolkits when calling `tools.get`.

## 2. Discover Tools

```python
tools = composio_client.tools.get(
    user_id=user_id,
    toolkits=["GITHUB", "SLACK"],
)
```

- Persist the returned schema + scopes using the catalog service described in
  `docs/architecture/composio-execution.md`.
- Use the schema to render approval forms in the UI.

## 3. Wrap Tools for ADK

ADK accepts `FunctionTool` instances. You can convert Composio tool definitions using the
`GoogleAdkProvider` helper (see the demo in
`libs_docs/composio_next/python/providers/google_adk/google_adk_demo.py`).

```python
from composio_google_adk import GoogleAdkProvider

provider = GoogleAdkProvider()
adk_tools = provider.convert_to_adk_tools(tools)

proverbs_agent = LlmAgent(
    name="employee",
    model="gemini-2.5-flash",
    tools=adk_tools,
    ...
)
```

## 4. Execute Tools Safely

When the Outbox worker pops an envelope, call `composio_client.tools.execute(...)` with:

```python
composio_client.tools.execute(
    user_id=user_id,
    connected_account_id=envelope["connected_account_id"],
    tool_slug=envelope["tool_slug"],
    arguments=envelope["args"],
    external_id=envelope["external_id"],
)
```

Handle the following cases explicitly:

- **Provider conflict (HTTP 409)** – record as `conflict` but do not retry.
- **Soft failures** – retry with Tenacity according to risk tier.
- **Hard failures** – move to DLQ and surface in Activity timeline.

## 5. Testing Strategy

- Mock Composio using the SDK’s in-memory fixtures to unit-test guards and envelope
  construction.
- Add integration tests (recorded cassettes or sandbox environment) before GA.

Keep this document updated as the integration solidifies, especially around schema
versions and safety policies.
