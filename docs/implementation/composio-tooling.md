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

- Read `COMPOSIO_API_KEY`, `COMPOSIO_CLIENT_ID`, `COMPOSIO_CLIENT_SECRET`, and
  `COMPOSIO_REDIRECT_URL` from `AppSettings` (see `pydantic-settings`). The API key
  authenticates against Composio, while the OAuth fields drive the hosted connection
  handshake.
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

## 3. Account Connection & OAuth

Leverage Composio’s hosted connection flow to link tenant accounts.

1. Generate a connection URL (use the redirect URI you registered in the Composio
   dashboard; hard-code it or plumb it through settings once the configuration is
   extended):

   ```python
   link = composio_client.accounts.create_connection_link(
       user_id=user_id,
       redirect_uri="https://your-ui.example.com/api/composio/callback",
       scopes=["GMAIL.SMTP", "CALENDAR.READ"]
   )
   ```

2. Expose `link.url` via shared state so the UI can open it. Capture the state token for
   CSRF validation.
3. Handle the callback (e.g. `/api/composio/callback`): exchange `code` for a
   `connected_account_id` using `composio_client.accounts.exchange_code(...)`.
4. Persist the account record (provider, granted scopes, metadata) using the catalog
   service and emit an audit event.
5. Update shared state with the new `connected_account_id` so approval flows know the
   account is active.

Both the service API key and OAuth secrets are available via `AppSettings`. Ensure
`COMPOSIO_API_KEY`, `COMPOSIO_CLIENT_ID`, `COMPOSIO_CLIENT_SECRET`, and
`COMPOSIO_REDIRECT_URL` are set in your environment before attempting the connection
flow.

## 4. Scope Handling & Guardrails

- Store granted scopes per `connected_account_id` in Supabase.
- When rendering approval prompts, compare requested scopes with stored grants; use the
  catalog JSON Schema to generate UI forms (see
  `docs/implementation/frontend-shared-state.md`).
- Populate `state.requested_scopes` and `state.enabled_scopes` so
  `agent/guardrails/scopes.py` can enforce policy before tool execution.
- If additional scopes are required, enqueue an approval envelope referencing the
  schema; log the request via `services.audit`.

## 5. Wrap Tools for ADK

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

## 6. Execute Tools Safely

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

## 7. Testing Strategy

- Mock Composio using the SDK’s in-memory fixtures to unit-test guards and envelope
  construction.
- Add integration tests (recorded cassettes or sandbox environment) before GA.

Keep this document updated as the integration solidifies, especially around schema
versions and safety policies.
