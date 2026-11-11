-- Migration: o dia de produção passa a começar pelo turno C (Noite).
-- A Noite que começa às 22h de domingo agora pertence a SEGUNDA-FEIRA.
-- Registros antigos de Noite estavam na data em que a Noite COMEÇOU, então
-- avançam 1 dia pra ficarem coerentes com a regra nova.
--
-- Rodar UMA VEZ. Tem trava: se rodar de novo, não faz nada.
--
-- IMPORTANTE (código novo já publicado antes do SQL): só avançam os registros
-- CRIADOS ANTES de `corte`. Checklists de Noite criados pelo código novo já
-- estão na regra nova e não podem ser empurrados de novo.
--   * Se ninguém abriu checklist de Noite (após as 22h) desde que o código novo
--     subiu, pode rodar assim mesmo (corte = agora).
--   * Se alguém abriu, troque a linha do corte pela hora em que o código subiu,
--     ex.:  corte timestamptz := '2026-11-11 15:30:00-03';
--
-- O deslocamento é em 2 passos porque (template, turno, data) é único e um
-- UPDATE direto de +1 esbarraria numa linha vizinha ainda não atualizada.

create table if not exists migracoes_aplicadas (
    nome        text primary key,
    aplicada_em timestamptz not null default now()
);

do $$
declare
    corte timestamptz := now();
begin
    if not exists (select 1 from migracoes_aplicadas where nome = 'dia_producao_noite') then
        update checklists set data = data + 10000 where turno_id = 3 and criado_em < corte;
        update checklists set data = data - 9999  where turno_id = 3 and data > date '2040-01-01';

        update ecoresinator_checklists set data = data + 10000 where turno_id = 3 and criado_em < corte;
        update ecoresinator_checklists set data = data - 9999  where turno_id = 3 and data > date '2040-01-01';

        insert into migracoes_aplicadas (nome) values ('dia_producao_noite');
        raise notice 'Migração dia_producao_noite aplicada.';
    else
        raise notice 'Migração dia_producao_noite já tinha sido aplicada — nada feito.';
    end if;
end $$;
