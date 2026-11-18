-- Linhas, áreas internas e centro de custo
alter table areas add column if not exists linha text;
alter table areas add column if not exists cc text not null default '';
-- chave passa a ser "LINHA · ÁREA" (ex.: MDF02 · PÁTIO)
do $$
declare o text; n text;
begin
  foreach o in array array['PÁTIO','REFINADOR','PRENSA','ACABAMENTO'] loop
    n := 'MDF02 · '||o;
    if exists(select 1 from areas where nome=o) then
      insert into areas(nome,linha) values (n,'MDF02') on conflict (nome) do nothing;
      update fts set area_op=n where area_op=o;
      update cm_itens set area=n where area=o;
      update ce set area=n where area=o;
      update perfil_areas set area=n where area=o and not exists(select 1 from perfil_areas p2 where p2.area=n and p2.perfil_id=perfil_areas.perfil_id);
      delete from perfil_areas where area=o;
      delete from areas where nome=o;
    end if;
  end loop;
end $$;
-- áreas e centros de custo reais do MDF02: rode migracao6_cc_mdf02.sql
