-- ===== PARTE 4: aprovação do supervisor, justificativa e marcações nas fotos =====
alter table fts add column if not exists aprovacao jsonb default '{}';
alter table cm  add column if not exists aprovacao jsonb default '{}';
alter table cm  add column if not exists dados jsonb default '{}';
alter table fotos add column if not exists anot jsonb default '[]';

-- só a função aprovar() pode alterar a coluna aprovacao (ninguém edita direto)
create or replace function guard_aprov() returns trigger language plpgsql as $$
begin
  if new.aprovacao is distinct from old.aprovacao and coalesce(current_setting('app.aprovando',true),'')<>'1' then
    new.aprovacao := old.aprovacao;
  end if;
  return new;
end $$;
drop trigger if exists t_guard_fts on fts; create trigger t_guard_fts before update on fts for each row execute function guard_aprov();
drop trigger if exists t_guard_cm on cm;   create trigger t_guard_cm  before update on cm  for each row execute function guard_aprov();

-- aprovação com um clique: supervisor, coordenador ou master
create or replace function aprovar(p_tab text, p_id text, p_ok boolean, p_obs text default '')
returns void language plpgsql security definer set search_path=public as $$
declare me perfis%rowtype;
begin
  select * into me from perfis where id=auth.uid();
  if me.id is null or not me.aprovado or not me.ativo or not (me.master or me.funcao in ('SUPERVISOR','COORDENADOR')) then
    raise exception 'sem permissão para aprovar';
  end if;
  if p_tab not in ('fts','cm') then raise exception 'tabela inválida'; end if;
  perform set_config('app.aprovando','1',true);
  execute format('update %I set aprovacao=$1 where id=$2',p_tab)
    using jsonb_build_object('status',case when p_ok then 'APROVADA' else 'REPROVADA' end,'por',me.nome,'matricula',me.matricula,'em',now(),'obs',coalesce(p_obs,'')), p_id;
end $$;
revoke all on function aprovar(text,text,boolean,text) from public;
grant execute on function aprovar(text,text,boolean,text) to authenticated;
