-- ============================================================
-- AIO-1.1 | WB-A.3 | Schema Audit/Flow Migration
-- Tables: events, audit_logs, artifacts, approvals
-- Blueprint: บทที่ 6 (Entities), บทที่ 8 (Side effects), บทที่ 11 (Approval)
-- ============================================================

create table if not exists public.events (
    id              uuid primary key default gen_random_uuid(),
    workspace_id    uuid not null references public.workspaces(id) on delete cascade,
    correlation_id  uuid,
    event_type      text not null,
    actor           text not null,
    payload         jsonb not null default '{}'::jsonb,
    created_at      timestamptz not null default now()
);
create index if not exists idx_events_workspace_id on public.events(workspace_id);
create index if not exists idx_events_correlation_id on public.events(correlation_id);
create index if not exists idx_events_created_at on public.events(created_at);

create table if not exists public.audit_logs (
    id            uuid primary key default gen_random_uuid(),
    workspace_id  uuid not null references public.workspaces(id) on delete cascade,
    action        text not null,
    actor         text not null,
    target_type   text,
    target_id     uuid,
    detail        jsonb not null default '{}'::jsonb,
    created_at    timestamptz not null default now()
);
create index if not exists idx_audit_workspace_id on public.audit_logs(workspace_id);
create index if not exists idx_audit_created_at on public.audit_logs(created_at);

create table if not exists public.artifacts (
    id            uuid primary key default gen_random_uuid(),
    workspace_id  uuid not null references public.workspaces(id) on delete cascade,
    project_id    uuid references public.projects(id) on delete cascade,
    task_id       uuid references public.tasks(id) on delete set null,
    name          text not null,
    content_type  text,
    storage_path  text,
    version       integer not null default 1,
    created_by    uuid references auth.users(id),
    created_at    timestamptz not null default now(),
    constraint uq_artifact_version unique (workspace_id, name, version)
);
create index if not exists idx_artifacts_workspace_id on public.artifacts(workspace_id);
create index if not exists idx_artifacts_project_id on public.artifacts(project_id);

create table if not exists public.approvals (
    id            uuid primary key default gen_random_uuid(),
    workspace_id  uuid not null references public.workspaces(id) on delete cascade,
    task_id       uuid references public.tasks(id) on delete cascade,
    risk_level    text not null default 'B' check (risk_level in ('A','B','C')),
    status        text not null default 'requested'
                  check (status in ('requested','granted','rejected','expired','revoked')),
    requested_by  text,
    decided_by    uuid references auth.users(id),
    expires_at    timestamptz,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now()
);
create index if not exists idx_approvals_workspace_id on public.approvals(workspace_id);
create index if not exists idx_approvals_task_id on public.approvals(task_id);
create index if not exists idx_approvals_status on public.approvals(status);
