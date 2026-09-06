-- Migration: suporte a itens de "texto livre" no checklist (perguntas
-- abertas tipo "Qual produto está sendo produzido?", usadas no checklist
-- do Supervisor de Turno). Rodar UMA VEZ no SQL Editor do Supabase.

alter table checklist_template_itens
    add column if not exists tipo_resposta text not null default 'sim_nao'
        check (tipo_resposta in ('sim_nao', 'texto_livre'));

-- Para itens de texto livre, a resposta de fato fica gravada na coluna
-- "observacao" (já existente) — "resposta" vira só um marcador 'Texto'.
alter table checklist_respostas drop constraint if exists checklist_respostas_resposta_check;
alter table checklist_respostas
    add constraint checklist_respostas_resposta_check
    check (resposta in ('Sim', 'Não', 'N/A', 'Texto'));
