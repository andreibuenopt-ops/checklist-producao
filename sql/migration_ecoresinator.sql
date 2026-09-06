-- Migration: formulário dedicado do Ecoresinator (cozinha de cola).
-- Rodar UMA VEZ no SQL Editor do Supabase. Idempotente.

create table if not exists ecoresinator_checklists (
    id                          uuid primary key default gen_random_uuid(),
    turno_id                    smallint not null references turnos(id),
    data                        date not null,
    colaborador_id              uuid references usuarios(id),
    supervisor_id               uuid references usuarios(id),
    horario_real                text not null default '',
    leituras_bicos              jsonb not null default '[]',
    bicos_em_manutencao         text not null default '',
    bicos_em_producao           text not null default '',
    rodizio_ligado              text check (rodizio_ligado in ('Sim', 'Não')),
    flush_ligado                text check (flush_ligado in ('Sim', 'Não')),
    pressao_bomba_resina        numeric,
    pressao_coletor_resina      numeric,
    pressao_bomba_agua          numeric,
    pressao_coletor_agua        numeric,
    pressao_vapor_coletor       numeric,
    vazao_resina_bomba          numeric,
    valvula_proporcional_auto   text check (valvula_proporcional_auto in ('Sim', 'Não')),
    agulhas_force_abertura      text check (agulhas_force_abertura in ('Sim', 'Não')),
    bomba_resina_manutencao     text check (bomba_resina_manutencao in ('Sim', 'Não')),
    bomba_resina_em_uso         text not null default '',
    bomba_parafina_em_uso       text not null default '',
    comentario                  text not null default '',
    status                      text not null default 'pendente'
                                check (status in ('pendente', 'completo')),
    concluido_em                timestamptz,
    criado_em                   timestamptz not null default now(),
    atualizado_em               timestamptz not null default now(),
    unique (turno_id, data)
);

drop trigger if exists trg_ecoresinator_atualizado_em on ecoresinator_checklists;
create trigger trg_ecoresinator_atualizado_em
    before update on ecoresinator_checklists
    for each row execute function set_atualizado_em();

alter table ecoresinator_checklists enable row level security;
drop policy if exists "app_full_access" on ecoresinator_checklists;
create policy "app_full_access" on ecoresinator_checklists for all using (true) with check (true);
