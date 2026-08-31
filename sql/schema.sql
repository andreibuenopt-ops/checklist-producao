-- =====================================================================
-- Checklist de Produção MDF — schema Supabase (Postgres) — v3 FINAL
-- Rodar inteiro, uma única vez, no SQL Editor de um projeto Supabase novo.
-- Idempotente: pode ser reaplicado sem duplicar dados.
-- =====================================================================

create extension if not exists pgcrypto;

-- Função utilitária usada por vários triggers "atualizado_em" ao longo
-- do arquivo — definida aqui no topo, antes de qualquer tabela, porque
-- a tabela configuracoes_sistema (logo abaixo) já usa ela num trigger.
-- (Bug real encontrado rodando o schema do zero contra um Postgres
-- limpo: antes essa função só era criada depois da tabela usuarios,
-- mais abaixo no arquivo — configuracoes_sistema falhava em banco novo.)
create or replace function set_atualizado_em()
returns trigger as $$
begin
    new.atualizado_em = now();
    return new;
end;
$$ language plpgsql;

-- ---------------------------------------------------------------------
-- GRANT no schema public para os roles anon/authenticated.
-- Necessário porque em alguns projetos Supabase os default privileges
-- do schema public não vêm pré-configurados para tabelas criadas via
-- SQL Editor (diferente de tabelas criadas pela Table Editor UI). Sem
-- isso, mesmo com RLS permissivo, o Postgres nega antes de a policy
-- ser avaliada: "permission denied for table X (42501)". Roda sempre,
-- de forma idempotente — sem custo mesmo se já estiver configurado.
-- Para tabelas futuras (criadas depois deste script), o "alter default
-- privileges" garante que o GRANT se aplica automaticamente.
-- ---------------------------------------------------------------------
grant usage on schema public to anon, authenticated;
alter default privileges in schema public
    grant select, insert, update, delete on tables to anon, authenticated;
-- Cobre também tabelas já existentes (reaplicação em banco já criado):
grant select, insert, update, delete on all tables in schema public to anon, authenticated;

-- Mesma classe de proteção para o schema storage (usado pela logo abaixo) —
-- evita repetir o mesmo "permission denied" já visto no schema public.
grant usage on schema storage to anon, authenticated;
grant select, insert, update, delete on storage.objects to anon, authenticated;
grant select on storage.buckets to anon, authenticated;

-- ---------------------------------------------------------------------
-- CONFIGURAÇÕES DO SISTEMA — linha única (singleton): logo da empresa e
-- cor principal do tema, exibidas no menu lateral e nos QR Codes.
-- Editável em Administração → Identidade Visual. Arquivo da logo fica no
-- Storage (bucket público "logos"), só a URL/caminho ficam nesta tabela.
-- ---------------------------------------------------------------------
create table if not exists configuracoes_sistema (
    id                          smallint primary key default 1,
    logo_path                   text,
    logo_url                    text,
    cor_primaria                text not null default '#667f38', -- verde Guararapes
    autocadastro_requer_aprovacao boolean not null default false,
    atualizado_em               timestamptz not null default now(),
    check (id = 1)
);

-- Cobre quem já rodou uma versão anterior do schema sem estas colunas:
alter table configuracoes_sistema add column if not exists cor_primaria text not null default '#667f38';
alter table configuracoes_sistema add column if not exists autocadastro_requer_aprovacao boolean not null default false;

insert into configuracoes_sistema (id) values (1) on conflict (id) do nothing;

drop trigger if exists trg_config_atualizado_em on configuracoes_sistema;
create trigger trg_config_atualizado_em
    before update on configuracoes_sistema
    for each row execute function set_atualizado_em();

insert into storage.buckets (id, name, public)
values ('logos', 'logos', true)
on conflict (id) do nothing;

drop policy if exists "app_full_access_logos" on storage.objects;
create policy "app_full_access_logos" on storage.objects
    for all using (bucket_id = 'logos') with check (bucket_id = 'logos');

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
-- ANÁLISE 5 PORQUÊS (RCA) — "FORMULÁRIO 5 PORQUÊS – PARADA DE LINHA"
-- Estrutura definitiva, espelhando o formulário físico da Guararapes.
-- Substitui a versão provisória anterior (drop + recreate: tabela nova,
-- sem uso em produção ainda, então é seguro recriar do zero).
-- Regra do formulário: preencher para paradas entre 30min e 1h30min
-- (validado só como aviso na UI, não trava o registro).
-- ---------------------------------------------------------------------
drop table if exists analise_5_porques_acoes cascade;
drop table if exists analises_5_porques cascade;

