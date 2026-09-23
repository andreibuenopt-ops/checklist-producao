-- Migration: nome de exibição (coluna "area") de checklists que hoje
-- mostram o nome genérico do setor no QR/etiqueta, mas deveriam mostrar
-- o nome específico do próprio checklist. Não mexe em setor_id — o
-- agrupamento por processo continua igual em todo o resto do sistema.
--
-- Isso é só um ponto de partida — daqui pra frente, edite direto em
-- Administração → Checklists Cadastrados → "Nome de exibição no QR".
-- Rodar UMA VEZ no SQL Editor do Supabase.

update checklist_templates set area = 'Área das Serras'              where codigo = 'FR-CD-M2-001';
update checklist_templates set area = 'Tanques de Resina e Secador'  where codigo = 'FR-CD-M2-010';
update checklist_templates set area = 'Sifter e Ventiladores Externos' where codigo = 'FR-CD-M2-011';
update checklist_templates set area = 'Preparação de Cavaco'         where codigo = 'FR-CD-M2-015';
update checklist_templates set area = 'Operador Prensa'              where codigo = 'FR-CD-M2-017';
update checklist_templates set area = 'Auxiliares de Prensa'         where codigo = 'FR-CD-M2-021';
update checklist_templates set area = 'Auxiliares Externos'          where codigo = 'FR-CD-M2-022';
