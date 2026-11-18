-- FTCM: equipamento e modelo por item da CM
alter table cm_itens add column if not exists equip text;
alter table cm_itens add column if not exists modelo text;
