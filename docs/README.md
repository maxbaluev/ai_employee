# AI Employee Platform Documentation

Welcome! This documentation is the implementation playbook for the AI Employee Platform.
It equips engineers, operators, and reviewers with the context they need to ship safely
and quickly, while making it explicit which behaviours exist today and which are still
on the roadmap.

**Quick Start:** Start with the universal PRD & Architecture to understand the
Composio‑only, one‑executor design and the five operator surfaces:
`docs/prd/universal-ai-employee-prd.md`. For implementation phases and repo-specific
notes, see `AGENTS.md` (Agent Control Plane Playbook).

Use the navigation below to jump directly to what you need:

- **Getting Started** – environment setup, dev loop, and core concepts. ↳
  `docs/getting-started/setup.md`, `docs/getting-started/core-concepts.md`
- **Architecture** – verified diagrams and component deep dives for the Next.js UI,
  FastAPI + ADK agents, the Composio‑only execution layer, and the universal action
  envelope. ↳ `docs/architecture/overview.md`,
  `docs/architecture/universal-action-envelope.md`, and related sub‑pages
- **Implementation Guides** – task-oriented recipes for extending the UI, wiring
  Composio tools, and evolving agent callbacks. ↳ files under
  `docs/implementation/`
- **Operations** – how to run, observe, and recover the system in lower and
  production environments. ↳ files under `docs/operations/`
- **Governance** – safety, security, and documentation stewardship expectations. ↳
  files under `docs/governance/`
- **Decisions** – architectural decision records constraining the system. ↳
  `docs/decisions/`
- **References** – product intent, requirement summaries, and terminology. ↳
  `docs/references/`
- **TODO Tracker** – layered backlog covering every documentation area. ↳
  `docs/todo.md`

Every document declares its status so you know how much of the behaviour is present in
this repository:

- `Implemented` – behaviour is live in the current codebase.
- `In progress` – partially implemented; remaining work is captured explicitly.
- `Planned` – roadmap guidance; follow it before landing code.

When you change the platform, change the documentation. The review process and doc
ownership checklist live in `docs/governance/ownership-and-evergreen.md`.
