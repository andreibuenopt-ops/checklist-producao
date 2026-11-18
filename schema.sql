-- ===== CONTROLE DE COMPRAS / FTS — schema =====
create table if not exists areas (nome text primary key, dono text not null default '');
create table if not exists ferramentas (cod text primary key, qtd int, descricao text not null);
create table if not exists materiais (cod text primary key, descricao text not null, un text, estoque numeric default 0, disc smallint check (disc in (0,1))); -- 0=elétrica 1=mecânica

create table if not exists fts (
  id text primary key, ss text unique not null, titulo text, linha text, area_texto text,
  data_prog text, disc smallint check (disc in (0,1)), area_op text references areas(nome),
  atividades jsonb default '[]', ferramentas jsonb default '[]', dados jsonb default '{}',
  sdcv jsonb default '{}', criado_em timestamptz default now());

create table if not exists cm (
  id text primary key, linha text not null, tipo smallint not null check (tipo in (0,1,2)), -- 0=PS 1=PM 2=PA
  mes smallint, semana smallint, ano smallint not null, status smallint not null default 0, obs text,
  sdcv jsonb default '{}', hist jsonb default '[]', criado_em timestamptz default now());
create table if not exists cm_itens (
  id bigserial primary key, cm_id text not null references cm(id) on delete cascade,
  ss text not null, item text references materiais(cod), descricao text, un text, qtd numeric not null,
  area text references areas(nome), disc smallint check (disc in (0,1)));

create table if not exists ce (
  id text primary key, ss text not null, item text not null, descricao text not null, defeito text,
  area text references areas(nome), disc smallint check (disc in (0,1)),
  linha text, tipo smallint, mes smallint, semana smallint, ano smallint,
  fornecedor text, nf_envio text, nf_retorno text, dt_envio date, dt_prev date, dt_ret date, valor numeric,
  status smallint not null default 0, obs text, sdcv jsonb default '{}', hist jsonb default '[]', criado_em timestamptz default now());

create index if not exists cm_itens_ss on cm_itens(ss); create index if not exists cm_itens_item on cm_itens(item);
create index if not exists ce_ss on ce(ss);

-- RLS: só usuários logados (Supabase Auth) acessam
do $$ declare t text; begin
 foreach t in array array['areas','ferramentas','materiais','fts','cm','cm_itens','ce'] loop
  execute format('alter table %I enable row level security',t);
  execute format('drop policy if exists "auth_all" on %I',t);
  execute format('create policy "auth_all" on %I for all to authenticated using (true) with check (true)',t);
  execute format('grant select,insert,update,delete on %I to authenticated',t);
 end loop; end $$;
grant usage,select on all sequences in schema public to authenticated;

insert into areas(nome) values ('PÁTIO'),('REFINADOR'),('PRENSA'),('ACABAMENTO') on conflict do nothing;

