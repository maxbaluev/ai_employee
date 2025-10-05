# Getting Started & Local Development

**Status:** Implemented (Next.js UI + FastAPI ADK scaffold) · Planned (Composio tools,
Supabase persistence)

This guide walks you from a clean checkout to a working local environment where the
Next.js CopilotKit UI streams events from the Python ADK agent. Follow it in order; the
verification section confirms everything is wired correctly.

## 1. Toolchain Checklist

| Component | Required version | Check command |
|-----------|-----------------|---------------|
| Node.js   | ≥ 18.18         | `node -v`     |
| pnpm      | ≥ 9             | `pnpm --version` |
| Python    | 3.11.x          | `python3 --version` |
| uvicorn   | (installed via `npm run install:agent`) | `agent/.venv/bin/uvicorn --version` |

If any command is missing, install it before continuing. We recommend pyenv / volta or
asdf to keep versions consistent across the team.

## 2. Install Dependencies

From the repository root:

```bash
pnpm install
npm run install:agent   # wraps scripts/setup-agent.sh
```

`npm run install:agent` provisions `agent/.venv` and installs the Python dependencies
defined in `agent/requirements.txt`. Re-run it whenever that file changes.

## 3. Configure Environment Variables

Copy the example env file and populate the required secrets. Only `GOOGLE_API_KEY` is
mandatory for the demo agent today, but fill in the Composio and Supabase values as soon
as the corresponding features ship.

```bash
cp .env.example .env

# Required for the ADK agent to call Gemini
export GOOGLE_API_KEY="..."

# Placeholder values until Composio + Supabase integration is implemented
export COMPOSIO_API_KEY="todo"
export SUPABASE_URL="todo"
export SUPABASE_SERVICE_KEY="todo"
```

Tip: use a `.env.local` file for UI-only overrides. The Python agent reads from `.env`
via `python-dotenv` (see `agent/agent.py`).

## 4. Run the Dev Loop

```bash
npm run dev
```

The script runs two commands concurrently (see `package.json`):

- `next dev --turbopack` serves the UI on <http://localhost:3000>
- `scripts/run-agent.sh` activates the virtualenv and starts the FastAPI server on
  <http://localhost:8000>

Stop both with `Ctrl+C`. To run them independently use `npm run dev:ui` or
`npm run dev:agent`.

## 5. Verify the Environment

1. Visit <http://localhost:3000>. You should see the Copilot sidebar and the
   theme-colour playground from `src/app/page.tsx`.
2. Run `curl http://localhost:8000/` – the FastAPI app should return AGUI metadata.
3. Trigger an action in the UI (e.g. “Set the theme to orange”) and confirm the colour
   updates without errors in the browser console or terminal logs.

If any step fails, consult the troubleshooting section in
`docs/operations/run-and-observe.md` before escalating.

## 6. Optional Quality-of-Life Scripts

- `npm run dev:debug` – runs the same loop with `LOG_LEVEL=debug` for verbose agent logs.
- `scripts/run-agent.sh` – run the agent standalone (useful when integrating Composio
  tools).
- `scripts/setup-agent.sh` – recreate the Python virtualenv from scratch.

When you modify the codebase, re-run the verification checklist. A working local loop is
the baseline for all other guides in this documentation.
