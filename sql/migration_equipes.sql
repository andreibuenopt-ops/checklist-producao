-- Migration: EQUIPES (grupo fechado de um líder — ex.: Equipe do Eduardo).
-- Rodar UMA VEZ no SQL Editor do Supabase. Idempotente.
-- A equipe é independente de turno/turma. Cada pessoa entra na equipe numa
-- data e pode sair em outra (transferência), e pode estar em mais de uma equipe.
-- O histórico respeita as datas: um checklist feito antes da transferência
-- continua contando pra equipe antiga.

create table if not exists equipes (
    id         uuid primary key default gen_random_uuid(),
    nome       text not null unique,
    lider_id   uuid references usuarios(id) on delete set null,
    ativa      boolean not null default true,
    criado_em  timestamptz not null default now()
);

create table if not exists equipe_membros (
    id          uuid primary key default gen_random_uuid(),
    equipe_id   uuid not null references equipes(id) on delete cascade,
    usuario_id  uuid not null references usuarios(id) on delete cascade,
    inicio      date not null default current_date,
    fim         date,
    check (fim is null or fim >= inicio),
    unique (equipe_id, usuario_id, inicio)
);
create index if not exists idx_equipe_membros_equipe on equipe_membros (equipe_id);
create index if not exists idx_equipe_membros_usuario on equipe_membros (usuario_id);

alter table equipes enable row level security;
alter table equipe_membros enable row level security;
drop policy if exists "app_full_access" on equipes;
create policy "app_full_access" on equipes for all using (true) with check (true);
drop policy if exists "app_full_access" on equipe_membros;
create policy "app_full_access" on equipe_membros for all using (true) with check (true);
