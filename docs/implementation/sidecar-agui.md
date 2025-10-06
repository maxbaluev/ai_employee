# Sidecar (AG‑UI) — Event → UI Mapping

**Status:** Implemented (baseline) · In progress (sticky pills, quick actions)

The Sidecar renders the agent’s narration and tool lifecycle from AG‑UI events. Keep the
stream coherent and avoid flooding the UI. Use this mapping as your source of truth.

| Event                        | UI                                                    |
|-----------------------------|-------------------------------------------------------|
| `RUN_STARTED/FINISHED`      | Header banner with timestamp                          |
| `TEXT_MESSAGE_*`            | Streaming narration bubbles (typing effect)           |
| `TOOL_CALL_START/END`       | Inline “Reading Foo…” ✓ with elapsed time             |
| `TOOL_CALL_ARGS`            | Collapsible JSON snippet (dev/debug)                  |
| `STATE_DELTA`               | Counters: low/med/high proposals; approvals remaining |
| `APPROVAL_REQUIRED`         | Sticky pill linking to that approval                  |
| `APPROVAL_DECISION`         | Toast: Approved/Rejected + link to card               |
| `ERROR {retryable|terminal}`| Red banner with action link & recovery guidance       |

Quick actions in the Sidecar:

- Pause employee / Pause all
- Approve all low‑risk
- Explain this plan

Implementation notes:

- Stream via SSE and batch related deltas into a single `STATE_DELTA` when possible.
- Use stable component names for generated UI so Next can hydrate predictably.
- Respect reduced‑motion settings and ensure ARIA live regions are used for updates.

