# Deployment Guide

**Status:** Planned (no production deployment scripts yet)

Use this as the baseline for creating reproducible environments once the backend is
stateful.

## Environment Matrix

| Environment | Purpose | Differences |
|-------------|---------|-------------|
| `dev` | Individual developer machines | `.env` + local Supabase instance optional |
| `staging` | Shared QA + demos | Real Composio sandbox accounts, Supabase project |
| `prod` | Customer-facing | Hardened secrets, audit retention, alerting |

## Build Artifacts

- **UI** – Next.js app bundled via `next build`. Containerise using the official Node LTS
  image and serve with `next start` or an edge runtime.
- **Agent** – Package as a Python container with the FastAPI app and background workers.
  Include a health endpoint (`/healthz`).
- **Workers** – Outbox executor and schedulers run as separate processes/containers.

## Configuration Management

- Store secrets in your platform’s secret manager (AWS SSM, GCP Secret Manager, etc.).
- Inject runtime configuration via environment variables consumed by `pydantic-settings`.
- Version infrastructure via IaC (Terraform or Pulumi) so database schema, buckets, and
  IAM roles are reproducible.

## Deployment Steps (once infra exists)

1. Build and push containers (`ui`, `agent`, `worker`).
2. Run database migrations.
3. Deploy to staging with feature flags disabled.
4. Run smoke tests (UI + agent health, Composio catalog fetch).
5. Promote to production via blue/green or rolling strategy.

## Rollback Strategy

- Keep the previous container tag available.
- Maintain backward-compatible database migrations whenever possible.
- In case of Composio incidents, toggle the platform into read-only mode (see
  `docs/operations/runbooks/composio-outage.md`).

Update this guide as soon as the first managed environment is created.
