# Non-Functional Requirements (Final)

## Reliability & Availability

- **R-001 Service Uptime:** UI + control plane target 99.9% monthly availability. Outbox worker 99.5% (tracked via `outbox_delivery_seconds`).
- **R-002 Graceful Degradation:** Composio outage → system enters read-only mode, queues writes, surfaces banner, emits alert (`docs/observability.md`).
- **R-003 Retry Policy:** Tenacity exponential backoff (initial 5s, max 5m, jitter) per rate bucket. DLQ drained within 30 minutes.

## Performance & Scalability

- **P-001 Desk Load:** Initial render < 2.5s p95 (SSR + minimal data). Use lazy loading for large evidence lists.
- **P-002 Planner Throughput:** Warm Scan completes within 120s for first 1k objects per toolkit; Trickle Refresh < 60s per cycle.
- **P-003 Outbox Latency:** Enqueue-to-provider-ack p95 ≤ 5 minutes; highlight if >10 minutes.
- **P-004 Horizontal Scaling:** Control plane stateless; Outbox can run multiple workers (use DB row-level locking + `FOR UPDATE SKIP LOCKED`).

## Security & Compliance

- **S-001 Least Privilege:** Only Composio scopes persisted; JIT upgrades logged with reason and revert path.
- **S-002 Data Residency:** Default US region; follow tenant config with ADR if change needed.
- **S-003 Secret Handling:** Secrets injected via env/secret manager; `.env.example` documents placeholders. `python-dotenv` limited to local dev.
- **S-004 Logging Hygiene:** Hash or redact PII (see `docs/logging-privacy.md`).

## Maintainability & Extensibility

- **M-001 Configuration-as-Code:** Tool catalog, reader kernels, value programs stored as YAML/JSON in repo with migrations.
- **M-002 ADR Discipline:** Significant architectural changes recorded within 48h (`docs/DECISIONS`).
- **M-003 Module Boundaries:** UI, control plane, Outbox, worker, and docs maintain clean interfaces; see `docs/MODULES.md`.
- **M-004 Generated Schema Reuse:** Never duplicate Composio schemas manually; rely on `tool.json_schema`.

## Observability

- **O-001 Metrics Pipeline:** Export metrics/traces via OpenTelemetry to chosen backend (Prometheus/OTLP). Ensure dashboards exist (`docs/observability.md`).
- **O-002 Log Correlation:** Include `trace_id`, `tenant_id` (hashed), `run_id` in logs.
- **O-003 Alerting:** Alerts triggered within 5 minutes of SLA breach (Outbox, scheduler, Composio errors).

## Accessibility & UX Quality

- **A-001 WCAG 2.1 AA compliance** with keyboard support (shortcuts defined in `docs/ux.md`).
- **A-002 Responsiveness:** Support 1280px width; degrade gracefully on smaller screens.
- **A-003 Localization Readiness:** UI copy externalized, dynamic text uses translation pipeline (future backlog). Ensure data/time formatting localized.

## Operational Preparedness

- **OP-001 Runbooks:** Outbox DLQ, Composio outage, trust anomaly runbooks maintained (`runbooks/`, to be created).
- **OP-002 Backup Strategy:** Daily database backups with point-in-time recovery; secret rotation quarterly.
- **OP-003 Compliance Reviews:** Privacy + security reviews quarterly; update threat model with findings.

## Known Gaps

- Observability stack not yet chosen; decision required in Sprint 0.
- Localization tooling pending; flag in roadmap Sprint 3.
- Runbooks directory not yet populated (action item in `docs/todo.md`).
