-- =====================================================================
-- Checklist de Produção MDF — schema Supabase (Postgres) — v3 FINAL
-- Rodar inteiro, uma única vez, no SQL Editor de um projeto Supabase novo.
-- Idempotente: pode ser reaplicado sem duplicar dados.
-- =====================================================================

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------
-- USUÁRIOS
-- Níveis de acesso:
--   master       -> ajuste de sistema, cadastra usuários, cria checklists,
--                   aprova/rejeita sugestões, reseta senha
--   coordenacao  -> visualiza tudo (todas as áreas), sem exportar dashboard
--   supervisor   -> assina checklist, visualiza e EXPORTA dashboard, gera QR
--   producao     -> preenche checklist
-- ---------------------------------------------------------------------
create table if not exists usuarios (
    id                uuid primary key default gen_random_uuid(),
    nome              text not null,
    email             text not null unique,
    matricula         text not null unique,
    senha_hash        text not null,
    papel             text not null default 'producao'
                      check (papel in ('producao', 'supervisor', 'coordenacao', 'master')),
    ativo             boolean not null default true,
    senha_temporaria  boolean not null default false,
    criado_por        uuid references usuarios(id),
    criado_em         timestamptz not null default now(),
    atualizado_em     timestamptz not null default now()
);

create index if not exists idx_usuarios_papel on usuarios (papel);
create index if not exists idx_usuarios_ativo on usuarios (ativo);

create or replace function set_atualizado_em()
returns trigger as $$
begin
    new.atualizado_em = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists trg_usuarios_atualizado_em on usuarios;
create trigger trg_usuarios_atualizado_em
    before update on usuarios
    for each row execute function set_atualizado_em();

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
-- SETORES DE PROCESSO — as 9 macro-áreas fixas da planta
-- ---------------------------------------------------------------------
create table if not exists setores_processo (
    id      smallint primary key,
    nome    text not null unique,
    ordem   smallint not null unique
);

insert into setores_processo (id, nome, ordem) values
    (1, 'Pátio de Madeira e Preparação', 1),
    (2, 'Silo de Cavaco', 2),
    (3, 'Planta Térmica', 3),
    (4, 'Refinador (Desfibrador)', 4),
    (5, 'Linha de Formação e Pré-prensa', 5),
    (6, 'Prensa Contínua', 6),
    (7, 'Saída e Arrefecedor de Chapas', 7),
    (8, 'Sistema de Gripper e Movimentação', 8),
    (9, 'Linha de Acabamento', 9)
on conflict (id) do nothing;

-- ---------------------------------------------------------------------
-- EQUIPAMENTOS — catálogo de áreas/equipamentos específicos dentro de
-- cada setor (ex.: setor "Silo de Cavaco" -> Descascador, Esteira de
-- Cavaco, Picador, Esteira Silo 1...). Vazio por padrão: o master
-- popula e mantém essa lista pela tela de Administração, sem precisar
-- de SQL. Usado como campo "área" do checklist na criação.
-- ---------------------------------------------------------------------
create table if not exists equipamentos (
    id        uuid primary key default gen_random_uuid(),
    setor_id  smallint not null references setores_processo(id),
    nome      text not null,
    ordem     smallint not null default 1,
    ativo     boolean not null default true,
    unique (setor_id, nome)
);

create index if not exists idx_equipamentos_setor on equipamentos (setor_id);

-- ---------------------------------------------------------------------
-- MODELOS DE CHECKLIST — o master cria/edita livremente pela tela de Administração
-- ---------------------------------------------------------------------
create table if not exists checklist_templates (
    id              uuid primary key default gen_random_uuid(),
    codigo          text not null unique,
    titulo          text not null,
    area            text not null,
    slug            text not null unique,
    revisao         text,
    observacao      text,
    setor_id        smallint references setores_processo(id),
    equipamento_id  uuid references equipamentos(id),
    ordem_processo  smallint not null default 999,
    ativo           boolean not null default true,
    criado_em       timestamptz not null default now()
);

