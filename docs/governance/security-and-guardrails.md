# Security, Safety & Guardrails

**Status:** In progress

We owe operators a system that is transparent, auditable, and safe by default. Use this
document as the source of truth for guardrails that must exist before enabling
autonomous behaviour.

## Principles

1. **Human-in-the-loop by default** – actions require approval until trust scores exceed
   configured thresholds.
2. **Least privilege** – tools only run with scopes explicitly enabled via Composio.
3. **Audit everything** – every approval, execution, scope change, and override must be
   recorded with actor, timestamp, and payload (PII redacted).

## Guardrail Matrix

| Guardrail | Owner | Implementation Notes | Status |
|-----------|-------|----------------------|--------|
| Quiet hours / DNC | Backend | Callback checks before enqueueing Outbox jobs. | Planned |
| Trust thresholds | Backend | Daily job updates trust score; auto-run only above 0.8. | Planned |
| Schema validation | Frontend + Backend | JSON Schema enforced client + server side. | Planned |
| Audit log | Backend | Supabase `audit_log` table with append-only policy. | Planned |
| Log redaction | Backend | Use `structlog` processors to scrub OAuth tokens, PII. | Planned |

Update the status column as each guardrail ships.

## Incident Response Expectations

- Maintain on-call coverage proportional to customer impact.
- Link runbooks (Composio outage, Outbox DLQ) in the on-call rotation doc.
- Conduct post-incident reviews within two business days.

## Secrets Management

- Never commit secrets to the repository. `.env` is for local dev only.
- Use per-environment secret stores with rotation policies (≤90 days).
- Document any new secret in `docs/governance/ownership-and-evergreen.md` to keep the
  onboarding guide current.

## Privacy Commitments

- Redact PII in logs and UI screenshots.
- Expose data retention controls once Supabase is live (default 90 days).

Keep this document updated whenever a new risk is identified or mitigated.