-- catálogo inicial (ilustrativo; trocar pelos códigos do ERP)
insert into ferramentas(cod,qtd,descricao) values
('FER-001',1,'ALICATE BOMBA D''ÁGUA 10"'),
('FER-002',1,'ALICATE DE PRESSÃO 10"'),
('FER-003',1,'ALICATE RETO P/ ANEL EXTERNO 7"'),
('FER-004',1,'ALICATE CURVO P/ ANEL EXTERNO 7"'),
('FER-005',1,'ALICATE RETO P/ ANEL INTERNO 7"'),
('FER-006',1,'ALICATE CURVO P/ ANEL INTERNO 7"'),
('FER-007',1,'ALICATE UNIVERSAL 8"'),
('FER-008',1,'ARCO DE SERRA 12"'),
('FER-009',1,'BROCAS 1,0 - 13,0 MM 25 PÇS'),
('FER-010',1,'CAIXA DE FERRAMENTAS 7 GAVETAS'),
('FER-011',1,'CALIBRE DE FOLGA 0,05 - 1,0 MM'),
('FER-012',1,'CALIBRE DE FOLGA 0,03 - 0,3 MM'),
('FER-013',1,'CALIBRE DE ROSCAS 52L'),
('FER-014',1,'CHAVE AJUSTÁVEL 6"'),
('FER-015',1,'CHAVE AJUSTÁVEL 8"'),
('FER-016',1,'CHAVE ALLEN 12 MM'),
('FER-017',1,'CHAVE ALLEN 14 MM'),
('FER-018',1,'CHAVE ALLEN 16 MM'),
('FER-019',1,'CHAVE ALLEN 17 MM'),
('FER-020',1,'CHAVE ALLEN 19 MM'),
('FER-021',1,'CHAVE ALLEN 22 MM'),
('FER-022',1,'CHAVE ALLEN LONGA CABEÇA REDONDA 1,5 - 10 MM'),
('FER-023',1,'CHAVE DE BOCA FIXA 6 - 7 MM'),
('FER-024',1,'CHAVE DE BOCA FIXA 8 - 9 MM'),
('FER-025',1,'CHAVE DE BOCA FIXA 10 - 11 MM'),
('FER-026',1,'CHAVE DE BOCA FIXA 12 - 13 MM'),
('FER-027',1,'CHAVE DE BOCA FIXA 14 - 15 MM'),
('FER-028',1,'CHAVE DE BOCA FIXA 16 - 17 MM'),
('FER-029',1,'CHAVE DE BOCA FIXA 18 - 19 MM'),
('FER-030',1,'CHAVE DE BOCA FIXA 20 - 22 MM'),
('FER-031',1,'CHAVE DE BOCA FIXA 21 - 23 MM'),
('FER-032',1,'CHAVE DE BOCA FIXA 24 - 26 MM'),
('FER-033',1,'CHAVE DE BOCA FIXA 25 - 28 MM'),
('FER-034',1,'CHAVE DE BOCA FIXA 27 - 32 MM'),
('FER-035',1,'CHAVE COMBINADA 6 MM'),
('FER-036',1,'CHAVE COMBINADA 7 MM'),
('FER-037',1,'CHAVE COMBINADA 8 MM'),
('FER-038',1,'CHAVE COMBINADA 9 MM'),
('FER-039',1,'CHAVE COMBINADA 10 MM'),
('FER-040',1,'CHAVE COMBINADA 11 MM'),
('FER-041',1,'CHAVE COMBINADA 12 MM'),
('FER-042',1,'CHAVE COMBINADA 13 MM'),
('FER-043',1,'CHAVE COMBINADA 14 MM'),
('FER-044',1,'CHAVE COMBINADA 17 MM'),
('FER-045',1,'CHAVE COMBINADA 18 MM'),
('FER-046',1,'CHAVE COMBINADA 19 MM'),
('FER-047',1,'CHAVE COMBINADA 22 MM'),
('FER-048',1,'CHAVE COMBINADA 24 MM'),
('FER-049',1,'CHAVE COMBINADA 27 MM'),
('FER-050',1,'CHAVE COMBINADA 30 MM'),
('FER-051',1,'CHAVE COMBINADA 32 MM'),
('FER-052',1,'CHAVE DE FENDA 3 X 100 MM'),
('FER-053',1,'CHAVE DE FENDA 6 X 150 MM'),
('FER-054',1,'CHAVE DE FENDA 8 X 200 MM'),
('FER-055',1,'CHAVE PHILIPS 4 X 100 MM'),
('FER-056',1,'CHAVE PHILIPS 6 X 150 MM'),
('FER-057',1,'CHAVE BIELA 8 MM'),
('FER-058',1,'CHAVE BIELA 10 MM'),
('FER-059',1,'CHAVE BIELA 13 MM'),
('FER-060',1,'CHAVE BIELA 17 MM'),
('FER-061',1,'CHAVE BIELA 19 MM'),
('FER-062',1,'ESPÁTULA 500 MM X 19 MM'),
('FER-063',1,'MARTELO BOLA 500 GR'),
('FER-064',1,'MARTELO POLIURETANO 350 GR'),
('FER-065',1,'MARRETA 1,5 KG'),
('FER-066',1,'PAQUÍMETRO 150 MM'),
('FER-067',1,'PUNÇÃO DE CENTRO 4 X 120 MM'),
('FER-068',1,'SACA PINO PARALELO 2,5 X 150 MM'),
('FER-069',1,'SACA PINO PARALELO 3,0 X 150 MM'),
('FER-070',1,'SACA PINO PARALELO 4,0 X 150 MM'),
('FER-071',1,'SACA PINO PARALELO 5,0 X 150 MM'),
('FER-072',1,'SACA PINO PARALELO 6,0 X 150 MM'),
('FER-073',1,'SACA PINO PARALELO 8,0 X 150 MM'),
('FER-074',1,'TALHADEIRA SEXTAVADA 19 X 200 MM')
on conflict do nothing;
insert into materiais(cod,descricao,un,estoque,disc) values
('MAT-00101','ALETA P/ VÁLVULA ROTATIVA DO SIFTER','PÇ',0,1),
('MAT-00102','MOTORREDUTOR (CONFORME PLACA DO EQUIPAMENTO)','PÇ',0,1),
('MAT-00103','CORRENTE DE ROLOS P/ ACIONAMENTO','M',12,1),
('MAT-00104','ELO DE EMENDA P/ CORRENTE DE ROLOS','PÇ',20,1),
('MAT-00105','CORREIA EM V PERFIL B','PÇ',8,1),
('MAT-00106','ROLAMENTO P/ MANCAL','PÇ',4,1),
('MAT-00107','GRAXA P/ MANCAIS - BALDE 18 KG','BD',3,1),
('MAT-00108','ÓLEO LUBRIFICANTE P/ REDUTOR','L',200,1),
('MAT-00109','PARAFUSO SEXTAVADO M12 X 50 CL 8.8','PÇ',300,1),
('MAT-00110','PORCA SEXTAVADA M12','PÇ',400,1),
('MAT-00111','ARRUELA LISA M12','PÇ',500,1),
('MAT-00112','CHAVETA PARALELA','PÇ',15,1),
('MAT-00113','ESTOPA / PANO INDUSTRIAL','KG',30,1),
('MAT-00114','DESENGRIPANTE SPRAY 300 ML','UN',24,1),
('MAT-00115','CADEADO DE BLOQUEIO (LOTO)','PÇ',10,1),
('MAT-00116','CONTATOR TRIPOLAR 25 A','PÇ',3,0),
('MAT-00117','SENSOR INDUTIVO M18','PÇ',5,0),
('MAT-00118','CABO FLEXÍVEL 2,5 MM²','M',200,0),
('MAT-00119','DISJUNTOR-MOTOR','PÇ',2,0)
on conflict do nothing;
