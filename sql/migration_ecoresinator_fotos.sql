-- Ecoresinator só com foto: fotos da rotina (mesmo bucket 'checklist-fotos', pasta ecoresinator/).
-- Rodar UMA VEZ no SQL Editor do Supabase. Idempotente.
create table if not exists ecoresinator_fotos (
    id             uuid primary key default gen_random_uuid(),
    ecoresinator_id uuid not null references ecoresinator_checklists(id) on delete cascade,
    caminho        text not null,
    enviado_por    uuid references usuarios(id),
    enviado_em     timestamptz not null default now()
);
create index if not exists idx_eco_fotos_ck on ecoresinator_fotos (ecoresinator_id);
alter table ecoresinator_fotos enable row level security;
drop policy if exists "app_full_access" on ecoresinator_fotos;
create policy "app_full_access" on ecoresinator_fotos for all using (true) with check (true);
