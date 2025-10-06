# Documentation Ownership & Evergreen Process

**Status:** Implemented

Documentation is part of the product. Treat updates as non-optional whenever behaviour
changes.

## Roles & Responsibilities

| Document area | Primary owner | Backup |
|---------------|---------------|--------|
| Getting Started | Developer Experience | Platform Eng |
| Architecture | Platform Eng | Product Eng |
| Implementation Guides | Feature team shipping the change | Platform Eng |
| Operations & Runbooks | SRE | Platform Eng |
| Governance | Security | Platform Eng |

The “owner” is responsible for reviewing doc changes, ensuring accuracy, and kicking off
refreshes when reality drifts.

## Definition of Done for Code Changes

Every PR that changes behaviour must:

1. Update or create the relevant doc page(s).
2. Add a changelog entry in the PR description linking to the doc update.
3. Include screenshots or logs if the behaviour is operator-facing.

PR reviewers should block merges that violate the above.

### Guardrail PR Checklist

Before merging changes to guardrail behaviour (quiet hours, trust, scopes, evidence):

- [ ] Tests updated and passing (`tests/guardrails/*`, `tests/agent/test_guardrails.py`).
- [ ] Documentation aligned (`docs/governance/security-and-guardrails.md`,
      `docs/implementation/backend-callbacks.md`).
- [ ] Audit/logging reviewed (`agent/services/audit.py`) and updated if behaviour changes.
- [ ] Observability signals covered (`docs/references/observability.md`, metrics emitted).
- [ ] Runbooks or tickets filed when operator behaviour shifts
      (`docs/operations/runbooks/*`).
- [ ] Transient artifacts (feature flags, debug hooks, temporary data) removed before ship.

Cross-link guardrail schema updates with `docs/implementation/frontend-shared-state.md`
and the JSON schemas in `docs/schemas/` when shared state changes.

> TODO: When PR templates or CONTRIBUTING guides land, add cross-links back to this
> Guardrail PR Checklist and `docs/todo.md` so contributors keep the doc hygiene loop
> closed.
> TODO: Once the PR template and CONTRIBUTING guide exist, ensure they explicitly link
> to this checklist and `docs/todo.md` as part of the submission checklist.

## Quarterly Doc Review

1. Assemble owners for a 60-minute audit.
2. Run `git diff` between the latest release tag and `main` to surface code changes.
3. Spot-check that the doc status labels (`Implemented`, `In progress`, `Planned`) are up
   to date.
4. File tickets for any drift and assign to the relevant team.

### Quarterly Doc-Audit Log

Maintain a lightweight log so ownership stays visible:

- **Owners:** doc-area owners listed above (primary + backup).
- **Scope:** governance docs, guardrail guides, shared-state schemas, runbooks, and
  observability references.
- **Checklist:** status labels accurate, guardrail docs in sync with tests, runbooks
  reflect current behaviour, pending TODOs triaged.
- **Template:**

  ```markdown
  | Date | Reviewer(s) | Findings | Actions / Tickets |
  |------|-------------|----------|-------------------|
  | 2025-09-30 | Alice / Bob | Scope doc drifted | DOC-1234 to update |
  ```

Store the log in the doc repo (`docs/governance/audit-log.md`) or the team space for easy
access.

## Adding New Docs

1. Decide where the doc fits in the structure (getting-started, architecture, etc.).
2. Include a status label at the top of the file.
3. Link the doc from `docs/README.md` to keep navigation complete.

## Retiring Docs

- Move outdated material to `docs/archive/` (create it when needed) with a note pointing
  to the replacement.
- Update inbound links to avoid dead references.

Following this process keeps the documentation trustworthy and useful for every new hire.
