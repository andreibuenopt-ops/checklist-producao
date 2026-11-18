-- ===== PARTE 2: USUÁRIOS, FUNÇÕES, DONOS DE ÁREA, PERMISSÕES, FOTOS =====
-- Rode DEPOIS do schema.sql

create table if not exists perfis (
  id uuid primary key references auth.users(id) on delete cascade,
  nome text not null,
  email text not null,                       -- e-mail Guararapes (contato)
  matricula text unique not null,            -- login = matrícula
  funcao text not null check (funcao in ('COORDENADOR','SUPERVISOR','DONO_AREA','EXECUTANTE','PCM')),
  disc smallint check (disc in (0,1)),       -- 0 elétrica, 1 mecânica, null = PCM/Produção
  setor text,                                -- MECÂNICA, ELÉTRICA, PCM, PRODUÇÃO, SUPERVISÃO
  master boolean not null default false,
  aprovado boolean not null default false,   -- só o master libera
  ativo boolean not null default true,
  trocar_senha boolean not null default true,
  criado_em timestamptz default now());

create table if not exists permissoes (
  perfil_id uuid references perfis(id) on delete cascade,
  modulo text check (modulo in ('dashboard','fts','cm','ce','catalogo','fotos')),
  nivel smallint not null check (nivel in (0,1,2)),   -- 0 sem acesso, 1 ver, 2 editar
  primary key (perfil_id, modulo));

-- quem trabalha em qual área (um dono por vaga, executantes sem ser dono)
create table if not exists perfil_areas (
  area text references areas(nome) on delete cascade,
  perfil_id uuid references perfis(id) on delete cascade,
  papel text not null default 'EXECUTANTE' check (papel in ('DONO','EXECUTANTE')),
  primary key (area, perfil_id));

create table if not exists fotos (
  id bigserial primary key, registro text not null,      -- id da FTS / CM / CE
  path text not null, legenda text, bytes int,
  criado_por uuid default auth.uid(), criado_em timestamptz default now());
create index if not exists fotos_reg on fotos(registro);

-- PCM sempre é master
create or replace function perfis_pcm_master() returns trigger language plpgsql as $$
begin if new.funcao='PCM' then new.master:=true; end if; return new; end $$;
drop trigger if exists t_pcm_master on perfis;
create trigger t_pcm_master before insert or update on perfis for each row execute function perfis_pcm_master();

-- funções de permissão
create or replace function eh_master() returns boolean language sql stable security definer set search_path=public as $$
  select coalesce((select master and aprovado and ativo from perfis where id=auth.uid()),false) $$;
create or replace function nivel_mod(m text) returns int language sql stable security definer set search_path=public as $$
  select case when eh_master() then 2 else coalesce((
    select p.nivel from permissoes p join perfis f on f.id=p.perfil_id
    where p.perfil_id=auth.uid() and p.modulo=m and f.aprovado and f.ativo),0) end $$;
create or replace function usuario_ativo() returns boolean language sql stable security definer set search_path=public as $$
  select coalesce((select aprovado and ativo from perfis where id=auth.uid()),false) $$;
-- o próprio usuário marca que já trocou a senha
create or replace function senha_trocada() returns void language sql security definer set search_path=public as $$
  update perfis set trocar_senha=false where id=auth.uid() $$;
revoke all on function senha_trocada() from public; grant execute on function senha_trocada() to authenticated;
grant execute on function eh_master(), nivel_mod(text), usuario_ativo() to authenticated;

-- RLS das tabelas de usuários
alter table perfis enable row level security; alter table permissoes enable row level security;
alter table perfil_areas enable row level security; alter table fotos enable row level security;
grant select,insert,update,delete on perfis,permissoes,perfil_areas,fotos to authenticated;
grant usage,select on all sequences in schema public to authenticated;