create table analises_5_porques (
    id                     uuid primary key default gen_random_uuid(),

    -- Origem opcional: se a análise nasceu de um "Não" de item crítico
    -- no checklist (fluxo automático). Pode ficar em branco — o
    -- formulário físico também é preenchido de forma avulsa.
    checklist_resposta_id  uuid references checklist_respostas(id),
    template_id            uuid references checklist_templates(id),

    -- Cabeçalho do formulário
    data_parada            date not null default current_date,
    equipamento            text not null,
    setor                  text not null,
    responsavel_id         uuid references usuarios(id),
    tempo_parada_minutos   integer,

    -- Descrição do problema + tabela dos 5 porquês
    descricao_problema     text not null,
    problema               text,
    porque_1               text,
    porque_2               text,
    porque_3               text,
    porque_4               text,
    porque_5               text,
    causa_raiz             text,

    -- Verificação da eficácia (Coordenador de produção)
    eficaz                 boolean,
    verificado_por         uuid references usuarios(id),
    verificado_em          timestamptz,
    evidencias             text,

    status                 text not null default 'aberta'
                           check (status in ('aberta', 'em_andamento', 'concluida')),
    criado_por             uuid not null references usuarios(id),
    criado_em              timestamptz not null default now(),
    atualizado_em          timestamptz not null default now()
);

-- Plano de Ação — tabela "Ação Corretiva | Responsável | Prazo" do
-- formulário, com múltiplas linhas (o papel tem 5 linhas em branco).
create table analise_5_porques_acoes (
    id              uuid primary key default gen_random_uuid(),
    analise_id      uuid not null references analises_5_porques(id) on delete cascade,
    ordem           smallint not null default 1,
    acao_corretiva  text not null,
    responsavel     text,
    prazo           date,
    concluida       boolean not null default false
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
create index if not exists idx_5porques_status                 on analises_5_porques (status);
create index if not exists idx_5porques_data                   on analises_5_porques (data_parada);
create index if not exists idx_5porques_acoes_analise           on analise_5_porques_acoes (analise_id);

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
-- LOGIN SEM EXPOR O HASH DA SENHA
-- Verifica a senha DENTRO do Postgres (pgcrypto) e devolve só um
-- boolean — o hash bcrypt nunca trafega até o app/navegador. Antes,
-- o app buscava a linha inteira (select "*") e comparava em Python;
-- com a chave publishable, qualquer um podia pedir "senha_hash" direto
-- pela API sem nem passar pelo app. Essa função fecha isso.
--
-- security definer: roda com o dono da função (acesso total à tabela),
-- não com o papel de quem chama (anon) — por isso funciona mesmo depois
-- do REVOKE de senha_hash logo abaixo.
--
-- Normaliza o prefixo do hash ($2b$/$2y$ -> $2a$) antes de comparar:
-- testado à mão com Postgres 16 + pgcrypto — essa build só reconhece
-- $2a$, e o bcrypt do Python sempre gera $2b$. $2a$/$2b$ são o mesmo
-- algoritmo (a diferença não afeta verificação de senha normal), então
-- normalizar não enfraquece nada — só evita depender de uma versão
-- específica de pgcrypto reconhecer $2b$.
--
-- search_path inclui "extensions": no Supabase (diferente de um Postgres
-- comum), o pgcrypto é instalado no schema "extensions", não em "public".
-- Erro real visto em produção sem isso: "function crypt(text, text) does
-- not exist" — reproduzido e corrigido testando local com a extensão
-- instalada em "extensions" de propósito, igual o Supabase faz.
-- =====================================================================
create or replace function autenticar_usuario(p_identificador text, p_senha text)
returns table (
    id                uuid,
    nome              text,
    email             text,
    matricula         text,
    papel             text,
    ativo             boolean,
    senha_temporaria  boolean,
    senha_valida      boolean
)
language plpgsql
security definer
set search_path = public, extensions
as $$
begin
    return query
    select
        u.id, u.nome, u.email, u.matricula, u.papel, u.ativo, u.senha_temporaria,
        (
            regexp_replace(u.senha_hash, '^\$2[by]\$', '$2a$')
            = crypt(p_senha, regexp_replace(u.senha_hash, '^\$2[by]\$', '$2a$'))
        ) as senha_valida
    from usuarios u
    where u.email = p_identificador or u.matricula = p_identificador
    limit 1;
end;
$$;

grant execute on function autenticar_usuario(text, text) to anon, authenticated;

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
alter table analise_5_porques_acoes enable row level security;
alter table configuracoes_sistema enable row level security;

drop policy if exists "app_full_access" on usuarios;
create policy "app_full_access" on usuarios for all using (true) with check (true);

-- Remove leitura direta do hash de senha via API — só a função
-- autenticar_usuario() (security definer, acima) consegue ler essa
-- coluna. INSERT/UPDATE continuam liberados (é preciso GRAVAR o hash
-- ao criar usuário/resetar senha), só a LEITURA fica restrita.
revoke select on usuarios from anon, authenticated;
grant select (id, nome, email, matricula, papel, ativo, senha_temporaria, criado_por, criado_em, atualizado_em)
    on usuarios to anon, authenticated;
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
drop policy if exists "app_full_access" on analise_5_porques_acoes;
create policy "app_full_access" on analise_5_porques_acoes for all using (true) with check (true);
drop policy if exists "app_full_access" on configuracoes_sistema;
create policy "app_full_access" on configuracoes_sistema for all using (true) with check (true);

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
