# Universal Action Envelope (mcp.exec)

**Status:** Implemented (contract) · In progress (worker execution telemetry)

The Action Envelope is the only write contract in the platform. Agents never call vendor
APIs directly; they propose envelopes. The Outbox worker is the single executor.

## Invariants

- Single type: `mcp.exec` (Composio MCP).
- Idempotent: `external_id` dedupes at worker level; provider conflicts mark `conflict`.
- Schema‑driven UI: preview and validation come from the Composio JSON Schema.
- Safety gates: quiet hours, trust, scopes, rate buckets, DNC enforced before send.
- RLS: `actions` and `outbox` rows are tenant‑scoped; UI reads via views.

## JSON Structure

```json
{
  "action_id": "uuid",
  "external_id": "stable-id",
  "tenant_id": "uuid",
  "employee_id": "uuid",
  "type": "mcp.exec",
  "tool": { "name": "slack.chat.postMessage", "composio_app": "slack" },
  "args": { "channel": "#cs", "text": "Daily digest …" },
  "risk": "low|medium|high",
  "approval": "auto|required|granted|denied",
  "constraints": { "rate_bucket": "slack.minute", "must_run_before": "<iso8601>" },
  "result": { "status": "pending|sending|sent|failed|conflict|skipped", "provider_id": null, "error": null },
  "timestamps": { "created_at": "<iso8601>", "sent_at": null, "completed_at": null }
}
```

See `docs/schemas/action-envelope.json` for the canonical JSON Schema.

## Execution Lifecycle

1. Agent proposes an envelope and emits shared‑state deltas for UI preview.
2. Operator approves (or auto‑approval when allowed) → `actions.approval_state = granted`.
3. Outbox worker polls `outbox (status=pending)` by `next_attempt_at` and executes via `composio.tools.execute`.
4. On success: `result.status = sent` and `provider_id` set. On conflict: `status = conflict`.
5. Failures retry with jitter until `outbox_max_attempts` then move to DLQ.

## Rates & Buckets

- Each envelope may include `constraints.rate_bucket` (e.g., `email.daily`, `slack.minute`, `tickets.api`).
- Worker enforces per‑bucket concurrency and backoff.

## UI Mapping

- Approvals: rendered from the Composio schema; `Approve` button disabled until valid.
- Activity Timeline: reflects `result.status` transitions; conflicts count as success.
- Undo: allowed while `status='pending'` (deschedules the envelope).

## Storage & Indexes

- `actions(external_id)` unique partial index to prevent duplicates.
- `outbox(status, next_attempt_at)` for polling.
- GIN indexes for JSONB fields referenced by readers.

Align worker code, UI preview, and Supabase migrations to this document to avoid drift.

