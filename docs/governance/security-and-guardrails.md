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
| Quiet hours / DNC | Backend | `agent/guardrails/quiet_hours.check` blocks during configured quiet window; see `tests/guardrails/test_quiet_hours.py`. | Implemented |
| Trust thresholds | Backend | `agent/guardrails/trust.check` treats missing scores as `0.0` and blocks until the trust score meets the threshold; see `tests/guardrails/test_trust.py`. | Implemented |
| Scope enforcement | Backend | `agent/guardrails/scopes.check` normalises scope strings and reports missing entries; see `tests/guardrails/test_scopes.py`. | Implemented |
| Evidence requirement | Backend | `agent/guardrails/evidence.check` verifies proposals contain supporting evidence; see `tests/guardrails/test_evidence.py`. | Implemented |
| Schema validation | Frontend + Backend | JSON Schema enforced client + server side. | Planned |
| Audit log | Backend | Supabase `audit_log` table with append-only policy. | Planned |
| Log redaction | Backend | Use `structlog` processors to scrub OAuth tokens, PII. | Planned |

Update the status column as each guardrail ships.

### Behaviour Summary

- **Quiet hours**: Blocks tool execution during the tenant-configured window; outside the
  window the guardrail returns an allow result with context in the reason string.
- **Trust thresholds**: Treats a missing trust score as `0.0`; actions auto-run only when
  the score meets or exceeds the configured threshold, otherwise a human must approve.
- **Scope enforcement**: Normalises requested/enabled scopes (strip + lowercase) and
  blocks when any requested scope is absent, listing the missing values to guide the
  operator.
- **Evidence requirement**: `ensure_evidence_present` bypasses validation when no
  proposal is present; once a proposal exists, the guardrail blocks when evidence is
  missing or empty.

Fast path wiring for all four guardrails lives in
`agent/callbacks/guardrails.py` and is consumed by `agent/callbacks/before.py` within
`run_guardrails`. Refer to `docs/implementation/backend-callbacks.md` for signature
details and integration examples.

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
