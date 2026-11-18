-- Especialidade: 0 ELÉTRICA, 1 MECÂNICA, 2 PRODUÇÃO, 3 OUTROS
do $$
declare r record;
begin
  for r in select c.conrelid::regclass as t, c.conname from pg_constraint c
    where c.contype='c' and c.conrelid::regclass::text in ('fts','cm_itens','ce','perfis') and pg_get_constraintdef(c.oid) ilike '%disc%'
  loop execute format('alter table %s drop constraint %I', r.t, r.conname); end loop;
end $$;
alter table fts add constraint fts_disc_chk check (disc is null or disc between 0 and 3);
alter table cm_itens add constraint cm_itens_disc_chk check (disc is null or disc between 0 and 3);
alter table ce add constraint ce_disc_chk check (disc is null or disc between 0 and 3);
alter table perfis add constraint perfis_disc_chk check (disc is null or disc between 0 and 3);

-- impede abrir FTS/CM/CE em especialidade diferente da do usuário (PCM/master podem tudo)
create or replace function guard_disc() returns trigger language plpgsql security definer set search_path=public as $$
declare p record;
begin
  if NEW.disc is null then return NEW; end if;
  if TG_OP='UPDATE' and NEW.disc is not distinct from OLD.disc then return NEW; end if;
  select master, disc into p from perfis where id=auth.uid();
  if not found or p.master or p.disc is null then return NEW; end if;
  if NEW.disc <> p.disc then raise exception 'Especialidade não permitida para o seu perfil'; end if;
  return NEW;
end $$;
drop trigger if exists g_disc on fts; create trigger g_disc before insert or update on fts for each row execute function guard_disc();
drop trigger if exists g_disc on cm_itens; create trigger g_disc before insert or update on cm_itens for each row execute function guard_disc();
drop trigger if exists g_disc on ce; create trigger g_disc before insert or update on ce for each row execute function guard_disc();