create index if not exists idx_templates_equipamento on checklist_templates (equipamento_id);

create table if not exists checklist_template_itens (
    id            uuid primary key default gen_random_uuid(),
    template_id   uuid not null references checklist_templates(id) on delete cascade,
    ordem         smallint not null,
    pergunta      text not null,
    criticidade   text not null default 'media'
                  check (criticidade in ('critica', 'alta', 'media')),
    unique (template_id, ordem)
);

-- Horário de verificação por turno — um horário fixo por turno, definido pelo master
create table if not exists checklist_template_horarios (
    id            uuid primary key default gen_random_uuid(),
    template_id   uuid not null references checklist_templates(id) on delete cascade,
    turno_id      smallint not null references turnos(id),
    horario       time not null,
    ordem         smallint not null default 1,
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

drop trigger if exists trg_checklists_atualizado_em on checklists;
create trigger trg_checklists_atualizado_em
    before update on checklists
    for each row execute function set_atualizado_em();

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

-- ---------------------------------------------------------------------
-- SUGESTÕES DE ITENS — qualquer usuário sugere, master aprova/rejeita
-- ---------------------------------------------------------------------
create table if not exists checklist_sugestoes (
    id                    uuid primary key default gen_random_uuid(),
    template_id           uuid not null references checklist_templates(id) on delete cascade,
    sugerido_por          uuid not null references usuarios(id),
    pergunta_sugerida     text not null,
    justificativa         text not null,
    criticidade_sugerida  text not null default 'media'
                          check (criticidade_sugerida in ('critica', 'alta', 'media')),
    status                text not null default 'pendente'
                          check (status in ('pendente', 'aprovada', 'rejeitada')),
    item_id               uuid references checklist_template_itens(id),
    analisado_por         uuid references usuarios(id),
    analisado_em          timestamptz,
    motivo_rejeicao       text,
    criado_em             timestamptz not null default now()
);

-- ---------------------------------------------------------------------
-- ANÁLISE 5 PORQUÊS (RCA) — ESTRUTURA PROVISÓRIA
-- Aba solicitada para ser criada agora; especificação final ainda será
-- enviada. Campos padrão de RCA (5 whys) vinculados a uma resposta "Não"
-- de item crítico. Ajustar/estender quando a spec definitiva chegar —
-- nenhuma outra tabela depende desta.
-- ---------------------------------------------------------------------
create table if not exists analises_5_porques (
    id                      uuid primary key default gen_random_uuid(),
    checklist_resposta_id   uuid references checklist_respostas(id),
    template_id             uuid references checklist_templates(id),
    problema                text not null,
    porque_1                text,
    porque_2                text,
    porque_3                text,
    porque_4                text,
    porque_5                text,
    causa_raiz              text,
    acao_corretiva          text,
    responsavel_id          uuid references usuarios(id),
    prazo                   date,
    status                  text not null default 'aberta'
                            check (status in ('aberta', 'em_andamento', 'concluida')),
    criado_por              uuid not null references usuarios(id),
    criado_em               timestamptz not null default now(),
    atualizado_em           timestamptz not null default now()
);

drop trigger if exists trg_5porques_atualizado_em on analises_5_porques;
create trigger trg_5porques_atualizado_em
    before update on analises_5_porques
    for each row execute function set_atualizado_em();

-- ---------------------------------------------------------------------
-- ÍNDICES — dashboard e agregações
-- ---------------------------------------------------------------------
create index if not exists idx_checklists_data              on checklists (data);
create index if not exists idx_checklists_template_data      on checklists (template_id, data);
create index if not exists idx_checklists_status             on checklists (status);
create index if not exists idx_respostas_checklist           on checklist_respostas (checklist_id);
create index if not exists idx_respostas_checklist_resposta  on checklist_respostas (checklist_id, resposta);
create index if not exists idx_respostas_resposta_nao        on checklist_respostas (resposta) where resposta = 'Não';
create index if not exists idx_templates_setor               on checklist_templates (setor_id);
create index if not exists idx_templates_ativo_ordem         on checklist_templates (ativo, ordem_processo);
create index if not exists idx_itens_criticidade             on checklist_template_itens (criticidade);
create index if not exists idx_sugestoes_status               on checklist_sugestoes (status);
create index if not exists idx_sugestoes_template              on checklist_sugestoes (template_id);
create index if not exists idx_5porques_status                on analises_5_porques (status);

-- ---------------------------------------------------------------------
-- VIEWS auxiliares (uso futuro em BI/relatórios; não consumidas pelo app)
-- ---------------------------------------------------------------------
create or replace view vw_checklists_status as
select
    c.*,
    ct.titulo, ct.area, ct.codigo, ct.setor_id, ct.ordem_processo,
    sp.nome as setor_nome,
    t.nome  as turno_nome
from checklists c
join checklist_templates ct on ct.id = c.template_id
join turnos t on t.id = c.turno_id
left join setores_processo sp on sp.id = ct.setor_id;

create or replace view vw_dashboard_respostas as
select
    cr.id as resposta_id, cr.checklist_id, cr.resposta, cr.respondido_em,
    cti.pergunta, cti.criticidade,
    c.data, c.turno_id, c.status as checklist_status,
    ct.id as template_id, ct.titulo, ct.area, ct.setor_id, ct.ordem_processo,
    sp.nome as setor_nome
from checklist_respostas cr
join checklist_template_itens cti on cti.id = cr.item_id
join checklists c on c.id = cr.checklist_id
join checklist_templates ct on ct.id = c.template_id
left join setores_processo sp on sp.id = ct.setor_id;

-- =====================================================================
-- RLS
-- O app (Streamlit) roda inteiramente no servidor: a chave do Supabase
-- fica em st.secrets e nunca chega ao navegador do usuário. O controle
-- de acesso real (quem loga, quem faz o quê) é feito pelo próprio app.
-- =====================================================================
alter table usuarios enable row level security;
alter table turnos enable row level security;
alter table setores_processo enable row level security;
alter table equipamentos enable row level security;
alter table checklist_templates enable row level security;
alter table checklist_template_itens enable row level security;
alter table checklist_template_horarios enable row level security;
alter table checklists enable row level security;
alter table checklist_respostas enable row level security;
alter table checklist_sugestoes enable row level security;
alter table analises_5_porques enable row level security;

drop policy if exists "app_full_access" on usuarios;
create policy "app_full_access" on usuarios for all using (true) with check (true);
drop policy if exists "app_full_access" on turnos;
create policy "app_full_access" on turnos for all using (true) with check (true);
drop policy if exists "app_full_access" on setores_processo;
create policy "app_full_access" on setores_processo for all using (true) with check (true);
drop policy if exists "app_full_access" on equipamentos;
create policy "app_full_access" on equipamentos for all using (true) with check (true);
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
drop policy if exists "app_full_access" on checklist_sugestoes;
create policy "app_full_access" on checklist_sugestoes for all using (true) with check (true);
drop policy if exists "app_full_access" on analises_5_porques;
create policy "app_full_access" on analises_5_porques for all using (true) with check (true);

-- =====================================================================
-- SEED — Template 1: Sifter e Ventiladores Externos
-- =====================================================================
insert into checklist_templates (codigo, titulo, area, slug, revisao, observacao, setor_id, ordem_processo) values
('FRCDM2011.r02', 'Checklist de inspeções - Sifter', 'Sifter e Ventiladores Externos', 'sifter', 'r02',
 'Obs.: toda resposta Não exige comentário sobre a situação, resolução ou pendência.', 3, 35)
on conflict (codigo) do nothing;

insert into checklist_template_itens (template_id, ordem, pergunta, criticidade)
select t.id, x.ordem, x.pergunta, x.criticidade
from checklist_templates t cross join (values
    (1, 'Existe vazamento de fibra em algum ponto específico do prédio?', 'media'),
    (2, 'Existe alguma porta de inspeção danificada ou acrilico quebrado?', 'media'),
    (3, 'Existe algum vazamento de ar nos cilindros de acionamentos dos flaps existentes no processo do Sifter?', 'alta'),
    (4, 'Ferramentas armazenadas no local adequado?', 'media'),
    (5, 'Realizado purga no cavalete de vapor dos radiadores de aquecimento do prédio?', 'media'),
    (6, 'Verificar se tem água nos drenos do cavalete de inundação e manter fechado o mesmo.', 'media'),
    (7, 'Regulagem dos descartes estão apresentando que tipo de fibra?', 'media'),
    (8, 'Bunkers de rejeito foram esvaziados?', 'media'),
    (9, 'Algum ruído nos ventiladores do sifter?', 'critica')
) as x(ordem, pergunta, criticidade)
where t.codigo = 'FRCDM2011.r02'
on conflict (template_id, ordem) do nothing;

insert into checklist_template_horarios (template_id, turno_id, horario, ordem)
select t.id, x.turno_id, x.horario, x.ordem
from checklist_templates t cross join (values
    (3, time '23:30', 1), (1, time '07:30', 1), (2, time '15:30', 1)
) as x(turno_id, horario, ordem)
where t.codigo = 'FRCDM2011.r02'
on conflict (template_id, turno_id, horario) do nothing;

-- =====================================================================
-- SEED — Template 2: Linha de Formação
-- =====================================================================
insert into checklist_templates (codigo, titulo, area, slug, revisao, observacao, setor_id, ordem_processo) values
('FRCDM2003.r02', 'Checklist de inspeções - Linha de Formação', 'Linha de Formação', 'linha-formacao', 'r02',
 'Obs.: toda resposta Não exige comentário sobre a situação, resolução ou pendência.', 5, 50)
on conflict (codigo) do nothing;

insert into checklist_template_itens (template_id, ordem, pergunta, criticidade)
select t.id, x.ordem, x.pergunta, x.criticidade
from checklist_templates t cross join (values
    (1,  'Correia da formação tem danos?', 'alta'),
    (2,  'Correia desaeradora tem danos?', 'media'),
    (3,  'Correia do fiber bin tem danos?', 'media'),
    (4,  'Tem mangotes de exaustão furados ou em más condições?', 'media'),
    (5,  'Correia de compressão da pré-prensa tem danos?', 'alta'),
    (6,  'Escova de limpeza inferior da pre-prensa está funcionando?', 'media'),
    (7,  'Existe vazamento de fibra em algum ponto específico?', 'media'),
    (8,  'Rolos da cabeça de formação tem ruídos?', 'alta'),
    (9,  'Sistema de spray apresenta alguma irregularidade?', 'media'),
    (10, 'Grades de proteção estão em boas condições?', 'media'),
    (11, 'Portões estão com identificações corretas?', 'media'),
    (12, 'Todos os portões estão com dispositivos de bloqueios no local?', 'media'),
    (13, 'Batimento das mangas estão corretos? Pressão do sistema está correto?', 'critica'),
    (14, 'Portas de inspeção do filtro de mangas, ciclones, tubulações e exaustores estão sem vazamento?', 'media'),
    (15, 'Algum bico dos sprays apresentou anomalia na dosagem?', 'media')
) as x(ordem, pergunta, criticidade)
where t.codigo = 'FRCDM2003.r02'
on conflict (template_id, ordem) do nothing;

insert into checklist_template_horarios (template_id, turno_id, horario, ordem)
select t.id, x.turno_id, x.horario, x.ordem
from checklist_templates t cross join (values
    (3, time '23:00', 1), (1, time '07:00', 1), (2, time '15:00', 1)
) as x(turno_id, horario, ordem)
where t.codigo = 'FRCDM2003.r02'
on conflict (template_id, turno_id, horario) do nothing;

-- =====================================================================
-- SEED — Template 3: Silo de Cavaco
-- =====================================================================
insert into checklist_templates (codigo, titulo, area, slug, revisao, observacao, setor_id, ordem_processo) values
('FRCDM2004.r01', 'Checklist de inspeções - Silo de Cavaco', 'Silo de Cavaco', 'silo-cavaco', 'r01',
 'Obs.: toda resposta Não exige comentário sobre a situação, resolução ou pendência.', 2, 20)
on conflict (codigo) do nothing;

insert into checklist_template_itens (template_id, ordem, pergunta, criticidade)
select t.id, x.ordem, x.pergunta, x.criticidade
from checklist_templates t cross join (values
    (1,  'Nível do silo dentro da faixa operacional mínima (evitar esvaziamento total / entrada de ar)?', 'critica'),
    (2,  'Existe formação de ponte ("rat hole") ou compactação de cavaco no silo?', 'alta'),
    (3,  'Rosca extratora de fundo apresenta ruído ou vibração anormal?', 'critica'),
    (4,  'Vazamento de óleo nos redutores das roscas dosadoras?', 'alta'),
    (5,  'Temperatura dos mancais das roscas dentro do limite (máx. 70°C)?', 'critica'),
    (6,  'Válvula rotativa de descarga sem folga excessiva ou cavaco preso?', 'alta'),
    (7,  'Sensor de nível (radar/ultrassônico) limpo e sem incrustação?', 'media'),
    (8,  'Comportas guilhotina operando livremente, sem cavaco compactado?', 'media'),
    (9,  'Sistema de aspersores de combate a incêndio testado e desobstruído?', 'critica'),
    (10, 'Detector de metais na entrada operacional (proteção do refinador)?', 'critica'),
    (11, 'Umidade do cavaco dentro da faixa especificada (35-45%)?', 'alta'),
    (12, 'Esteiras/transportadores de alimentação sem desalinhamento?', 'media')
) as x(ordem, pergunta, criticidade)
where t.codigo = 'FRCDM2004.r01'
on conflict (template_id, ordem) do nothing;

insert into checklist_template_horarios (template_id, turno_id, horario, ordem)
select t.id, x.turno_id, x.horario, x.ordem
from checklist_templates t cross join (values
    (3, time '23:30', 1), (1, time '07:30', 1), (2, time '15:30', 1)
) as x(turno_id, horario, ordem)
where t.codigo = 'FRCDM2004.r01'
on conflict (template_id, turno_id, horario) do nothing;

-- =====================================================================
-- SEED — Template 4: Planta Térmica
-- =====================================================================
insert into checklist_templates (codigo, titulo, area, slug, revisao, observacao, setor_id, ordem_processo) values
('FRCDM2005.r01', 'Checklist de inspeções - Planta Térmica', 'Planta Térmica', 'planta-termica', 'r01',
 'Obs.: toda resposta Não exige comentário sobre a situação, resolução ou pendência.', 3, 30)
on conflict (codigo) do nothing;

insert into checklist_template_itens (template_id, ordem, pergunta, criticidade)
select t.id, x.ordem, x.pergunta, x.criticidade
from checklist_templates t cross join (values
    (1,  'Temperatura de entrada do secador dentro do setpoint?', 'critica'),
    (2,  'Temperatura de saída do secador dentro do setpoint?', 'critica'),
    (3,  'Pressão negativa do sistema de exaustão dentro do range?', 'alta'),
    (4,  'Nível de combustível no silo do gerador térmico adequado?', 'critica'),
    (5,  'Temperatura da câmara de combustão da fornalha normal?', 'critica'),
    (6,  'Sistema de detecção de fagulhas (spark detector) na entrada do secador operacional?', 'critica'),
    (7,  'Válvulas/dampers de alívio de pressão desobstruídos?', 'critica'),
    (8,  'Umidade da fibra na saída do secador dentro da especificação?', 'alta'),
    (9,  'Vibração dos ventiladores principais de tiragem (ID fan) dentro do limite?', 'critica'),
    (10, 'Amperagem dos motores dos exaustores dentro da faixa nominal?', 'alta'),
    (11, 'Diferencial de pressão dos ciclones normal (sem obstrução)?', 'alta'),
    (12, 'Ausência de foco de fumaça/incêndio em dutos ou ciclones?', 'critica')
) as x(ordem, pergunta, criticidade)
where t.codigo = 'FRCDM2005.r01'
on conflict (template_id, ordem) do nothing;

insert into checklist_template_horarios (template_id, turno_id, horario, ordem)
select t.id, x.turno_id, x.horario, x.ordem
from checklist_templates t cross join (values
    (3, time '23:00', 1), (1, time '07:00', 1), (2, time '15:00', 1)
) as x(turno_id, horario, ordem)
where t.codigo = 'FRCDM2005.r01'
on conflict (template_id, turno_id, horario) do nothing;

-- =====================================================================
-- SEED — Template 5: Refinador
-- =====================================================================
insert into checklist_templates (codigo, titulo, area, slug, revisao, observacao, setor_id, ordem_processo) values
('FRCDM2006.r01', 'Checklist de inspeções - Refinador', 'Refinador (Desfibrador)', 'refinador', 'r01',
 'Obs.: toda resposta Não exige comentário sobre a situação, resolução ou pendência.', 4, 40)
on conflict (codigo) do nothing;

insert into checklist_template_itens (template_id, ordem, pergunta, criticidade)
select t.id, x.ordem, x.pergunta, x.criticidade
from checklist_templates t cross join (values
    (1,  'Pressão de vapor do pré-aquecedor/digestor dentro do setpoint (7-9 bar)?', 'critica'),
    (2,  'Temperatura do digestor/pré-aquecedor dentro do range?', 'critica'),
    (3,  'Pressão hidráulica do sistema de fechamento dos discos normal?', 'critica'),
    (4,  'Abertura entre discos (plate gap) dentro do programado?', 'critica'),
    (5,  'Vibração do motor principal do refinador dentro do limite (ISO 10816)?', 'critica'),
    (6,  'Temperatura dos mancais do eixo principal normal?', 'critica'),
    (7,  'Nível e pressão do óleo hidráulico de avanço dos discos adequados?', 'alta'),
    (8,  'Desgaste dos discos refinadores dentro da vida útil prevista?', 'alta'),
    (9,  'Corrente/amperagem do motor principal dentro da faixa nominal?', 'alta'),
    (10, 'Vazão e pressão de dosagem de resina/parafina na blow-line normais?', 'alta'),
    (11, 'Ausência de vazamento de vapor nas juntas/gaxetas?', 'media'),
    (12, 'Temperatura da blow-line pós-refinador dentro do range?', 'alta')
) as x(ordem, pergunta, criticidade)
where t.codigo = 'FRCDM2006.r01'
on conflict (template_id, ordem) do nothing;

insert into checklist_template_horarios (template_id, turno_id, horario, ordem)
select t.id, x.turno_id, x.horario, x.ordem
from checklist_templates t cross join (values
    (3, time '23:00', 1), (1, time '07:00', 1), (2, time '15:00', 1)
) as x(turno_id, horario, ordem)
where t.codigo = 'FRCDM2006.r01'
on conflict (template_id, turno_id, horario) do nothing;

-- =====================================================================
-- SEED — Template 6: Pré-Prensa
-- =====================================================================
insert into checklist_templates (codigo, titulo, area, slug, revisao, observacao, setor_id, ordem_processo) values
('FRCDM2007.r01', 'Checklist de inspeções - Pré-Prensa', 'Linha de Formação e Pré-prensa', 'pre-prensa', 'r01',
 'Obs.: toda resposta Não exige comentário sobre a situação, resolução ou pendência.', 5, 55)
on conflict (codigo) do nothing;

insert into checklist_template_itens (template_id, ordem, pergunta, criticidade)
select t.id, x.ordem, x.pergunta, x.criticidade
from checklist_templates t cross join (values
    (1, 'Correia de compressão sem cortes ou desalinhamento?', 'alta'),
    (2, 'Tensão da correia dentro do especificado?', 'alta'),
    (3, 'Escovas de limpeza (superior/inferior) em contato adequado?', 'media'),
    (4, 'Rolos compressores sem folga ou ruído anormal?', 'alta'),
    (5, 'Altura do colchão pré-comprimido dentro do padrão?', 'media'),
    (6, 'Alinhamento lateral do tapete de formação (sensor de borda) correto?', 'alta'),
    (7, 'Vazamento de fibra nas laterais dos rolos de compressão?', 'media')
) as x(ordem, pergunta, criticidade)
where t.codigo = 'FRCDM2007.r01'
on conflict (template_id, ordem) do nothing;

insert into checklist_template_horarios (template_id, turno_id, horario, ordem)
select t.id, x.turno_id, x.horario, x.ordem
from checklist_templates t cross join (values
    (3, time '23:30', 1), (1, time '07:30', 1), (2, time '15:30', 1)
) as x(turno_id, horario, ordem)
where t.codigo = 'FRCDM2007.r01'
on conflict (template_id, turno_id, horario) do nothing;

-- =====================================================================
-- SEED — Template 7: Prensa Contínua
-- =====================================================================
insert into checklist_templates (codigo, titulo, area, slug, revisao, observacao, setor_id, ordem_processo) values
('FRCDM2008.r01', 'Checklist de inspeções - Prensa Contínua', 'Prensa Contínua', 'prensa-continua', 'r01',
 'Obs.: toda resposta Não exige comentário sobre a situação, resolução ou pendência.', 6, 60)
on conflict (codigo) do nothing;

insert into checklist_template_itens (template_id, ordem, pergunta, criticidade)
select t.id, x.ordem, x.pergunta, x.criticidade
from checklist_templates t cross join (values
    (1,  'Temperatura dos pratos por zona dentro da faixa programada?', 'critica'),
    (2,  'Pressão específica aplicada por zona conforme diagrama de pressão?', 'critica'),
    (3,  'Velocidade da esteira de aço estável, sem oscilação?', 'critica'),
    (4,  'Nível do óleo hidráulico do sistema de fechamento adequado?', 'critica'),
    (5,  'Temperatura do óleo hidráulico dentro do limite?', 'critica'),
    (6,  'Corrente lateral (side chain) sem ruído/vibração anormal?', 'critica'),
    (7,  'Tensão e alinhamento da esteira de aço (tracking) corretos?', 'critica'),
    (8,  'Vazamento de óleo térmico nas conexões dos pratos?', 'critica'),
    (9,  'Pressão do óleo térmico no circuito de aquecimento normal?', 'critica'),
    (10, 'Desgaste dos roletes (roller bars) sob a esteira dentro do previsto?', 'alta'),
    (11, 'Temperatura de saída da chapa (núcleo, via IV) dentro do range?', 'alta'),
    (12, 'Amperagem dos motores de acionamento da esteira normal?', 'alta')
) as x(ordem, pergunta, criticidade)
where t.codigo = 'FRCDM2008.r01'
on conflict (template_id, ordem) do nothing;

insert into checklist_template_horarios (template_id, turno_id, horario, ordem)
select t.id, x.turno_id, x.horario, x.ordem
from checklist_templates t cross join (values
    (3, time '23:15', 1), (1, time '07:15', 1), (2, time '15:15', 1)
) as x(turno_id, horario, ordem)
where t.codigo = 'FRCDM2008.r01'
on conflict (template_id, turno_id, horario) do nothing;

-- =====================================================================
-- SEED — Template 8: Arrefecedor de Chapas e Gripper
-- =====================================================================
insert into checklist_templates (codigo, titulo, area, slug, revisao, observacao, setor_id, ordem_processo) values
('FRCDM2009.r01', 'Checklist de inspeções - Arrefecedor e Gripper', 'Saída, Arrefecedor de Chapas e Gripper', 'arrefecedor-gripper', 'r01',
 'Obs.: toda resposta Não exige comentário sobre a situação, resolução ou pendência.', 7, 70)
on conflict (codigo) do nothing;

insert into checklist_template_itens (template_id, ordem, pergunta, criticidade)
select t.id, x.ordem, x.pergunta, x.criticidade
from checklist_templates t cross join (values
    (1,  'Velocidade de rotação do star cooler sincronizada com a linha?', 'alta'),
    (2,  'Temperatura da chapa na entrada e saída do resfriador dentro do range?', 'alta'),
    (3,  'Folga entre braços do star cooler sem atrito/contato?', 'critica'),
    (4,  'Ruído ou vibração anormal no motor de acionamento do star cooler?', 'alta'),
    (5,  'Pressão pneumática de fixação das garras do gripper dentro do range?', 'critica'),
    (6,  'Desgaste das borrachas/insertos de fixação do gripper?', 'alta'),
    (7,  'Alinhamento e lubrificação do carro do gripper adequados?', 'alta'),
    (8,  'Sensores de posição/fim de curso do gripper calibrados?', 'alta'),
    (9,  'Empilhador (stacker) sem obstrução, sensores de pilha funcionando?', 'media'),
    (10, 'Corrente de transporte pós-cooler sem folga excessiva?', 'media')
) as x(ordem, pergunta, criticidade)
where t.codigo = 'FRCDM2009.r01'
on conflict (template_id, ordem) do nothing;

insert into checklist_template_horarios (template_id, turno_id, horario, ordem)
select t.id, x.turno_id, x.horario, x.ordem
from checklist_templates t cross join (values
    (3, time '00:30', 1), (1, time '08:30', 1), (2, time '16:30', 1)
) as x(turno_id, horario, ordem)
where t.codigo = 'FRCDM2009.r01'
on conflict (template_id, turno_id, horario) do nothing;

-- =====================================================================
-- SEED — Template 9: Linha de Acabamento
-- =====================================================================
insert into checklist_templates (codigo, titulo, area, slug, revisao, observacao, setor_id, ordem_processo) values
('FRCDM2010.r01', 'Checklist de inspeções - Linha de Acabamento', 'Linha de Acabamento (Lixadeiras e Esquadrejadeiras)', 'acabamento', 'r01',
 'Obs.: toda resposta Não exige comentário sobre a situação, resolução ou pendência.', 9, 90)
on conflict (codigo) do nothing;

insert into checklist_template_itens (template_id, ordem, pergunta, criticidade)
select t.id, x.ordem, x.pergunta, x.criticidade
from checklist_templates t cross join (values
    (1,  'Desgaste das lixas dentro da vida útil, sem rasgos?', 'alta'),
    (2,  'Pressão dos rolos de lixamento calibrada por cabeçote?', 'alta'),
    (3,  'Espessura de saída dentro da tolerância especificada?', 'critica'),
    (4,  'Sistema de exaustão de pó das lixadeiras sem obstrução?', 'critica'),
    (5,  'Amperagem dos motores dos cabeçotes de lixa dentro da faixa nominal?', 'alta'),
    (6,  'Alinhamento das serras da esquadrejadeira dentro da tolerância?', 'critica'),
    (7,  'Desgaste/afiação das serras circulares de corte adequados?', 'alta'),
    (8,  'Vácuo de fixação da chapa na esquadrejadeira dentro do range?', 'alta'),
    (9,  'Sistema de aspiração de pó/cavaco funcionando corretamente?', 'critica'),
    (10, 'Detector de faísca (spark detection) no duto de exaustão ativo?', 'critica')
) as x(ordem, pergunta, criticidade)
where t.codigo = 'FRCDM2010.r01'
on conflict (template_id, ordem) do nothing;

insert into checklist_template_horarios (template_id, turno_id, horario, ordem)
select t.id, x.turno_id, x.horario, x.ordem
from checklist_templates t cross join (values
    (3, time '01:00', 1), (1, time '09:00', 1), (2, time '17:00', 1)
) as x(turno_id, horario, ordem)
where t.codigo = 'FRCDM2010.r01'
on conflict (template_id, turno_id, horario) do nothing;
