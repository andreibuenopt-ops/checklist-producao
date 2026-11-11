-- Migration: o dia de produção passa a começar pelo turno C (Noite).
-- A Noite que começa às 22h de domingo agora pertence a SEGUNDA-FEIRA.
-- Registros antigos de Noite estavam na data em que a Noite COMEÇOU, então
-- avançam 1 dia pra ficarem coerentes com a regra nova.
--
-- Rodar UMA VEZ. Tem trava: se rodar de novo, não faz nada (senão
-- empurraria os registros mais um dia). O deslocamento é feito em 2 passos
-- porque (template, turno, data) é único e um UPDATE direto de +1 poderia
-- esbarrar numa linha vizinha ainda não atualizada.

create table if not exists migracoes_aplicadas (
    nome        text primary key,
    aplicada_em timestamptz not null default now()
);

do $$
begin
    if not exists (select 1 from migracoes_aplicadas where nome = 'dia_producao_noite') then
        update checklists set data = data + 10000 where turno_id = 3;
        update checklists set data = data - 9999  where turno_id = 3;

        update ecoresinator_checklists set data = data + 10000 where turno_id = 3;
        update ecoresinator_checklists set data = data - 9999  where turno_id = 3;

        insert into migracoes_aplicadas (nome) values ('dia_producao_noite');
        raise notice 'Migração dia_producao_noite aplicada.';
    else
        raise notice 'Migração dia_producao_noite já tinha sido aplicada — nada feito.';
    end if;
end $$;
