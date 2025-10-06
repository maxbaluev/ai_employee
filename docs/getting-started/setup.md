# Getting Started & Local Development

**Status:** Implemented (Next.js UI + FastAPI ADK scaffold) · Planned (Composio tools,
Supabase persistence)

Follow this guide to stand up a local environment that mirrors the documented
infrastructure (mise + uv + pnpm).

## 1. Toolchain Checklist

| Component | Required version | Check command | Notes |
|-----------|-----------------|---------------|-------|
| Node.js   | 22.x            | `node -v`     | Installed and pinned by `mise` (`.mise.toml`). |
| pnpm      | 10.18.x         | `pnpm --version` | Enable via `corepack prepare pnpm@10 --activate`. |
| Python    | 3.13.x          | `python3 --version` or `mise list | grep python` | Managed by `mise` and synced with `uv`. |
| uv        | ≥ 0.8           | `uv --version` | Handles virtualenv + dependency resolution. |

Install any missing component before continuing.

### Bootstrap mise + uv

1. Install mise: `curl https://mise.run | sh` (or follow the
   [official guide](https://mise.jdx.dev/getting-started.html)).
2. Reload your shell (`exec $SHELL` or open a new terminal).
3. Verify setup: `mise doctor`. Resolve any warnings (missing shims, PATH issues)
   before moving on.
4. From the repo root run `mise install` to install the versions pinned in `.mise.toml`.
5. Confirm `uv` is installed (`pipx install uv` or package manager of choice) and
   accessible on PATH.

## 2. Install Dependencies

From the repository root:

```bash
mise install              # ensures Node 22 & Python 3.13 are available
pnpm install              # installs JS deps and runs `uv sync --extra test`
```

`pnpm install` triggers the `postinstall` script which executes `uv sync --extra test`.
That command creates or updates `.venv/` according to `pyproject.toml` and `uv.lock`.
You can re-run it manually with `pnpm run install:agent` or `uv sync --extra test`.
If the environment becomes corrupted, run `uv venv --upgrade` followed by
`uv sync --extra test` to rebuild it.

## 3. Configure Environment Variables

Copy the example env file and populate the required secrets. `GOOGLE_API_KEY` powers the
demo agent today; the Composio variables enable OAuth flows once real toolkits go live.
Supabase remains optional until persistence lands.

```bash
cp .env.example .env

echo "GOOGLE_API_KEY=..." >> .env
echo "COMPOSIO_API_KEY=..." >> .env
echo "COMPOSIO_CLIENT_ID=..." >> .env
echo "COMPOSIO_CLIENT_SECRET=..." >> .env
echo "COMPOSIO_REDIRECT_URL=http://localhost:8000/api/composio/callback" >> .env
echo "SUPABASE_URL=..." >> .env
echo "SUPABASE_SERVICE_KEY=..." >> .env
```

The Python process reads `.env` via `python-dotenv`. Keep UI-only overrides in
`.env.local` if needed.

## 4. Run the Dev Loop

```bash
pnpm dev          # or `mise run dev`
```

This launches two processes (via `concurrently`):

- `next dev --turbopack` – UI at <http://localhost:3000>.
- `scripts/run-agent.sh` – `uv run python -m agent` exposing FastAPI at
  <http://localhost:8000>.

Run just the frontend with `pnpm run dev:ui`, or only the agent with
`pnpm run dev:agent` / `mise run agent`.

## 5. Verify the Environment

1. Visit <http://localhost:3000>; the Copilot sidebar and theme playground should load.
2. `curl http://localhost:8000/healthz` should return `{ "status": "ok" }`.
3. Trigger the sample “set theme” action and confirm the console shows AGUI events
   without errors.

## 6. Optional: Supabase Bootstrap

If you are bringing up Supabase locally, apply the draft schema in `db/migrations/001_init.sql`
from your Supabase project directory before running migrations of your own:

```bash
supabase db execute --file db/migrations/001_init.sql
# or
psql $SUPABASE_DATABASE_URL -f db/migrations/001_init.sql
```

See `db/README.md` for extension requirements (e.g., `pgcrypto`) and seed placeholders.

If anything fails, start with the troubleshooting checklist in
`docs/operations/run-and-observe.md`.

## 6. Optional Quality-of-Life Scripts

- `pnpm run dev:debug` – adds `LOG_LEVEL=debug` for verbose agent logs.
- `scripts/run-agent.sh` / `.bat` – direct agent execution via uv.
- `scripts/setup-agent.sh` / `.bat` – idempotent `uv sync --extra test` rebuild.

Retest using the verification checklist whenever you modify dependencies or infra.

## Appendix A – First-run Troubleshooting

| Symptom | Likely cause | Resolution |
|---------|--------------|------------|
| `mise: command not found` | Shell session predates installation | Re-open your terminal or source the shell init snippet printed by the installer. |
| `uv sync` reports Python 3.13 missing | System Python is older than 3.13 | Run `mise install python@3.13` then retry `mise install && uv sync --extra test`. |
| `pnpm dev` fails with "Cannot find module ag_ui_adk" | `uv sync` did not run / `.venv` not activated | Execute `pnpm run install:agent` (runs `uv sync --extra test`) or `uv run python -m agent` once to warm the environment. |
| UI can’t reach agent (`502` or CORS error) | `NEXT_PUBLIC_COPILOTKIT_URL` misconfigured | Ensure `.env` sets `NEXT_PUBLIC_COPILOTKIT_URL=http://localhost:8000` or proxies correctly. |
| `/metrics` 404 during smoke-check | Prometheus middleware not wired yet | Complete the instrumentation steps in `docs/operations/run-and-observe.md` before validating metrics. |
