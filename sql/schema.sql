-- =====================================================================
-- Checklist de Produção — schema Supabase (Postgres)
-- Gerado a partir de: FRCDM2011.r02 (Sifter e Ventiladores Externos)
--                      FRCDM2003.r02 (Linha de Formação)
-- =====================================================================

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------
-- USUÁRIOS (cadastro próprio do app: nome, email, matrícula, senha)
-- ---------------------------------------------------------------------
create table if not exists usuarios (
    id            uuid primary key default gen_random_uuid(),
    nome          text not null,
    email         text not null unique,
    matricula     text not null unique,
    senha_hash    text not null,
    papel         text not null default 'operador'
                  check (papel in ('operador', 'supervisor', 'admin')),
    ativo         boolean not null default true,
    criado_em     timestamptz not null default now()
);

-- ---------------------------------------------------------------------
-- TURNOS (fixos: Manhã / Tarde / Noite)
-- ---------------------------------------------------------------------
create table if not exists turnos (
    id            smallint primary key,
    nome          text not null unique,
    hora_inicio   time not null,
    hora_fim      time not null,
    ordem         smallint not null
);

insert into turnos (id, nome, hora_inicio, hora_fim, ordem) values
    (1, 'Manhã', '07:00', '15:00', 1),
    (2, 'Tarde', '15:00', '23:00', 2),
    (3, 'Noite', '23:00', '07:00', 3)
on conflict (id) do nothing;

-- ---------------------------------------------------------------------
-- MODELOS DE CHECKLIST (um por formulário/área: Sifter, Linha de Formação, ...)
-- ---------------------------------------------------------------------
create table if not exists checklist_templates (
    id            uuid primary key default gen_random_uuid(),
    codigo        text not null unique,      -- ex: FRCDM2011.r02
    titulo        text not null,             -- ex: Checklist de inspeções - Sifter
    area          text not null,             -- ex: Sifter e Ventiladores Externos
    slug          text not null unique,      -- usado no QR Code: ?area=slug
    revisao       text,
    observacao    text,
    ativo         boolean not null default true,
    criado_em     timestamptz not null default now()
);

-- Perguntas de cada modelo, na ordem em que aparecem no formulário
create table if not exists checklist_template_itens (
    id            uuid primary key default gen_random_uuid(),
    template_id   uuid not null references checklist_templates(id) on delete cascade,
    ordem         smallint not null,
    pergunta      text not null,
    unique (template_id, ordem)
);

-- Horários de checagem (rondas) dentro de cada turno, por modelo
create table if not exists checklist_template_horarios (
    id            uuid primary key default gen_random_uuid(),
    template_id   uuid not null references checklist_templates(id) on delete cascade,
    turno_id      smallint not null references turnos(id),
    horario       time not null,
    ordem         smallint not null,
    unique (template_id, turno_id, horario)
);

-- ---------------------------------------------------------------------
-- INSTÂNCIAS DE CHECKLIST (um registro por template + turno + data)
-- ---------------------------------------------------------------------
create table if not exists checklists (
    id              uuid primary key default gen_random_uuid(),
    template_id     uuid not null references checklist_templates(id),
    turno_id        smallint not null references turnos(id),
    data            date not null,
    colaborador_id  uuid references usuarios(id),
    supervisor_id   uuid references usuarios(id),
    comentario      text not null default '',
    status          text not null default 'pendente'
                    check (status in ('pendente', 'em_andamento', 'completo')),
    concluido_em    timestamptz,
    criado_em       timestamptz not null default now(),
    atualizado_em   timestamptz not null default now(),
    unique (template_id, turno_id, data)
);

create index if not exists idx_checklists_data on checklists (data);
create index if not exists idx_checklists_template_data on checklists (template_id, data);

-- Respostas: cada pergunta é respondida em cada horário/ronda do turno
create table if not exists checklist_respostas (
    id              uuid primary key default gen_random_uuid(),
    checklist_id    uuid not null references checklists(id) on delete cascade,
    item_id         uuid not null references checklist_template_itens(id),
    horario_id      uuid not null references checklist_template_horarios(id),
    resposta        text check (resposta in ('Sim', 'Não', 'N/A')),
    respondido_por  uuid references usuarios(id),
    respondido_em   timestamptz not null default now(),
    unique (checklist_id, item_id, horario_id)
);

create index if not exists idx_respostas_checklist on checklist_respostas (checklist_id);

-- ---------------------------------------------------------------------
-- Trigger: atualiza automaticamente checklists.atualizado_em
-- ---------------------------------------------------------------------
create or replace function set_atualizado_em()
returns trigger as $$
begin
    new.atualizado_em = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists trg_checklists_atualizado_em on checklists;
create trigger trg_checklists_atualizado_em
    before update on checklists
    for each row execute function set_atualizado_em();

-- =====================================================================
-- RLS
-- O app (Streamlit) roda inteiramente no servidor: a chave do Supabase
-- fica em st.secrets e NUNCA chega ao navegador do usuário (diferente de
-- uma SPA React, onde a chave vai no bundle JS). A autenticação de quem
-- pode usar o app é feita pelo próprio app (tabela `usuarios`), não pelo
-- Supabase Auth — por isso as policies abaixo liberam o acesso para a
-- key usada pelo app, e o controle de quem entra fica 100% no login do
-- Streamlit.
-- =====================================================================
alter table usuarios enable row level security;
alter table turnos enable row level security;
alter table checklist_templates enable row level security;
alter table checklist_template_itens enable row level security;
alter table checklist_template_horarios enable row level security;
alter table checklists enable row level security;
alter table checklist_respostas enable row level security;

drop policy if exists "app_full_access" on usuarios;
create policy "app_full_access" on usuarios for all using (true) with check (true);

