-- 001_init.sql (universal)
-- Supabase schema aligned to the universal PRD & Action Envelope
-- Invariants: Composio-only, one executor (Outbox), strict RLS

create extension if not exists pgcrypto;

-- Helper to extract the tenant_id claim from authenticated requests.
create or replace function public.current_tenant_id_uuid() returns uuid as $$
    select nullif(
        nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'tenant_id',
        ''
    )::uuid
$$ language sql stable;

create or replace function public.current_tenant_id() returns uuid as $$
    select public.current_tenant_id_uuid()
$$ language sql stable;

create or replace function public.set_updated_at() returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

create table if not exists tenants (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    plan text not null default 'free',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists tenants_plan_idx on tenants(plan);

create table if not exists objectives (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references tenants(id) on delete cascade,
    title text not null,
    metric text not null,
    target text,
    horizon text,
    summary text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists objectives_tenant_metric_idx on objectives(tenant_id, metric);

create table if not exists guardrails (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null unique references tenants(id) on delete cascade,
    quiet_hours jsonb,
    trust_threshold numeric,
    scopes jsonb default '{}'::jsonb,
    require_evidence boolean default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists connected_accounts (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references tenants(id) on delete cascade,
    provider text not null,
    status text not null default 'pending',
    scopes text[] default array[]::text[],
    linked_at timestamptz,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists connected_accounts_tenant_provider_idx
    on connected_accounts(tenant_id, provider);

create table if not exists tool_catalog (
    id bigserial primary key,
    tenant_id uuid not null references tenants(id) on delete cascade,
    tool_slug text not null,
    display_name text,
    description text,
    version text not null default 'latest',
    risk text,
    -- universal fields
    category text, -- 'read' | 'write' | 'destructive'
    read_write_flags jsonb default '{"read": true, "write": false}'::jsonb,
    risk_default text default 'medium',
    approval_default text default 'required',
    write_allowed boolean default false,
    rate_bucket text,

    schema jsonb not null default '{}'::jsonb,
    required_scopes text[] not null default array[]::text[],
    updated_at timestamptz not null default now()
);

create unique index if not exists tool_catalog_tenant_slug_version_idx
    on tool_catalog(tenant_id, tool_slug, version);

create table if not exists outbox (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references tenants(id) on delete cascade,
    tool_slug text not null,
    arguments jsonb not null,
    connected_account_id text,
    risk text not null default 'medium',
    external_id text,
    trust_context jsonb default '{}'::jsonb,
    metadata jsonb default '{}'::jsonb,
    status text not null default 'pending',
    attempts integer not null default 0,
    -- universal execution controls
    rate_bucket text,
    must_run_before timestamptz,
    result jsonb default '{"status":"pending"}'::jsonb,
    next_run_at timestamptz,
    last_error text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create unique index if not exists outbox_external_id_uidx on outbox(external_id);
create index if not exists outbox_tenant_status_idx on outbox(tenant_id, status);

create table if not exists outbox_dlq (
    id uuid primary key,
    tenant_id uuid not null references tenants(id) on delete cascade,
    tool_slug text not null,
    arguments jsonb not null,
    connected_account_id text,
    risk text not null default 'medium',
    external_id text,
    trust_context jsonb default '{}'::jsonb,
    metadata jsonb default '{}'::jsonb,
    status text not null default 'dlq',
    attempts integer not null default 0,
    last_error text,
    created_at timestamptz not null default now(),
    moved_at timestamptz not null default now()
);

create index if not exists outbox_dlq_tenant_idx on outbox_dlq(tenant_id, moved_at desc);

create table if not exists audit_log (
    id bigint generated always as identity primary key,
    tenant_id uuid references tenants(id) on delete cascade,
    actor_type text,
    actor_id text,
    category text not null,
    payload jsonb,
    created_at timestamptz not null default now()
);

create index if not exists audit_log_tenant_created_idx
    on audit_log(tenant_id, created_at desc);

-- Employees & Programs (multi-employee native)
create table if not exists employees (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references tenants(id) on delete cascade,
    name text not null,
    role text not null default 'assistant',
    autonomy numeric not null default 0.5,
    schedule jsonb default '{}'::jsonb,
    status text not null default 'active',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists employees_tenant_status_idx on employees(tenant_id, status);

create table if not exists program_assignments (
    employee_id uuid not null references employees(id) on delete cascade,
    program_id text not null,
    tenant_id uuid not null references tenants(id) on delete cascade,
    capacity_per_day integer not null default 10,
    priority integer not null default 50,
    enabled boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (employee_id, program_id)
);

create index if not exists program_assignments_tenant_idx on program_assignments(tenant_id, employee_id);

-- Tasks & Actions (minimal tracking)
create table if not exists tasks (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references tenants(id) on delete cascade,
    employee_id uuid references employees(id) on delete set null,
    objective_id uuid references objectives(id) on delete set null,
    program_id text,
    title text not null,
    status text not null default 'proposed',
    proposed_at timestamptz not null default now(),
    approved_at timestamptz,
    executed_at timestamptz,
    seed_ref jsonb default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists tasks_tenant_employee_status_idx on tasks(tenant_id, employee_id, status);

create table if not exists actions (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references tenants(id) on delete cascade,
    task_id uuid references tasks(id) on delete set null,
    employee_id uuid references employees(id) on delete set null,
    -- universal envelope projection (for history; executor is outbox)
    external_id text not null,
    type text not null default 'mcp.exec',
    tool jsonb not null,
    args jsonb not null,
    risk text not null default 'medium',
    approval text not null default 'required',
    constraints jsonb default '{}'::jsonb,
    result jsonb default '{"status":"pending"}'::jsonb,
    created_at timestamptz not null default now(),
    sent_at timestamptz,
    completed_at timestamptz,
    updated_at timestamptz not null default now()
);

create unique index if not exists actions_external_id_uidx on actions(external_id);

-- Updated-at triggers
create trigger tenants_set_updated_at
    before update on tenants
    for each row execute function public.set_updated_at();

create trigger objectives_set_updated_at
    before update on objectives
    for each row execute function public.set_updated_at();

create trigger guardrails_set_updated_at
    before update on guardrails
    for each row execute function public.set_updated_at();

create trigger tool_catalog_set_updated_at
    before update on tool_catalog
    for each row execute function public.set_updated_at();

create trigger outbox_set_updated_at
    before update on outbox
    for each row execute function public.set_updated_at();

create trigger employees_set_updated_at
    before update on employees
    for each row execute function public.set_updated_at();

create trigger program_assignments_set_updated_at
    before update on program_assignments
    for each row execute function public.set_updated_at();

create trigger tasks_set_updated_at
    before update on tasks
    for each row execute function public.set_updated_at();

create trigger actions_set_updated_at
    before update on actions
    for each row execute function public.set_updated_at();

-- Row level security policies
alter table tenants enable row level security;
alter table objectives enable row level security;
alter table guardrails enable row level security;
alter table connected_accounts enable row level security;
alter table tool_catalog enable row level security;
alter table outbox enable row level security;
alter table outbox_dlq enable row level security;
alter table audit_log enable row level security;
alter table employees enable row level security;
alter table program_assignments enable row level security;
alter table tasks enable row level security;
alter table actions enable row level security;

-- Service-role policies
create policy tenants_service_role on tenants
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy objectives_service_role on objectives
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy guardrails_service_role on guardrails
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy connected_accounts_service_role on connected_accounts
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy tool_catalog_service_role on tool_catalog
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy outbox_service_role on outbox
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy outbox_dlq_service_role on outbox_dlq
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

create policy audit_log_service_role on audit_log
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
create policy employees_service_role on employees
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
create policy program_assignments_service_role on program_assignments
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
create policy tasks_service_role on tasks
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
create policy actions_service_role on actions
    for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

-- Tenant-scoped read/write policies
create policy tenants_select_self on tenants
    for select using (
        auth.role() = 'service_role' or id = current_tenant_id_uuid()
    );

create policy objectives_select_own on objectives
    for select using (
        auth.role() = 'service_role' or tenant_id = current_tenant_id_uuid()
    );

create policy objectives_write_own on objectives
    for insert with check (tenant_id = current_tenant_id_uuid());

create policy objectives_update_own on objectives
    for update using (tenant_id = current_tenant_id_uuid())
    with check (tenant_id = current_tenant_id_uuid());

create policy guardrails_select_own on guardrails
    for select using (
        auth.role() = 'service_role' or tenant_id = current_tenant_id_uuid()
    );

create policy guardrails_update_own on guardrails
    for update using (tenant_id = current_tenant_id_uuid())
    with check (tenant_id = current_tenant_id_uuid());

create policy connected_accounts_select_own on connected_accounts
    for select using (
        auth.role() = 'service_role' or tenant_id = current_tenant_id_uuid()
    );

create policy connected_accounts_write_own on connected_accounts
    for insert with check (tenant_id = current_tenant_id_uuid());

create policy connected_accounts_update_own on connected_accounts
    for update using (tenant_id = current_tenant_id_uuid())
    with check (tenant_id = current_tenant_id_uuid());

create policy tool_catalog_select_own on tool_catalog
    for select using (
        auth.role() = 'service_role' or tenant_id = current_tenant_id_uuid()
    );

create policy outbox_select_own on outbox
    for select using (
        auth.role() = 'service_role' or tenant_id = current_tenant_id_uuid()
    );

create policy outbox_dlq_select_own on outbox_dlq
    for select using (
        auth.role() = 'service_role' or tenant_id = current_tenant_id_uuid()
    );

create policy audit_log_select_own on audit_log
    for select using (
        auth.role() = 'service_role' or tenant_id = current_tenant_id_uuid()
    );

create policy employees_select_own on employees
    for select using (
        auth.role() = 'service_role' or tenant_id = current_tenant_id_uuid()
    );

create policy program_assignments_select_own on program_assignments
    for select using (
        auth.role() = 'service_role' or tenant_id = current_tenant_id_uuid()
    );

create policy tasks_select_own on tasks
    for select using (
        auth.role() = 'service_role' or tenant_id = current_tenant_id_uuid()
    );

create policy tasks_write_own on tasks
    for insert with check (tenant_id = current_tenant_id_uuid());

create policy tasks_update_own on tasks
    for update using (tenant_id = current_tenant_id_uuid())
    with check (tenant_id = current_tenant_id_uuid());

create policy actions_select_own on actions
    for select using (
        auth.role() = 'service_role' or tenant_id = current_tenant_id_uuid()
    );

-- Optional helper view of tenant metadata (service role only)
create or replace view public.tenants_overview as
select id, name, plan, created_at from tenants;

-- Views for worker/UI
create or replace view public.outbox_pending_view as
select id, tenant_id, tool_slug, arguments, connected_account_id, risk, external_id,
       status, attempts, next_run_at, rate_bucket, must_run_before, created_at
from outbox
where status = 'pending' and (next_run_at is null or next_run_at <= now())
  and (must_run_before is null or must_run_before > now());

create or replace view public.outbox_history_view as
select id, tenant_id, tool_slug, status, attempts, last_error, created_at, updated_at, result
from outbox
where status in ('sent','failed','conflict','skipped','success')
order by updated_at desc;

-- Policy overrides per tool
create table if not exists tool_policies (
    tenant_id uuid not null references tenants(id) on delete cascade,
    composio_app text not null,
    tool_key text not null,
    risk text,
    approval text,
    write_allowed boolean,
    rate_bucket text,
    updated_at timestamptz not null default now(),
    primary key (tenant_id, composio_app, tool_key)
);
alter table tool_policies enable row level security;
create policy tool_policies_service_role on tool_policies for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
create policy tool_policies_select_own on tool_policies for select using (auth.role() = 'service_role' or tenant_id = current_tenant_id_uuid());

create or replace view public.catalog_tools_view as
select 
  tc.tenant_id,
  tc.tool_slug,
  tc.display_name,
  tc.description,
  tc.category,
  tc.schema,
  tc.required_scopes,
  coalesce(tp.risk, tc.risk_default) as effective_risk,
  coalesce(tp.approval, tc.approval_default) as effective_approval,
  coalesce(tp.write_allowed, tc.write_allowed) as effective_write_allowed,
  coalesce(tp.rate_bucket, tc.rate_bucket) as effective_rate_bucket,
  tc.updated_at
from tool_catalog tc
left join tool_policies tp
  on tp.tenant_id = tc.tenant_id
  and (tc.tool_slug = (tp.composio_app || '.' || tp.tool_key));
