-- Migration: perguntas de PARADA no checklist do Supervisor de Turno
-- (FR-CD-M2-019) + suporte a sub-perguntas com foto obrigatória.
-- Rodar UMA VEZ no SQL Editor do Supabase. Idempotente.

alter table checklist_template_itens
    add column if not exists pai_item_id uuid references checklist_template_itens(id) on delete cascade;
alter table checklist_template_itens
    add column if not exists exige_foto boolean not null default false;
create index if not exists idx_itens_pai on checklist_template_itens (pai_item_id);

-- As 3 perguntas novas entram no FIM do checklist (as atuais continuam iguais).
-- Cada uma é Sim/Não; ao responder "Sim", abre as sub-perguntas daquela parada
-- (cadastradas em Administração → Checklists cadastrados → "Sub-perguntas").
do $$
declare
    tid uuid;
    p   text;
    prox int;
begin
    select id into tid from checklist_templates where codigo = 'FR-CD-M2-019';
    if tid is null then
        raise notice 'Checklist FR-CD-M2-019 (Supervisor de Turno) não encontrado — nada feito.';
        return;
    end if;

    foreach p in array array[
        'Houve parada programada no turno?',
        'Houve parada para limpeza de saída de finos no turno?',
        'Houve parada de oportunidade para limpeza?'
    ] loop
        if not exists (select 1 from checklist_template_itens where template_id = tid and pergunta = p) then
            select coalesce(max(ordem), 0) + 1 into prox from checklist_template_itens where template_id = tid;
            insert into checklist_template_itens (template_id, ordem, pergunta, criticidade, tipo_resposta)
            values (tid, prox, p, 'alta', 'sim_nao');
        end if;
    end loop;
end $$;
