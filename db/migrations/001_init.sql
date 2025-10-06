-- 001_init.sql
-- Draft Supabase schema derived from docs/architecture/data-roadmap.md

create extension if not exists pgcrypto;

create table if not exists tenants (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    plan text not null default 'free',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists tenants_plan_idx on tenants(plan);
-- TODO: enable row level security (RLS) and add tenant-aware policies

create table if not exists objectives (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references tenants(id) on delete cascade,
    title text not null,
    metric text not null,
    target numeric,
    horizon interval,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists objectives_tenant_metric_idx on objectives(tenant_id, metric);
-- TODO: RLS using tenant_id claim once auth wiring is in place

create table if not exists guardrails (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null unique references tenants(id) on delete cascade,
    quiet_hours jsonb,
    trust_threshold numeric,
    scopes jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
-- TODO: RLS policies for tenant owners and service role updates

create table if not exists connected_accounts (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references tenants(id) on delete cascade,
    provider text not null,
    status text not null default 'pending',
    scopes text[] default array[]::text[],
    linked_at timestamptz,
    metadata jsonb,
    created_at timestamptz not null default now()
);

create index if not exists connected_accounts_tenant_provider_idx
    on connected_accounts(tenant_id, provider);
-- TODO: RLS policies allowing tenants to view/manage their connected accounts

create table if not exists tool_catalog (
    id bigserial primary key,
    tenant_id uuid references tenants(id) on delete cascade,
    tool_slug text not null,
    version text not null default 'latest',
    risk text,
    schema jsonb,
    updated_at timestamptz not null default now()
);

create unique index if not exists tool_catalog_tenant_slug_version_idx
    on tool_catalog(tenant_id, tool_slug, version);
-- TODO: RLS allowing read access for tenant, writes via catalog sync job

create table if not exists outbox (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references tenants(id) on delete cascade,
    envelope jsonb not null,
    status text not null default 'pending',
    attempts integer not null default 0,
    external_id text,
    next_run_at timestamptz,
    last_error text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists outbox_tenant_status_idx on outbox(tenant_id, status);
create unique index if not exists outbox_external_id_uidx on outbox(external_id);
-- TODO: RLS to allow tenant reads; worker executes with service role

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
-- TODO: RLS permitting tenant read access; inserts via service role only

-- NOTE: enable extension `pgcrypto` for gen_random_uuid() if not already installed.
