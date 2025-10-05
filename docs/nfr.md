# Non-Functional Requirements — AI Employee Platform

## Reliability & Availability

- **R-001 Service uptime**: UI and control plane target 99.9% availability measured monthly.
- **R-002 Outbox reliability**: Outbox worker maintains 99.5% successful deliveries; DLQ drained within 30 minutes.
- **R-003 Retry strategy**: Exponential backoff with jitter; configurable per rate bucket.

## Performance & Scalability

- **P-001 Latency**: Desk page initial load < 2.5s at 95th percentile with warm cache.
- **P-002 Outbox completion**: Action completion p95 ≤ 5 minutes (enqueue to provider acknowledgement).
- **P-003 Planner throughput**: Warm Scan completes within 120 seconds for first 1k records per tool; Trickle Refresh budget <= 60 seconds per cycle.

## Security & Compliance

- **S-001 Least privilege**: Only Composio-provided scopes stored; JIT upgrades logged and reversible.
- **S-002 Data residency**: All persisted data stays within configured region (default: us-east). Future expansions require ADR.
- **S-003 Secret handling**: No secrets stored in repo; `.env.example` lists placeholders; runtime secrets injected via env/secret manager.

## Maintainability

- **M-001 Configuration as code**: Tool catalog, rate buckets, and program templates versioned as YAML/JSON artifacts.
- **M-002 Module encapsulation**: Frontend, backend, worker modules maintain clear interfaces documented in `docs/MODULES.md`.
- **M-003 ADR cadence**: Decisions recorded within 48h of change to architecture or vendor dependencies.

## Observability

- **O-001 Metrics**: Emit standardized metrics described in `docs/observability.md` to chosen backend (e.g., OpenTelemetry/Prometheus).
- **O-002 Traces**: Business transactions (plan run, approval, execution) must have correlation IDs across services.
- **O-003 Logging**: Structured JSON logs with tenant/employee identifiers (hashed) and request IDs.

## Accessibility & UX Quality

- **A-001 WCAG**: Surfaces meet WCAG 2.1 AA, including keyboard navigation and contrast.
- **A-002 Responsiveness**: Desk and Approvals responsive down to 1280px width without loss of functionality.
- **A-003 Localization-ready**: Copy stored in translation-friendly format; no hard-coded concatenation in UI components.

## Known Gaps

- Distributed tracing pipeline not yet configured; requires selection of observability stack.
- Localization tooling not set up; UI copy currently inline (tracked in `docs/roadmap.md`).
