# Getting Started & Local Development

**Status:** Implemented (Next.js UI + FastAPI ADK + Supabase schema + Outbox worker) · In progress (optional custom OAuth branding)

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
demo agent today. For Composio MCP, only `COMPOSIO_API_KEY` is required — all non‑auth
tools work out of the box, and tools that require authentication can use Composio’s
hosted connect flow automatically. Supabase is optional for UI‑only demos; it is
required for the Outbox worker and analytics endpoints.

```bash
cp .env.example .env

echo "GOOGLE_API_KEY=..." >> .env
echo "COMPOSIO_API_KEY=..." >> .env
# Optional: restrict catalog discovery and baseline scopes per tenant.
# Leave COMPOSIO_DEFAULT_TOOLKITS empty to fetch ALL available toolkits via MCP.
# Set it only if you want to limit discovery, e.g.: GITHUB,SLACK
# echo "COMPOSIO_DEFAULT_TOOLKITS=GITHUB,SLACK" >> .env
# COMPOSIO_DEFAULT_SCOPES are tenant‑wide baseline scopes appended to proposals (optional)
# echo "COMPOSIO_DEFAULT_SCOPES=SLACK.CHAT:WRITE" >> .env
echo "SUPABASE_URL=..." >> .env
echo "SUPABASE_ANON_KEY=..." >> .env
echo "SUPABASE_SERVICE_KEY=..." >> .env
```

The Python process reads `.env` via `python-dotenv`. Keep UI-only overrides in
`.env.local` if needed. If you want to pre-configure Supabase before persistence
goes live, follow the credential bootstrap steps below.

### 3.1 Composio Auth Flow (no client ID/secret required)

- For tools that require OAuth, Composio provides a hosted connect experience and
  redirect handling. With only `COMPOSIO_API_KEY`, your app can initiate a connection
  and receive a redirect URL to Composio’s consent screen. You do not need
  `COMPOSIO_CLIENT_ID`, `COMPOSIO_CLIENT_SECRET`, or a custom `COMPOSIO_REDIRECT_URL`
  unless you want to brand the redirect domain (advanced/optional).
- A custom redirect can be added later using the “custom domain redirect” pattern
  vendored in `libs_docs/composio_next/fern/pages/src/authentication/custom-auth-configs.mdx`.

### 3.2 Supabase Credential Bootstrap {#supabase-credential-bootstrap}

**Prerequisites:** Access to a Supabase project you can administer and the Supabase CLI
(`supabase >= 1.168`). Install the CLI via Homebrew, npm, or the
[official instructions](https://supabase.com/docs/guides/cli) if it is not already
available.

1. Authenticate the CLI and link the project you will use for development:
   ```bash
   supabase login
   supabase projects list          # copy the project ref for the desired project
   supabase link --project-ref <project-ref>
   ```
2. In the Supabase dashboard, navigate to **Project Settings → API** and copy the
   `Project URL`, `anon public` key, and `service_role` key. These values map directly to
   the environment variables the agent and upcoming workers consume.
3. Store the secrets in `.env` so backend services can read them:
   ```bash
   echo "SUPABASE_URL=https://<project-id>.supabase.co" >> .env
   echo "SUPABASE_ANON_KEY=..." >> .env
   echo "SUPABASE_SERVICE_KEY=..." >> .env
   ```
   - Place UI-only values (for example `NEXT_PUBLIC_SUPABASE_ANON_KEY`) in `.env.local`
     to avoid shipping privileged credentials in the browser bundle.
   - No additional wiring is required—`python-dotenv` loads `.env` automatically when the
     FastAPI app starts.
4. Verify the CLI link before running migrations or local jobs:
   ```bash
   supabase projects list
   ```
   Confirm the project reference you linked in step 1 appears in the output (look for the
   `Project Ref` column). Re-run `supabase link --project-ref <project-ref>` if you need
   to switch projects.

> **Security:** Treat the `service_role` key as highly privileged. Never commit it to
> source control, rotate it from the Supabase dashboard if you suspect exposure, and use
> the anon key for any client-visible operations.

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
2. `curl http://localhost:8000/healthz` and `/readyz` should return `{ "status": "ok" }`.
3. `curl http://localhost:8000/analytics/outbox/status` returns JSON (when Supabase configured).
4. Trigger the sample “set theme” action and confirm the console shows AGUI events
   without errors.

## 6. Optional: Supabase Bootstrap

If you are bringing up Supabase locally, apply the initial universal schema in `db/migrations/001_init.sql`
and the demo seed in `db/seeds/000_demo_tenant.sql` from your Supabase project directory
before running migrations of your own:

```bash
supabase db execute --file db/migrations/001_init.sql
supabase db execute --file db/seeds/000_demo_tenant.sql
# or
psql $SUPABASE_DATABASE_URL -f db/migrations/001_init.sql
psql $SUPABASE_DATABASE_URL -f db/seeds/000_demo_tenant.sql
```

See `db/README.md` for extension requirements (e.g., `pgcrypto`), helper functions, RLS
policies, and seed details.

If anything fails, start with the troubleshooting checklist in
`docs/operations/run-and-observe.md`.

## 7. Optional Quality-of-Life Scripts

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
