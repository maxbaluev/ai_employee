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

## Quarterly Doc Review

1. Assemble owners for a 60-minute audit.
2. Run `git diff` between the latest release tag and `main` to surface code changes.
3. Spot-check that the doc status labels (`Implemented`, `In progress`, `Planned`) are up
   to date.
4. File tickets for any drift and assign to the relevant team.

## Adding New Docs

1. Decide where the doc fits in the structure (getting-started, architecture, etc.).
2. Include a status label at the top of the file.
3. Link the doc from `docs/README.md` to keep navigation complete.

## Retiring Docs

- Move outdated material to `docs/archive/` (create it when needed) with a note pointing
  to the replacement.
- Update inbound links to avoid dead references.

Following this process keeps the documentation trustworthy and useful for every new hire.
