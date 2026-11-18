-- CE: campos da planilha de consertos externos + novos status
do $$
begin
  if not exists (select 1 from information_schema.columns where table_name='ce' and column_name='ficha') then
    -- remapeia status antigos (0 AGUARD.ENVIO,1 ENVIADO,2 EM CONSERTO,3 RETORNADO,4 INSTALADO)
    -- para os novos (0 AGUARD.ENVIO,1 AGUARD.ORÇAMENTO,2 ORÇ.EM APROVAÇÃO,3 EM COMPRAS,4 CONSERTO EM ANDAMENTO,5 RETORNO C/ CONSERTO,6 RETORNO S/ CONSERTO,7 FINALIZADO,8 CANCELADO)
    update ce set status = case status when 1 then 1 when 2 then 4 when 3 then 5 when 4 then 7 else 0 end;
  end if;
end $$;
alter table ce add column if not exists ficha text;
alter table ce add column if not exists cte text;
alter table ce add column if not exists compra text;
alter table ce add column if not exists dt_followup date;
alter table ce add column if not exists validada text;
alter table ce add column if not exists pcm text;
alter table ce add column if not exists responsavel text;
alter table ce add column if not exists cadastro text;
alter table ce add column if not exists retorno text;
alter table ce add column if not exists aplicacao text;
alter table ce add column if not exists qtd numeric;
alter table ce add column if not exists aprovador text;
alter table ce add column if not exists transportadora text;
alter table ce add column if not exists area_texto text;
create index if not exists ce_ficha on ce(ficha);
