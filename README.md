# AI Employee Platform

This repository is the reference implementation for the Composio-only AI Employee
experience documented under `docs/`. It wires a Next.js + CopilotKit frontend to a
Google ADK agent, and captures the roadmap for layering in Supabase persistence,
Composio execution, and guardrails.

## Toolchain

We standardise on **mise + uv + pnpm** so every contributor and AI assistant shares the
same environment contracts.

| Component | Version | How we manage it |
|-----------|---------|-------------------|
| Node.js   | 22.x    | `mise` (`.mise.toml`) |
| pnpm      | 10.18.x | `corepack prepare pnpm@10 --activate` (run once per shell) |
| Python    | 3.13.x  | `mise` + `uv` |

Install the toolchain once per machine (mirrors the guidance in
`docs/getting-started/setup.md`):

```bash
curl https://mise.jdx.dev/install.sh | sh
curl -fsSL https://astral.sh/uv/install.sh | sh
corepack enable && corepack prepare pnpm@10 --activate
```

## Quick Start

```bash
# 1. Clone then install pinned runtimes & dependencies
mise install
pnpm install          # triggers `uv sync --extra test`

# 2. Configure environment variables (see docs/getting-started/setup.md)
cp .env.example .env
echo 'GOOGLE_API_KEY=...' >> .env

# 3. Run the local loop (Next.js + ADK agent)
pnpm dev              # or `mise run dev`

# 4. Visit http://localhost:3000 (workspace shell) and curl http://localhost:8000/healthz

# 5. (Optional) Run the Outbox worker against Supabase
uv run python -m worker.outbox start
```

The `scripts/` folder is now uv-aware:

- `scripts/run-agent.*` executes `uv run python -m agent` so it always uses the synced
  virtual environment.
- `scripts/setup-agent.*` simply calls `uv sync --extra test` for parity with the
  package.json `install:agent` script.

## Workspace Surfaces

The `/` workspace is built from shared state emitted by the agent:

- `/` – overview tiles summarising queue, approvals, guardrail blocks.
- `/desk` – live queue with evidence, quick status toggles, and guardrail banners.
- `/approvals` – schema-driven approval forms pulled from `tool_catalog.schema`.

All routes live under `src/app/(workspace)/` and react instantly to `StateDeltaEvent`s.

## Workflow Scripts

All package scripts assume pnpm; `mise run <task>` simply proxies to them.

| Command | Purpose |
|---------|---------|
| `pnpm dev` | Run Next.js (`dev:ui`) and the ADK agent (`dev:agent`) concurrently. |
| `pnpm run dev:ui` | Launch only the frontend. |
| `pnpm run dev:agent` | Launch only the agent via uv. |
| `pnpm build` / `pnpm start` | Build and serve the Next.js bundle. |
| `pnpm lint` | ESLint (Next.js config). |
| `pnpm install:agent` | Idempotent `uv sync --extra test`. |

## Documentation Map

Authoritative system documentation lives in `docs/`:

- `docs/README.md` – navigation hub linking to architecture, implementation, operations,
  and governance guides.
- `AGENTS.md` – comprehensive agent control plane playbook with multi-phase roadmap
  covering control-plane modularization, Composio integration, approvals/frontend state,
  data persistence, and operations/governance. References current implementation status,
  target architecture, and actionable next steps mapped to `docs/todo.md`.
- `docs/todo.md` – layered delivery tracker mirroring every documentation area.
- `docs/getting-started/` – environment setup, core concepts, onboarding.
- `docs/architecture/` – component diagrams and contracts for frontend, agent, Composio,
  and data layers.
- `docs/implementation/` – task-focused how-tos for callbacks, shared state, schemas, and
  UI surfaces.
- `docs/operations/` – deployment, observability, and incident runbooks.
- `docs/prd/` – product requirements snapshots for the control plane.
- `docs/use_cases/` – operator workflows anchored to the current implementation.
- `docs/governance/` – ownership, security, and evergreen processes.
- `docs/references/` – roadmap, glossary, product intent, requirements, observability.

### Analytics & Operations Quick Links

- `GET /analytics/outbox/status?tenant=TENANT_ID` – queue and DLQ counts sourced from Supabase.
- `GET /analytics/guardrails/recent?tenant=TENANT_ID&limit=20` – recent guardrail audit entries.
- `GET /analytics/cron/jobs?limit=20` – Supabase Cron job history for sync jobs.

Each document declares `Status:` so you know which behaviours are live. Keep the docs in
lockstep with the code; reviewers are expected to block drift.

## TODO Tracker

`docs/todo.md` is the single backlog for engineering work across agent, frontend, data,
and operations. Update it as milestones ship and reference it in PR descriptions when you
close items.

## Contributing

- Use pnpm for JS scripts, uv for Python management, and `mise run` for task shortcuts.
- Run the local verification checklist in `docs/getting-started/setup.md` before pushing.
- Document every behaviour change; the governance checklist (`docs/governance/`)
  enforces this policy.

Happy hacking ✨
