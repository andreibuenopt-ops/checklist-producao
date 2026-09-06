-- Migration: tipo_area (interno/externo) + justificativa de atraso.
-- Rodar UMA VEZ no SQL Editor do Supabase. Idempotente.

alter table checklist_templates
    add column if not exists tipo_area text not null default 'interno'
        check (tipo_area in ('interno', 'externo'));

create table if not exists checklist_justificativas_atraso (
    id              uuid primary key default gen_random_uuid(),
    checklist_id    uuid not null references checklists(id) on delete cascade,
    horario_id      uuid not null references checklist_template_horarios(id),
    justificativa   text not null,
    registrado_por  uuid references usuarios(id),
    registrado_em   timestamptz not null default now(),
    unique (checklist_id, horario_id)
);

alter table checklist_justificativas_atraso enable row level security;
drop policy if exists "app_full_access" on checklist_justificativas_atraso;
create policy "app_full_access" on checklist_justificativas_atraso for all using (true) with check (true);
