-- Áreas (centros de custo) do MDF02 / L2
insert into areas(nome,linha,cc) values
 ('MDF02 · DESCASCADOR DE TORAS 02','MDF02','720112'),
 ('MDF02 · PICADOR 02','MDF02','720114'),
 ('MDF02 · SILO DE CAVACO 02','MDF02','720115'),
 ('MDF02 · SILO DE BIOMASSA 02','MDF02','720311'),
 ('MDF02 · LINHA DESFIBRAMENTO','MDF02','720512'),
 ('MDF02 · LINHA DE ENCOLAGEM','MDF02','720711'),
 ('MDF02 · LINHA SECADOR/CICLONES 2','MDF02','720911'),
 ('MDF02 · CLASSIFICADOR DE FIBRAS','MDF02','720912'),
 ('MDF02 · LINHA DE FORMAÇÃO','MDF02','721112'),
 ('MDF02 · LINHA CALDEIRA 02','MDF02','721312'),
 ('MDF02 · LINHA PRENSA CONTÍNUA','MDF02','721512'),
 ('MDF02 · LINHA RESFRIAMENTO','MDF02','721711'),
 ('MDF02 · FORMADORA DE PACOTES (SAÍDA PRENSA)','MDF02','721801'),
 ('MDF02 · LIXADEIRA 02 STEINEMANN','MDF02','722011')
on conflict (nome) do update set linha=excluded.linha, cc=excluded.cc;
-- remove áreas-modelo sem uso criadas antes
delete from areas a where a.linha='MDF02' and a.cc='' 
 and a.nome in ('MDF02 · PLANTA TÉRMICA','MDF02 · REFINADOR','MDF02 · FORMAÇÃO','MDF02 · PRÉ-PRENSA','MDF02 · SAÍDA DE PRENSA','MDF02 · PÁTIO')
 and not exists(select 1 from fts where area_op=a.nome) and not exists(select 1 from cm_itens where area=a.nome)
 and not exists(select 1 from ce where area=a.nome) and not exists(select 1 from perfil_areas where area=a.nome);
