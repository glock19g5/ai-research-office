-- 0006_status_alignment.sql
-- WB-B.1 : align DB status constraints with domain enums
-- Ref: Blueprint ch.6 (standard statuses), D-004
-- Idempotent: safe to run more than once.

-- 1. projects : add missing CHECK, align default with ProjectStatus.DRAFT
alter table public.projects
    drop constraint if exists projects_status_check;

alter table public.projects
    alter column status set default 'draft';

alter table public.projects
    add constraint projects_status_check
    check (status in ('draft','planned','active','review',
                      'completed','cancelled','failed'));

-- 2. artifacts : add missing status column + CHECK
alter table public.artifacts
    add column if not exists status text not null default 'draft';

alter table public.artifacts
    drop constraint if exists artifacts_status_check;

alter table public.artifacts
    add constraint artifacts_status_check
    check (status in ('draft','generated','validated','pending_approval',
                      'approved','rejected','published','archived'));

create index if not exists idx_artifacts_status
    on public.artifacts(status);

-- 3. agent_runs : expand 4 -> 7 statuses, align default with QUEUED
alter table public.agent_runs
    drop constraint if exists agent_runs_status_check;

alter table public.agent_runs
    alter column status set default 'queued';

alter table public.agent_runs
    add constraint agent_runs_status_check
    check (status in ('queued','running','waiting_approval','retrying',
                      'succeeded','failed','cancelled'));