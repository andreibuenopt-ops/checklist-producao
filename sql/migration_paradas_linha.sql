-- Migration: PARADA DE LINHA — 3 tipos de checklist (programada, saída de
-- finos, corretiva), um checklist novo a cada parada, com foto por pergunta.
-- Rodar UMA VEZ no SQL Editor do Supabase. Idempotente.
-- As perguntas de cada tipo são cadastradas pela tela: Administração > Paradas.

create table if not exists paradas_itens (
    id          uuid primary key default gen_random_uuid(),
    tipo        text not null check (tipo in ('programada', 'saida_finos', 'corretiva')),
    ordem       smallint not null,
    pergunta    text not null,
    exige_foto  boolean not null default true,
    ativo       boolean not null default true,
    unique (tipo, ordem)
);

create table if not exists paradas (
    id              uuid primary key default gen_random_uuid(),
    tipo            text not null check (tipo in ('programada', 'saida_finos', 'corretiva')),
    turno_id        smallint not null references turnos(id),
    data            date not null,   -- dia de produção do turno
    iniciada_em     timestamptz not null default now(),
    descricao       text not null default '',
    colaborador_id  uuid references usuarios(id),
    supervisor_id   uuid references usuarios(id),
    status          text not null default 'em_andamento' check (status in ('em_andamento', 'completo')),
    comentario      text not null default '',
    concluido_em    timestamptz,
    atualizado_em   timestamptz not null default now()
);
create index if not exists idx_paradas_data on paradas (data, turno_id);

create table if not exists paradas_respostas (
    id              uuid primary key default gen_random_uuid(),
    parada_id       uuid not null references paradas(id) on delete cascade,
    item_id         uuid not null references paradas_itens(id),
    resposta        text check (resposta in ('Sim', 'Não', 'N/A')),
    observacao      text not null default '',
    respondido_por  uuid references usuarios(id),
    respondido_em   timestamptz not null default now(),
    unique (parada_id, item_id)
);

create table if not exists paradas_fotos (
    id           uuid primary key default gen_random_uuid(),
    parada_id    uuid not null references paradas(id) on delete cascade,
    item_id      uuid not null references paradas_itens(id),
    caminho      text not null,
    enviado_por  uuid references usuarios(id),
    enviado_em   timestamptz not null default now()
);
create index if not exists idx_paradas_fotos_parada on paradas_fotos (parada_id);

drop trigger if exists trg_paradas_atualizado_em on paradas;
create trigger trg_paradas_atualizado_em
    before update on paradas
    for each row execute function set_atualizado_em();

alter table paradas_itens enable row level security;
alter table paradas enable row level security;
alter table paradas_respostas enable row level security;
alter table paradas_fotos enable row level security;
drop policy if exists "app_full_access" on paradas_itens;
create policy "app_full_access" on paradas_itens for all using (true) with check (true);
drop policy if exists "app_full_access" on paradas;
create policy "app_full_access" on paradas for all using (true) with check (true);
drop policy if exists "app_full_access" on paradas_respostas;
create policy "app_full_access" on paradas_respostas for all using (true) with check (true);
drop policy if exists "app_full_access" on paradas_fotos;
create policy "app_full_access" on paradas_fotos for all using (true) with check (true);
