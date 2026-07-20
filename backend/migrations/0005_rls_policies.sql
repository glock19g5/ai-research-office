-- ============================================================
-- AIO-1.1 | WB-A.5 | Row Level Security (RLS) Migration
-- Scope: all 16 tables (schema public)
-- Blueprint: ch.10 (Security), D-014 (env separation)
--
-- Model (single-user, D-001):
--   workspaces      -> visible when created_by = auth.uid()
--   all other 15    -> visible when workspace_id belongs to caller
--   events/audit_logs -> SELECT + INSERT only (append-only at DB level, ch.12)
--
-- NOTE: service_role key bypasses RLS by design. This layer protects the
-- anon/client path; backend-side authorization is handled at the
-- application layer (Milestone B).
-- ============================================================

create or replace function public.is_workspace_member(ws_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public, pg_temp
as $fn$
  select exists (
    select 1 from public.workspaces w
    where w.id = ws_id and w.created_by = (select auth.uid())
  );
$fn$;

alter table public.workspaces enable row level security;

drop policy if exists p_workspaces_select on public.workspaces;
create policy p_workspaces_select on public.workspaces
  for select using (created_by = (select auth.uid()));

drop policy if exists p_workspaces_insert on public.workspaces;
create policy p_workspaces_insert on public.workspaces
  for insert with check (created_by = (select auth.uid()));

drop policy if exists p_workspaces_update on public.workspaces;
create policy p_workspaces_update on public.workspaces
  for update using (created_by = (select auth.uid()))
  with check (created_by = (select auth.uid()));

drop policy if exists p_workspaces_delete on public.workspaces;
create policy p_workspaces_delete on public.workspaces
  for delete using (created_by = (select auth.uid()));

do $rls$
declare
  t text;
  full_tables text[] := array[
    'projects','tasks','task_dependencies','artifacts','approvals',
    'agent_definitions','agent_runs','sources','model_usage',
    'tool_connections','backup_records','knowledge_documents','knowledge_chunks'
  ];
  append_tables text[] := array['events','audit_logs'];
begin
  foreach t in array full_tables loop
    execute format('alter table public.%I enable row level security', t);
    execute format('drop policy if exists p_%s_select on public.%I', t, t);
    execute format('create policy p_%s_select on public.%I for select using (public.is_workspace_member(workspace_id))', t, t);
    execute format('drop policy if exists p_%s_insert on public.%I', t, t);
    execute format('create policy p_%s_insert on public.%I for insert with check (public.is_workspace_member(workspace_id))', t, t);
    execute format('drop policy if exists p_%s_update on public.%I', t, t);
    execute format('create policy p_%s_update on public.%I for update using (public.is_workspace_member(workspace_id)) with check (public.is_workspace_member(workspace_id))', t, t);
    execute format('drop policy if exists p_%s_delete on public.%I', t, t);
    execute format('create policy p_%s_delete on public.%I for delete using (public.is_workspace_member(workspace_id))', t, t);
  end loop;

  foreach t in array append_tables loop
    execute format('alter table public.%I enable row level security', t);
    execute format('drop policy if exists p_%s_select on public.%I', t, t);
    execute format('create policy p_%s_select on public.%I for select using (public.is_workspace_member(workspace_id))', t, t);
    execute format('drop policy if exists p_%s_insert on public.%I', t, t);
    execute format('create policy p_%s_insert on public.%I for insert with check (public.is_workspace_member(workspace_id))', t, t);
  end loop;
end
$rls$;
