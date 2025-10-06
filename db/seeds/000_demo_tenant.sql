-- Seed demo tenant data for local development.

insert into tenants (id, name, plan)
values (
    '11111111-1111-1111-1111-111111111111',
    'Demo Tenant',
    'demo'
)
on conflict (id) do nothing;

insert into objectives (id, tenant_id, title, metric, target, horizon, summary)
values (
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    'Increase renewal rate',
    'renewal_rate',
    '+5% QoQ',
    'Q4',
    'Partner with CSMs to contact at-risk customers before renewal milestones.'
), (
    '33333333-3333-3333-3333-333333333333',
    '11111111-1111-1111-1111-111111111111',
    'Improve support SLA',
    'sla_achieved',
    '>= 95%',
    'Monthly',
    'Ensure all priority incidents receive responses within 30 minutes.'
)
on conflict (id) do nothing;

insert into guardrails (tenant_id, quiet_hours, trust_threshold, scopes, require_evidence)
values (
    '11111111-1111-1111-1111-111111111111',
    jsonb_build_object('start', 22, 'end', 6),
    0.8,
    jsonb_build_object('allowed', array['GMAIL', 'SLACK']),
    true
)
on conflict (tenant_id) do nothing;

insert into tool_catalog (
    tenant_id,
    tool_slug,
    display_name,
    description,
    version,
    risk,
    schema,
    required_scopes
)
values (
    '11111111-1111-1111-1111-111111111111',
    'GMAIL__drafts.create',
    'Create Gmail Draft',
    'Prepare a Gmail draft message for user review.',
    '1.0',
    'medium',
    jsonb_build_object(
        'type', 'object',
        'required', array['to', 'subject', 'body'],
        'properties', jsonb_build_object(
            'to', jsonb_build_object('type', 'string', 'description', 'Recipient email'),
            'subject', jsonb_build_object('type', 'string'),
            'body', jsonb_build_object('type', 'string')
        )
    ),
    array['GMAIL.SMTP']
), (
    '11111111-1111-1111-1111-111111111111',
    'SLACK__chat.postMessage',
    'Post Slack Message',
    'Send a message to a Slack channel on behalf of the tenant.',
    '1.0',
    'low',
    jsonb_build_object(
        'type', 'object',
        'required', array['channel', 'text'],
        'properties', jsonb_build_object(
            'channel', jsonb_build_object('type', 'string'),
            'text', jsonb_build_object('type', 'string')
        )
    ),
    array['SLACK.CHAT:WRITE']
)
on conflict (tenant_id, tool_slug, version) do nothing;

insert into outbox (
    id,
    tenant_id,
    tool_slug,
    arguments,
    risk,
    status,
    metadata
)
values (
    '44444444-4444-4444-4444-444444444444',
    '11111111-1111-1111-1111-111111111111',
    'GMAIL__drafts.create',
    jsonb_build_object('to', 'customer@example.com', 'subject', 'Renewal reminder', 'body', 'Hi there...'),
    'medium',
    'pending',
    jsonb_build_object('seed', true)
)
on conflict (id) do nothing;

insert into audit_log (
    tenant_id,
    actor_type,
    actor_id,
    category,
    payload
)
values (
    '11111111-1111-1111-1111-111111111111',
    'agent',
    'seed',
    'guardrail',
    jsonb_build_object('guardrail', 'quiet_hours', 'allowed', true)
)
on conflict do nothing;