drop policy if exists p_sel on perfis;  create policy p_sel on perfis for select to authenticated using (id=auth.uid() or eh_master());
drop policy if exists p_all on perfis;  create policy p_all on perfis for all to authenticated using (eh_master()) with check (eh_master());
drop policy if exists pm_sel on permissoes; create policy pm_sel on permissoes for select to authenticated using (perfil_id=auth.uid() or eh_master());
drop policy if exists pm_all on permissoes; create policy pm_all on permissoes for all to authenticated using (eh_master()) with check (eh_master());
drop policy if exists pa_sel on perfil_areas; create policy pa_sel on perfil_areas for select to authenticated using (usuario_ativo());
drop policy if exists pa_all on perfil_areas; create policy pa_all on perfil_areas for all to authenticated using (eh_master()) with check (eh_master());
drop policy if exists f_sel on fotos; create policy f_sel on fotos for select to authenticated using (nivel_mod('fotos')>=1);
drop policy if exists f_ins on fotos; create policy f_ins on fotos for insert to authenticated with check (nivel_mod('fotos')>=2);
drop policy if exists f_del on fotos; create policy f_del on fotos for delete to authenticated using (nivel_mod('fotos')>=2);

-- troca as políticas abertas do schema.sql por políticas por módulo
do $$ declare r record; begin
 for r in select * from (values ('fts','fts'),('cm','cm'),('cm_itens','cm'),('ce','ce'),('materiais','catalogo'),('ferramentas','catalogo')) v(t,m) loop
  execute format('drop policy if exists "auth_all" on %I',r.t);
  execute format('drop policy if exists s_sel on %I',r.t); execute format('drop policy if exists s_ins on %I',r.t);
  execute format('drop policy if exists s_upd on %I',r.t); execute format('drop policy if exists s_del on %I',r.t);
  execute format('create policy s_sel on %I for select to authenticated using (nivel_mod(%L)>=1)',r.t,r.m);
  execute format('create policy s_ins on %I for insert to authenticated with check (nivel_mod(%L)>=2)',r.t,r.m);
  execute format('create policy s_upd on %I for update to authenticated using (nivel_mod(%L)>=2) with check (nivel_mod(%L)>=2)',r.t,r.m,r.m);
  execute format('create policy s_del on %I for delete to authenticated using (nivel_mod(%L)>=2)',r.t,r.m);
 end loop;
 drop policy if exists "auth_all" on areas;
 drop policy if exists ar_sel on areas; create policy ar_sel on areas for select to authenticated using (usuario_ativo());
 drop policy if exists ar_all on areas; create policy ar_all on areas for all to authenticated using (eh_master()) with check (eh_master());
end $$;
-- dashboard lê CM/CE: quem tem 'dashboard' vê também
drop policy if exists d_cm on cm; create policy d_cm on cm for select to authenticated using (nivel_mod('dashboard')>=1);
drop policy if exists d_cmi on cm_itens; create policy d_cmi on cm_itens for select to authenticated using (nivel_mod('dashboard')>=1);
drop policy if exists d_ce on ce; create policy d_ce on ce for select to authenticated using (nivel_mod('dashboard')>=1);

-- fotos: bucket privado, só links assinados
insert into storage.buckets (id,name,public) values ('fotos','fotos',false) on conflict do nothing;
drop policy if exists st_sel on storage.objects; create policy st_sel on storage.objects for select to authenticated using (bucket_id='fotos' and nivel_mod('fotos')>=1);
drop policy if exists st_ins on storage.objects; create policy st_ins on storage.objects for insert to authenticated with check (bucket_id='fotos' and nivel_mod('fotos')>=2);
drop policy if exists st_del on storage.objects; create policy st_del on storage.objects for delete to authenticated using (bucket_id='fotos' and nivel_mod('fotos')>=2);

-- ===== PRIMEIRO MASTER (você) — 1) crie o usuário em Authentication > Users com e-mail
-- <SUA_MATRICULA>@fts.guararapes.local e senha Guara@123 (marque "Auto Confirm"); 2) edite e rode:
-- insert into perfis(id,nome,email,matricula,funcao,disc,setor,master,aprovado,trocar_senha)
-- select id,'SEU NOME COMPLETO','seu.email@guararapes.com.br','SUA_MATRICULA','PCM',null,'PCM',true,true,true
-- from auth.users where email='SUA_MATRICULA@fts.guararapes.local';