drop policy if exists "app_full_access" on turnos;
create policy "app_full_access" on turnos for all using (true) with check (true);

drop policy if exists "app_full_access" on checklist_templates;
create policy "app_full_access" on checklist_templates for all using (true) with check (true);

drop policy if exists "app_full_access" on checklist_template_itens;
create policy "app_full_access" on checklist_template_itens for all using (true) with check (true);

drop policy if exists "app_full_access" on checklist_template_horarios;
create policy "app_full_access" on checklist_template_horarios for all using (true) with check (true);

drop policy if exists "app_full_access" on checklists;
create policy "app_full_access" on checklists for all using (true) with check (true);

drop policy if exists "app_full_access" on checklist_respostas;
create policy "app_full_access" on checklist_respostas for all using (true) with check (true);

-- =====================================================================
-- SEED: Template 1 — Sifter e Ventiladores Externos (FRCDM2011.r02)
-- =====================================================================
insert into checklist_templates (codigo, titulo, area, slug, revisao, observacao) values
(
    'FRCDM2011.r02',
    'Checklist de inspeções - Sifter',
    'Sifter e Ventiladores Externos',
    'sifter',
    'r02',
    'Obs.: todas as vezes que a resposta for Não para as questões, deve haver um comentário sobre a situação. Se foi resolvido, como foi resolvido ou se ficará como pendência.'
)
on conflict (codigo) do nothing;

insert into checklist_template_itens (template_id, ordem, pergunta)
select t.id, x.ordem, x.pergunta
from checklist_templates t
cross join (values
    (1, 'Existe vazamento de fibra em algum ponto específico do prédio?'),
    (2, 'Existe alguma porta de inspeção danificada ou acrílico quebrado?'),
    (3, 'Existe algum vazamento de ar nos cilindros de acionamentos dos flaps existentes no processo do Sifter?'),
    (4, 'Ferramentas armazenadas no local adequado?'),
    (5, 'Realizado purga no cavalete de vapor dos radiadores de aquecimento do prédio?'),
    (6, 'Verificar se tem água nos drenos do cavalete de inundação e manter fechado o mesmo.'),
    (7, 'Regulagem dos descartes estão apresentando que tipo de fibra?'),
    (8, 'Bunkers de rejeito foram esvaziados?'),
    (9, 'Algum ruído nos ventiladores do sifter?')
) as x(ordem, pergunta)
where t.codigo = 'FRCDM2011.r02'
on conflict (template_id, ordem) do nothing;

insert into checklist_template_horarios (template_id, turno_id, horario, ordem)
select t.id, x.turno_id, x.horario, x.ordem
from checklist_templates t
cross join (values
    (3, time '23:30', 1), (3, time '03:30', 2),   -- Noite
    (1, time '07:30', 1), (1, time '11:30', 2),   -- Manhã
    (2, time '15:30', 1), (2, time '19:30', 2)    -- Tarde
) as x(turno_id, horario, ordem)
where t.codigo = 'FRCDM2011.r02'
on conflict (template_id, turno_id, horario) do nothing;

-- =====================================================================
-- SEED: Template 2 — Linha de Formação (FRCDM2003.r02)
-- =====================================================================
insert into checklist_templates (codigo, titulo, area, slug, revisao, observacao) values
(
    'FRCDM2003.r02',
    'Checklist de inspeções - Linha de Formação',
    'Linha de Formação',
    'linha-formacao',
    'r02',
    'Obs.: todas as vezes que a resposta for Não para as questões, deve haver um comentário sobre a situação. Se foi resolvido, como foi resolvido ou se ficará como pendência.'
)
on conflict (codigo) do nothing;

insert into checklist_template_itens (template_id, ordem, pergunta)
select t.id, x.ordem, x.pergunta
from checklist_templates t
cross join (values
    (1,  'Correia da formação tem danos?'),
    (2,  'Correia desaeradora tem danos?'),
    (3,  'Correia do fiber bin tem danos?'),
    (4,  'Tem mangotes de exaustão furados ou em más condições?'),
    (5,  'Correia de compressão da pré-prensa tem danos?'),
    (6,  'Escova de limpeza inferior da pré-prensa está funcionando?'),
    (7,  'Existe vazamento de fibra em algum ponto específico?'),
    (8,  'Rolos da cabeça de formação tem ruídos?'),
    (9,  'Sistema de spray apresenta alguma irregularidade?'),
    (10, 'Grades de proteção estão em boas condições?'),
    (11, 'Portões estão com identificações corretas?'),
    (12, 'Todos os portões estão com dispositivos de bloqueios no local?'),
    (13, 'Batimento das mangas estão corretos? Pressão do sistema está correto?'),
    (14, 'Portas de inspeção do filtro de mangas, ciclones, tubulações e exaustores estão sem vazamento?'),
    (15, 'Algum bico dos sprays apresentou anomalia na dosagem?')
) as x(ordem, pergunta)
where t.codigo = 'FRCDM2003.r02'
on conflict (template_id, ordem) do nothing;

insert into checklist_template_horarios (template_id, turno_id, horario, ordem)
select t.id, x.turno_id, x.horario, x.ordem
from checklist_templates t
cross join (values
    (3, time '23:00', 1), (3, time '01:30', 2), (3, time '04:00', 3),   -- Noite
    (1, time '07:00', 1), (1, time '09:30', 2), (1, time '12:00', 3),   -- Manhã
    (2, time '15:00', 1), (2, time '17:30', 2), (2, time '20:00', 3)    -- Tarde
) as x(turno_id, horario, ordem)
where t.codigo = 'FRCDM2003.r02'
on conflict (template_id, turno_id, horario) do nothing;
