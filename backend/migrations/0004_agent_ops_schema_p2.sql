-- ============================================================
-- AIO-1.1 | WB-A.4 (part 2/2) | Schema Agent/Ops Migration
-- Tables: tool_connections, backup_records, knowledge_documents, knowledge_chunks
-- Blueprint: บทที่ 6, D-012 (Backup), D-016 (kill switch)
-- Note: knowledge_chunks.embedding (pgvector) deferred to RAG phase
-- ============================================================

create table if not exists public.tool_connections (
    id            uuid primary key default gen_random_uuid(),
    workspace_id  uuid not null references public.workspaces(id) on delete cascade,
    tool_name     text not null,
    provider      text,
    enabled       boolean not null default false,
    kill_switch   boolean not null default false,
    config        jsonb not null default '{}'::jsonb,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now()
);
create index if not exists idx_toolconn_workspace_id on public.tool_connections(workspace_id);

create table if not exists public.backup_records (
    id            uuid primary key default gen_random_uuid(),
    workspace_id  uuid references public.workspaces(id) on delete cascade,
    backup_type   text not null,
    status        text not null default 'pending' check (status in ('pending','success','failed')),
    location      text,
    size_bytes    bigint,
    started_at    timestamptz not null default now(),
    finished_at   timestamptz
);
create index if not exists idx_backup_started_at on public.backup_records(started_at);

create table if not exists public.knowledge_documents (
    id            uuid primary key default gen_random_uuid(),
    workspace_id  uuid not null references public.workspaces(id) on delete cascade,
    source_id     uuid references public.sources(id) on delete set null,
    title         text not null,
    content       text,
    metadata      jsonb not null default '{}'::jsonb,
    created_at    timestamptz not null default now()
);
create index if not exists idx_knowdoc_workspace_id on public.knowledge_documents(workspace_id);

create table if not exists public.knowledge_chunks (
    id            uuid primary key default gen_random_uuid(),
    workspace_id  uuid not null references public.workspaces(id) on delete cascade,
    document_id   uuid not null references public.knowledge_documents(id) on delete cascade,
    chunk_index   integer not null default 0,
    content       text not null,
    metadata      jsonb not null default '{}'::jsonb,
    created_at    timestamptz not null default now(),
    constraint uq_chunk unique (document_id, chunk_index)
);
create index if not exists idx_knowchunk_document_id on public.knowledge_chunks(document_id);
