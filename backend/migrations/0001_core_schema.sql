-- ============================================================
-- AIO-1.1 | WB-A.2 | Schema Core Migration
-- Tables: workspaces, projects, tasks, task_dependencies
-- Blueprint: บทที่ 6 (Entities), บทที่ 7 (Task state machine)
-- ============================================================

-- Table 1: workspaces
create table if not exists public.workspaces (
    id            uuid primary key default gen_random_uuid(),
    name          text not null,
    description   text,
    created_by    uuid references auth.users(id),
    version       integer not null default 1,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now()
);
create index if not exists idx_workspaces_created_at on public.workspaces(created_at);

-- Table 2: projects
create table if not exists public.projects (
    id            uuid primary key default gen_random_uuid(),
    workspace_id  uuid not null references public.workspaces(id) on delete cascade,
    name          text not null,
    description   text,
    status        text not null default 'active',
    created_by    uuid references auth.users(id),
    version       integer not null default 1,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now()
);
create index if not exists idx_projects_workspace_id on public.projects(workspace_id);
create index if not exists idx_projects_status on public.projects(status);

-- Table 3: tasks (with state machine)
create table if not exists public.tasks (
    id            uuid primary key default gen_random_uuid(),
    workspace_id  uuid not null references public.workspaces(id) on delete cascade,
    project_id    uuid not null references public.projects(id) on delete cascade,
    title         text not null,
    description   text,
    status        text not null default 'pending'
                  check (status in ('pending','ready','in_progress','blocked','review','approved','completed','failed','cancelled')),
    priority      integer not null default 3 check (priority between 1 and 5),
    created_by    uuid references auth.users(id),
    version       integer not null default 1,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now()
);
create index if not exists idx_tasks_workspace_id on public.tasks(workspace_id);
create index if not exists idx_tasks_project_id on public.tasks(project_id);
create index if not exists idx_tasks_status on public.tasks(status);

-- Table 4: task_dependencies
create table if not exists public.task_dependencies (
    id                  uuid primary key default gen_random_uuid(),
    workspace_id        uuid not null references public.workspaces(id) on delete cascade,
    task_id             uuid not null references public.tasks(id) on delete cascade,
    depends_on_task_id  uuid not null references public.tasks(id) on delete cascade,
    created_at          timestamptz not null default now(),
    constraint uq_task_dependency unique (task_id, depends_on_task_id),
    constraint chk_no_self_dependency check (task_id <> depends_on_task_id)
);
create index if not exists idx_task_deps_task_id on public.task_dependencies(task_id);
create index if not exists idx_task_deps_depends_on on public.task_dependencies(depends_on_task_id);
