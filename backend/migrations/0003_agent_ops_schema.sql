-- ============================================================
-- AIO-1.1 | WB-A.4 (part 1/2) | Schema Agent/Ops Migration
-- Tables: agent_definitions, agent_runs, sources, model_usage
-- Blueprint: บทที่ 6 (Entities), บทที่ 12 (Cost/Observability), D-015
-- ============================================================

create table if not exists public.agent_definitions (
    id            uuid primary key default gen_random_uuid(),
    workspace_id  uuid not null references public.workspaces(id) on delete cascade,
    name          text not null,
    role          text,
    config        jsonb not null default '{}'::jsonb,
    status        text not null default 'provisional' check (status in ('provisional','active','retired')),
    version       integer not null default 1,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now()
);
create index if not exists idx_agentdef_workspace_id on public.agent_definitions(workspace_id);

create table if not exists public.agent_runs (
    id            uuid primary key default gen_random_uuid(),
    workspace_id  uuid not null references public.workspaces(id) on delete cascade,
    agent_id      uuid references public.agent_definitions(id) on delete set null,
    task_id       uuid references public.tasks(id) on delete set null,
    status        text not null default 'running' check (status in ('running','succeeded','failed','cancelled')),
    started_at    timestamptz not null default now(),
    finished_at   timestamptz,
    result        jsonb not null default '{}'::jsonb
);
create index if not exists idx_agentruns_workspace_id on public.agent_runs(workspace_id);
create index if not exists idx_agentruns_task_id on public.agent_runs(task_id);

create table if not exists public.sources (
    id            uuid primary key default gen_random_uuid(),
    workspace_id  uuid not null references public.workspaces(id) on delete cascade,
    url           text,
    title         text,
    source_type   text,
    metadata      jsonb not null default '{}'::jsonb,
    created_at    timestamptz not null default now()
);
create index if not exists idx_sources_workspace_id on public.sources(workspace_id);

create table if not exists public.model_usage (
    id             uuid primary key default gen_random_uuid(),
    workspace_id   uuid not null references public.workspaces(id) on delete cascade,
    provider       text not null,
    model          text not null,
    input_tokens   integer not null default 0,
    output_tokens  integer not null default 0,
    cost_usd       numeric(12,6) not null default 0,
    created_at     timestamptz not null default now()
);
create index if not exists idx_modelusage_workspace_id on public.model_usage(workspace_id);
create index if not exists idx_modelusage_created_at on public.model_usage(created_at);
