-- Perguntas "removidas" que já têm histórico: em vez de apagar (o banco não deixa e o histórico se perderia),
-- ficam desativadas — somem do checklist novo, mas o histórico continua mostrando e dá para restaurar.
-- Idempotente. Rodar uma vez no SQL Editor.
alter table checklist_template_itens add column if not exists ativo boolean not null default true;
create index if not exists idx_itens_ativo on checklist_template_itens (template_id, ativo);
