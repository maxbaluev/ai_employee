# Glossary

| Term | Definition |
|------|------------|
| **ADK** | Google Agent Development Kit providing the agent runtime, callbacks, and event stream consumed by CopilotKit. |
| **AGUI** | Agent GUI event protocol emitted by ADK and consumed by CopilotKit to synchronise state. |
| **Composio** | Third-party Model Context Protocol provider supplying tool schemas, OAuth flows, and execution APIs. |
| **Envelope** | JSON payload containing the tool slug, arguments, connected account, and metadata queued for execution. |
| **Outbox** | Background worker responsible for executing envelopes via Composio with retries and audit logging. |
| **Quiet hours** | Guardrail preventing actions from executing during operator-defined windows. |
| **Trust score** | Rolling measure of autonomous reliability used to decide when actions auto-execute. |
| **Warm scan** | First-pass read of tenant data after connecting Composio to populate signals. |
| **Trickle refresh** | Periodic read jobs that keep evidence up to date without manual prompts. |
