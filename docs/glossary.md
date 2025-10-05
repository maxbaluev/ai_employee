# Glossary

| Term | Definition |
| ---- | ---------- |
| **AGUI (Agent UI) Protocol** | Event stream format used by CopilotKit and AG-UI clients (`RunStartedEvent`, `ToolCall*`, `StateDeltaEvent`). |
| **Composio** | Model Context Protocol provider offering unified toolkits (read/write) with JSON schemas, scope metadata, and rate limits. Sole integration surface for the platform. |
| **Value Objective** | User-defined outcome (e.g., "Increase demos 20% in 30 days") driving planning prioritization. |
| **Reader Kernel** | Configuration describing how to query Composio read tools and transform results into Signals. |
| **Signal** | Compact representation of tool data (counts, exemplars) produced by kernels; feeds Evidence Cards. |
| **Evidence Card** | UI element summarizing Signal data with supporting details and linkage to Value Objectives. |
| **Action Envelope** | Normalized representation of a proposed write (`tool`, `args`, `risk`, `approval_state`, `constraints`, `external_id`). |
| **Outbox** | Single executor responsible for delivering approved action envelopes to Composio, ensuring idempotency and retries. |
| **Trust Score** | Per-employee metric derived from approvals/edits/errors; controls autonomy gates (Propose/Assist/Trusted). |
| **Warm Scan** | Initial batch of reader kernel executions after Composio connect to seed Evidence Cards. |
| **Trickle Refresh** | Scheduled follow-up runs to keep Signals fresh while respecting rate limits. |
| **JIT Scope Upgrade** | Flow prompting operators to enable additional Composio scopes when an action requires them. |
| **DLQ (Dead Letter Queue)** | Storage for Outbox actions that failed repeatedly; requires operator intervention. |
| **Quiet Hours / DNC** | Guardrails preventing outbound actions during specified times or to Do-Not-Contact entities. |
| **ADR (Architecture Decision Record)** | Structured document capturing significant technical decisions and rationale (`docs/DECISIONS`). |
