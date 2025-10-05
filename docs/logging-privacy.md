# Logging & Privacy Guidelines

## Data Classification

- **PII (Restricted)**: email addresses, phone numbers, names from external tools, call transcripts.
- **Sensitive Business Data (Confidential)**: objectives, plan content, action arguments, trust scores.
- **Operational Metadata (Internal)**: run IDs, tool slugs, rate bucket names.

## Logging Rules

1. Hash or tokenize PII before logging (`sha256` + salt). Never log raw email/phone.
2. Redact message bodies or limit to summaries; store full payloads only in secure storage with retention policy.
3. Annotate logs with `classification` field to support downstream scrubbing.
4. Separate audit logs (immutability, append-only) from application logs; apply WORM storage where required.
5. Retain application logs for 30 days, audit logs for 1 year unless stricter tenant policies apply.

## Privacy Safeguards

- Respect `do_not_contact` lists: Outbox should mask identifiers when evaluating guardrails.
- Ensure CopilotKit UI does not render raw secrets; configurations handled server-side.
- Provide data export/delete endpoints for tenants (future requirement; track in backlog).
- Review third-party telemetry providers for compliance (SOC2/GDPR) before integration.

## Monitoring & Compliance

- Run periodic log scrubs to confirm hashing policy.
- Alert if unclassified log entries exceed threshold (indicates missing metadata).
- Document incident handling in future `runbooks/` when privacy breach detected.

## Open Tasks

- Implement per-tenant encryption keys (KMS) for stored audit logs.
- Add automated linting rule to block `print`/`console.log` in production paths.
- Define data subject request workflow before GA.
