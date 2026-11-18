-- SDCV do ERP (importados por CSV): materiais (CM) e serviços CNAE (FTS)
create table if not exists sdcv (
  id text primary key,                 -- ex.: 123433/26
  item text, descricao text, comprador text, tipo text, tipo_compra text,
  cc text, categoria text, qtd numeric, erp text,
  abertura date, triagem date, previsao date, ult_mov timestamp,
  status text, tempo int,
  ss text, ss_man boolean not null default false,   -- SS/OM (extraída da OS do texto; ss_man=true quando ajustada à mão)
  kind text check (kind in ('M','S')),               -- M material · S serviço (CNAE)
  cnae text, disc smallint check (disc is null or disc between 0 and 3),
  solic_real text, ref date,                          -- ref = posição do ERP no arquivo
  aprovador text, tipo_apr text, dt_envio date, dias_parado int, aprov2 text,
  ativo boolean not null default true,
  updated_at timestamptz not null default now()
);
create index if not exists sdcv_ss on sdcv(ss);
create index if not exists sdcv_kind on sdcv(kind, ativo);
alter table sdcv enable row level security;
drop policy if exists sd_sel on sdcv; create policy sd_sel on sdcv for select to authenticated using (usuario_ativo());
drop policy if exists sd_all on sdcv; create policy sd_all on sdcv for all to authenticated using (eh_master()) with check (eh_master());
