-- ============================================================
-- CARGA DOS CHECKLISTS REAIS DA GUARARAPES — PARTE 2/3
-- Auxiliares de Prensa + Auxiliares Externos (rotinas de limpeza,
-- formato em matriz item x horário, mesma lógica dos demais).
-- ============================================================

-- ---- FR-CD-M2-021 · Rotina de limpeza da prensa - Auxiliares de Prensa ----
insert into checklist_templates (codigo, titulo, area, slug, setor_id, tipo_area, revisao)
select 'FR-CD-M2-021', 'Rotina de limpeza da prensa - Auxiliares de Prensa', s.nome, 'rotina-de-limpeza-da-prensa-auxiliares-de-prensa', 6, 'interno', 'r01'
from setores_processo s where s.id = 6
on conflict (codigo) do update set titulo = excluded.titulo, tipo_area = excluded.tipo_area, revisao = excluded.revisao;

delete from checklist_template_itens where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-021');
insert into checklist_template_itens (template_id, ordem, pergunta, criticidade, tipo_resposta) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 1, 'Limpeza do raspador e bandeja entrada superior', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 2, 'Limpeza bandejas inferiores saida (esteira roletes)', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 3, 'Limpeza calha de óleo entrada inferior acima raspador inferior', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 4, 'Limpeza na coifa direita e esquerda entrada da prensa lavador de gases', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 5, 'Limpeza coifas direita e esquerda saída da prensa lavador de gases', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 6, 'Limpeza bandejas inferiores saída (raspador inferior)', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 7, 'Limpeza das contenções de óleo vindas das calhas laterais e da entrada da prensa', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 8, 'Limpeza calhas laterais de óleo lado direito', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 9, 'Limpeza calhas laterais de óleo lado esquerdo', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 10, 'Limpeza fosso da prensa e tanques lavador gases', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 11, 'Limpeza de calhas de óleo ambos lados fosso da prensa', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 12, 'Limpeza da sujeira das esteiras de roletes inferiores e superiores com aspirador', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 13, 'Verificado se não há obstrução no tubo de drenagem calha de óleo da entrada superior?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 14, 'Coleta do óleo das contenções da entrada e dos frames?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 15, 'Foi realizado limpeza no raspador superior em abertura de nariz?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 16, 'Foi realizado limpeza no raspador inferior em abertura de nariz?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 17, 'Foi realizado limpeza dentro das esteiras de roletes saida superior em parada de produção?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 18, 'Foi realizado limpeza dentro das esteiras de roletes saida inferior em parada de produção?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 19, 'Foi realizado limpeza dentro das esteiras de roletes entrada superior em parada de produção?', 'media', 'sim_nao');

delete from checklist_template_horarios where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-021');
insert into checklist_template_horarios (template_id, turno_id, horario, ordem) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 3, '00:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 3, '04:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 1, '07:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 1, '12:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 2, '15:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-021'), 2, '21:00:00', 2);

-- ---- FR-CD-M2-022 · Rotina de limpeza área externa - Auxiliares Externos ----
insert into checklist_templates (codigo, titulo, area, slug, setor_id, tipo_area, revisao)
select 'FR-CD-M2-022', 'Rotina de limpeza área externa - Auxiliares Externos', s.nome, 'rotina-de-limpeza-rea-externa-auxiliares-externos', 3, 'externo', 'r01'
from setores_processo s where s.id = 3
on conflict (codigo) do update set titulo = excluded.titulo, tipo_area = excluded.tipo_area, revisao = excluded.revisao;

delete from checklist_template_itens where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-022');
insert into checklist_template_itens (template_id, ordem, pergunta, criticidade, tipo_resposta) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 1, 'Limpeza área da peneira de cavacos MDF2', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 2, 'Limpeza área da peneira de cavacos MDF1', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 3, 'Limpeza piso refinador (passagem visitas)', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 4, 'Limpeza piso abaixo ciclones cinzas, EVA, ECO e fornalha (ar, soprador ou água)', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 5, 'Limpeza abaixo silos, pó, trimming, finos e lippel (ar ou soprador)', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 6, 'Limpeza calha chegada do pré aquecedor', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 7, 'Limpeza área dos Id fans e secador', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 8, 'Limpeza dos trilho do silo Lippel', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 9, 'Limpeza passadiço central silo de casca', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 10, 'Limpeza área atrás da tremonha auxiliar da caldeira', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 11, 'Limpeza e organização área de recebimento resina e parafina', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 12, 'Limpeza unidade hidraulica caldeira', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 13, 'Limpeza tela das portas da torre de resfriamento', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 14, 'Limpeza bunker PLUG e peneira hidrostatica', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 15, 'Drenar contenções ecoresinator, bombas de resina e fosso residuos atrás refinador', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 16, 'Limpeza das bandejas do ecoresinator', 'media', 'sim_nao');

delete from checklist_template_horarios where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-022');
insert into checklist_template_horarios (template_id, turno_id, horario, ordem) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 3, '00:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 3, '04:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 1, '07:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 1, '12:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 2, '15:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-022'), 2, '21:00:00', 2);
