-- Migration: turma fixa do colaborador (A, B, C ou D).
-- Rodar UMA VEZ no SQL Editor do Supabase. Idempotente.
--
-- Atenção: a tabela usuarios tem permissão de leitura POR COLUNA (o hash da
-- senha nunca é legível pelo app). Coluna nova precisa ser liberada
-- explicitamente — sem o grant abaixo o app não consegue ler a turma.

alter table usuarios add column if not exists turma text;

alter table usuarios drop constraint if exists usuarios_turma_check;
alter table usuarios add constraint usuarios_turma_check check (turma in ('A', 'B', 'C', 'D'));

grant select (turma) on usuarios to anon, authenticated;
