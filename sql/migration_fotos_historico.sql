-- Migration: fotos nos checklists + marca de "assinado incompleto".
-- Rodar UMA VEZ no SQL Editor do Supabase. Idempotente.

alter table checklists add column if not exists incompleto boolean not null default false;

create table if not exists checklist_fotos (
    id              uuid primary key default gen_random_uuid(),
    checklist_id    uuid not null references checklists(id) on delete cascade,
    item_id         uuid not null references checklist_template_itens(id),
    horario_id      uuid not null references checklist_template_horarios(id),
    caminho         text not null,
    enviado_por     uuid references usuarios(id),
    enviado_em      timestamptz not null default now()
);
create index if not exists idx_fotos_checklist on checklist_fotos (checklist_id);

alter table checklist_fotos enable row level security;
drop policy if exists "app_full_access" on checklist_fotos;
create policy "app_full_access" on checklist_fotos for all using (true) with check (true);

-- Bucket privado pras fotos (as fotos são baixadas pelo app, não por link público).
insert into storage.buckets (id, name, public)
values ('checklist-fotos', 'checklist-fotos', false)
on conflict (id) do nothing;

drop policy if exists "app_full_access_fotos" on storage.objects;
create policy "app_full_access_fotos" on storage.objects
    for all using (bucket_id = 'checklist-fotos') with check (bucket_id = 'checklist-fotos');

-- Medidores de espaço (usados em Administração → Armazenamento).
create or replace function tamanho_banco_mb() returns numeric
language sql security definer set search_path = public as $$
    select round(pg_database_size(current_database()) / 1048576.0, 1)
$$;

create or replace function tamanho_fotos_mb() returns numeric
language sql security definer set search_path = public, storage as $$
    select round(coalesce(sum((metadata->>'size')::bigint), 0) / 1048576.0, 1)
    from storage.objects where bucket_id = 'checklist-fotos'
$$;

grant execute on function tamanho_banco_mb(), tamanho_fotos_mb() to anon, authenticated;

-- Índice redundante (o UNIQUE de checklist_respostas já cobre checklist_id):
-- remove pra economizar espaço do banco.
drop index if exists idx_respostas_checklist;
