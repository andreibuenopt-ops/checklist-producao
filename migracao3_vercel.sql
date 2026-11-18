-- ===== PARTE 3 (Vercel): fotos com categoria/tamanho, update de fotos, item livre na CM =====
alter table fotos add column if not exists cat text default 'Durante';
alter table fotos add column if not exists w int;
alter table fotos add column if not exists h int;
drop policy if exists f_upd on fotos;
create policy f_upd on fotos for update to authenticated using (nivel_mod('fotos')>=2) with check (nivel_mod('fotos')>=2);
-- permite itens que ainda não estão no catálogo
alter table cm_itens drop constraint if exists cm_itens_item_fkey;
