-- Seed demo tenant data aligned with 001_init.sql (universal schema).

-- Tenant baseline -----------------------------------------------------------
insert into tenants (id, name, plan)
values (
    '11111111-1111-1111-1111-111111111111',
    'Demo Tenant',
    'demo'
)
on conflict (id) do nothing;

-- Strategic objectives used by the desk/agent prompt ------------------------
insert into objectives (id, tenant_id, title, metric, target, horizon, summary)
values
    (
        '22222222-2222-2222-2222-222222222222',
        '11111111-1111-1111-1111-111111111111',
        'Increase renewal rate',
        'renewal_rate',
        '+5% QoQ',
        'Q4',
        'Partner with CSMs to contact at-risk customers before renewal milestones.'
    ),
    (
        '33333333-3333-3333-3333-333333333333',
        '11111111-1111-1111-1111-111111111111',
        'Improve support SLA',
        'sla_achieved',
        '>= 95%',
        'Monthly',
        'Ensure all priority incidents receive responses within 30 minutes.'
    )
on conflict (id) do nothing;

-- Guardrail defaults (quiet hours, trust threshold, evidence) ---------------
insert into guardrails (tenant_id, quiet_hours, trust_threshold, scopes, require_evidence)
values (
    '11111111-1111-1111-1111-111111111111',
    jsonb_build_object('start', 22, 'end', 6),
    0.8,
    jsonb_build_object('allowed', array['GMAIL', 'SLACK']),
    true
)
on conflict (tenant_id) do nothing;

-- Connected accounts showcase -----------------------------------------------
insert into connected_accounts (
    id,
    tenant_id,
    provider,
    status,
    scopes,
    linked_at,
    metadata
)
values (
    '55555555-5555-5555-5555-555555555555',
    '11111111-1111-1111-1111-111111111111',
    'SLACK',
    'connected',
    array['SLACK.CHAT:WRITE'],
    now(),
    jsonb_build_object('workspace', 'demo-space', 'connected_by', 'seed')
)
on conflict (id) do nothing;

-- Catalog entries pulled from Composio (write tools) ------------------------
insert into tool_catalog (
    tenant_id,
    tool_slug,
    display_name,
    description,
    version,
    risk,
    category,
    read_write_flags,
    risk_default,
    approval_default,
    write_allowed,
    rate_bucket,
    schema,
    required_scopes
)
values
    (
        '11111111-1111-1111-1111-111111111111',
        'GMAIL__drafts.create',
        'Create Gmail Draft',
        'Prepare a Gmail draft message for user review.',
        '1.0',
        'medium',
        'write',
        jsonb_build_object('read', false, 'write', true),
        'medium',
        'required',
        false,
        'email.daily',
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
    ),
    (
        '11111111-1111-1111-1111-111111111111',
        'SLACK__chat.postMessage',
        'Post Slack Message',
        'Send a message to a Slack channel on behalf of the tenant.',
        '1.0',
        'low',
        'write',
        jsonb_build_object('read', false, 'write', true),
        'low',
        'auto',
        true,
        'slack.minute',
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
on conflict (tenant_id, tool_slug, version) do update set
    display_name = excluded.display_name,
    description = excluded.description,
    risk = excluded.risk,
    category = excluded.category,
    read_write_flags = excluded.read_write_flags,
    risk_default = excluded.risk_default,
    approval_default = excluded.approval_default,
    write_allowed = excluded.write_allowed,
    rate_bucket = excluded.rate_bucket,
    schema = excluded.schema,
    required_scopes = excluded.required_scopes,
    updated_at = now();

-- Optional policy override example -----------------------------------------
insert into tool_policies (
    tenant_id,
    composio_app,
    tool_key,
    approval,
    write_allowed
)
values (
    '11111111-1111-1111-1111-111111111111',
    'SLACK',
    'chat.postMessage',
    'required',
    true
)
on conflict (tenant_id, composio_app, tool_key) do nothing;

-- Employees & routing context ----------------------------------------------
insert into employees (id, tenant_id, name, role, autonomy, status)
values (
    '66666666-6666-6666-6666-666666666666',
    '11111111-1111-1111-1111-111111111111',
    'Avery Collins',
    'assistant',
    0.6,
    'active'
)
on conflict (id) do nothing;

insert into program_assignments (
    employee_id,
    program_id,
    tenant_id,
    capacity_per_day,
    priority,
    enabled
)
values (
    '66666666-6666-6666-6666-666666666666',
    'renewals',
    '11111111-1111-1111-1111-111111111111',
    8,
    40,
    true
)
on conflict (employee_id, program_id) do nothing;

-- Active task/envelope context ---------------------------------------------
insert into tasks (
    id,
    tenant_id,
    employee_id,
    objective_id,
    program_id,
    title,
    status,
    proposed_at
)
values (
    '77777777-7777-7777-7777-777777777777',
    '11111111-1111-1111-1111-111111111111',
    '66666666-6666-6666-6666-666666666666',
    '22222222-2222-2222-2222-222222222222',
    'renewals',
    'Send renewal reminder to ACME Corp',
    'proposed',
    now()
)
on conflict (id) do nothing;

insert into outbox (
    id,
    tenant_id,
    tool_slug,
    arguments,
    connected_account_id,
    risk,
    external_id,
    status,
    metadata
)
values (
    '44444444-4444-4444-4444-444444444444',
    '11111111-1111-1111-1111-111111111111',
    'GMAIL__drafts.create',
    jsonb_build_object(
        'to', 'customer@example.com',
        'subject', 'Renewal reminder',
        'body', 'Hi there, your renewal is coming up next week.'
    ),
    null,
    'medium',
    'env-seed-gmail-001',
    'pending',
    jsonb_build_object('seed', true)
)
on conflict (id) do nothing;

insert into actions (
    id,
    tenant_id,
    task_id,
    external_id,
    type,
    tool,
    args,
    risk,
    approval,
    constraints,
    result,
    created_at,
    sent_at,
    completed_at
)
values (
    '88888888-8888-8888-8888-888888888888',
    '11111111-1111-1111-1111-111111111111',
    '77777777-7777-7777-7777-777777777777',
    'env-seed-slack-001',
    'mcp.exec',
    jsonb_build_object(
        'name', 'chat.postMessage',
        'composio_app', 'SLACK'
    ),
    jsonb_build_object('channel', '#renewals', 'text', 'Reminder sent to ACME Corp.'),
    'low',
    'granted',
    jsonb_build_object('rate_bucket', 'slack.minute'),
    jsonb_build_object('status', 'sent'),
    now() - interval '2 minutes',
    now() - interval '90 seconds',
    now() - interval '60 seconds'
)
on conflict (id) do nothing;

-- Seed audit log snapshot ---------------------------------------------------
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
    jsonb_build_object(
        'guardrail', 'quiet_hours',
        'allowed', true,
        'window', jsonb_build_object('start', 22, 'end', 6)
    )
)
on conflict do nothing;
