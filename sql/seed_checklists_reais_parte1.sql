-- ============================================================
-- CARGA DOS CHECKLISTS REAIS DA GUARARAPES — PARTE 1/3
-- 11 checklists padrão (Sim/Não/N-A), extraídos dos FR-CD-M2-xxx.
-- Idempotente: on conflict (codigo) atualiza; itens/horários são
-- recriados do zero a cada rodada (delete + insert) pra sempre
-- refletir exatamente este arquivo.
-- ============================================================

-- ---- FR-CD-M2-001 · Checklist de limpeza e inspeções - Área das serras ----
insert into checklist_templates (codigo, titulo, area, slug, setor_id, tipo_area, revisao)
select 'FR-CD-M2-001', 'Checklist de limpeza e inspeções - Área das serras', s.nome, 'checklist-de-limpeza-e-inspe-es-rea-das-serras', 1, 'interno', 'r02'
from setores_processo s where s.id = 1
on conflict (codigo) do update set titulo = excluded.titulo, tipo_area = excluded.tipo_area, revisao = excluded.revisao;

delete from checklist_template_itens where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-001');
insert into checklist_template_itens (template_id, ordem, pergunta, criticidade, tipo_resposta) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 1, 'Mesa do Stenografico está com as correias nos lugares?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 2, 'Mesa das serras está limpa e sem acumulos?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 3, 'Mangotes de exaustão estão com boa eficiencia?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 4, 'Tem algum ponto gerando sujeira acima do normal?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 5, 'Corte das serras estão de acordo com qualidade?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 6, 'Dimensões estão de acordo?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 7, 'Chapas de amostras estão com a etiqueta de qualidade?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 8, 'Serras diagonais estão com ponto de referencia correto?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 9, 'Serras foram levadas para afiação?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 10, 'Espessurômetros estão funcionando adequadamente?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 11, 'Detectores de bolhas estão funcionando todas pistas?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 12, 'Pressão dos pit rolls e sistema de elevação das serras estão corretos?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 13, 'Grades de proteção estão em boas condições?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 14, 'Portões estão com identificações corretas?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 15, 'Todos os portões estão com dispositivos de bloqueios no local?', 'media', 'sim_nao');

delete from checklist_template_horarios where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-001');
insert into checklist_template_horarios (template_id, turno_id, horario, ordem) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 3, '23:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 3, '01:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 3, '04:00:00', 3),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 1, '07:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 1, '09:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 1, '12:00:00', 3),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 2, '15:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 2, '17:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-001'), 2, '20:00:00', 3);

-- ---- FR-CD-M2-002 · Check list de limpeza e inspeções - Área de Empilhamento ----
insert into checklist_templates (codigo, titulo, area, slug, setor_id, tipo_area, revisao)
select 'FR-CD-M2-002', 'Check list de limpeza e inspeções - Área de Empilhamento', s.nome, 'check-list-de-limpeza-e-inspe-es-rea-de-empilhamento', 8, 'interno', 'r02'
from setores_processo s where s.id = 8
on conflict (codigo) do update set titulo = excluded.titulo, tipo_area = excluded.tipo_area, revisao = excluded.revisao;

delete from checklist_template_itens where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-002');
insert into checklist_template_itens (template_id, ordem, pergunta, criticidade, tipo_resposta) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-002'), 1, 'Gripper com algum ruido?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-002'), 2, 'Pressões de trabalho dos batedores e pit rolls de acordo com indicado no manometro?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-002'), 3, 'Algum rolo de transporte apresentando ruído?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-002'), 4, 'Gripper está realizando manobras com capas adequadamente?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-002'), 5, 'Ocorreu algum problema na área que gerou parada?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-002'), 6, 'Etiquetas estão com informações de acordo com o produto?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-002'), 7, 'Está tendo quebra de chapas na mesa de formação?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-002'), 8, 'Grades de proteção estão em boas condições?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-002'), 9, 'Portões estão com identificações corretas?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-002'), 10, 'Todos os portões estão com dispositivos de bloqueios no local?', 'media', 'sim_nao');

delete from checklist_template_horarios where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-002');
insert into checklist_template_horarios (template_id, turno_id, horario, ordem) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-002'), 3, '23:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-002'), 3, '01:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-002'), 3, '04:00:00', 3),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-002'), 1, '07:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-002'), 1, '09:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-002'), 1, '12:00:00', 3),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-002'), 2, '15:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-002'), 2, '17:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-002'), 2, '20:00:00', 3);

-- ---- FR-CD-M2-003 · Checklist de inspeções - Linha de Formação ----
insert into checklist_templates (codigo, titulo, area, slug, setor_id, tipo_area, revisao)
select 'FR-CD-M2-003', 'Checklist de inspeções - Linha de Formação', s.nome, 'checklist-de-inspe-es-linha-de-forma-o', 5, 'interno', 'r02'
from setores_processo s where s.id = 5
on conflict (codigo) do update set titulo = excluded.titulo, tipo_area = excluded.tipo_area, revisao = excluded.revisao;

delete from checklist_template_itens where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-003');
insert into checklist_template_itens (template_id, ordem, pergunta, criticidade, tipo_resposta) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 1, 'Correia da formação tem danos?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 2, 'Correia desaeradora tem danos?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 3, 'Correia do fiber bin tem danos?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 4, 'Tem mangotes de exaustão furados ou em más condições?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 5, 'Correia de compressão da pré-prensa tem danos?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 6, 'Escova de limpeza inferior da pre-prensa está funcionando?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 7, 'Existe vazamento de fibra em algum ponto específico?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 8, 'Rolos da cabeça de formação tem ruídos?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 9, 'Sistema de spray apresenta alguma irregularidade?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 10, 'Grades de proteção estão em boas condições?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 11, 'Portões estão com identificações corretas?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 12, 'Todos os portões estão com dispositivos de bloqueios no local?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 13, 'Batimento das mangas estão corretos? Pressão do sistema está correto?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 14, 'Portas de inspeção do filtro de mangas, ciclones, tubulações e exaustores estão sem vazamento?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 15, 'Algum bico dos sprays apresentou anomalia na dosagem?', 'media', 'sim_nao');

delete from checklist_template_horarios where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-003');
insert into checklist_template_horarios (template_id, turno_id, horario, ordem) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 3, '23:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 3, '01:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 3, '04:00:00', 3),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 1, '07:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 1, '09:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 1, '12:00:00', 3),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 2, '15:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 2, '17:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-003'), 2, '20:00:00', 3);

-- ---- FR-CD-M2-004 · Checklist de inspeções - Prensa ----
insert into checklist_templates (codigo, titulo, area, slug, setor_id, tipo_area, revisao)
select 'FR-CD-M2-004', 'Checklist de inspeções - Prensa', s.nome, 'checklist-de-inspe-es-prensa', 6, 'interno', 'r02'
from setores_processo s where s.id = 6
on conflict (codigo) do update set titulo = excluded.titulo, tipo_area = excluded.tipo_area, revisao = excluded.revisao;

delete from checklist_template_itens where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-004');
insert into checklist_template_itens (template_id, ordem, pergunta, criticidade, tipo_resposta) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-004'), 1, 'Estado de limpeza da cinta de aço?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-004'), 2, 'Estado de conservação e limpeza cinta intermediária?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-004'), 3, 'Existe vazamento ou ruído nas bombas de óleo térmico e hidraúlica ?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-004'), 4, 'Mangotes do lavador de gases entrada e saída estão limpos?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-004'), 5, 'Equipamentos do lavador de gases apresenta vazamento ou ruído fora do normal?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-004'), 6, 'Esguicho da carreta de combate está saindo água normalmente?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-004'), 7, 'Temos compressores parados? Qual?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-004'), 8, 'Calhas de cobertura do fosso da prensa estão no local?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-004'), 9, 'Portas de inspeção da peneira, centrifuga, tubulações e tanques lavador de gases estão fechadas e sem vazamento?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-004'), 10, 'Grades de proteção estão em boas condições?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-004'), 11, 'Portões estão com identificações corretas?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-004'), 12, 'Todos os portões estão com dispositivos de bloqueios no local?', 'media', 'sim_nao');

delete from checklist_template_horarios where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-004');
insert into checklist_template_horarios (template_id, turno_id, horario, ordem) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-004'), 3, '23:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-004'), 3, '01:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-004'), 3, '04:00:00', 3),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-004'), 1, '07:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-004'), 1, '09:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-004'), 1, '12:00:00', 3),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-004'), 2, '15:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-004'), 2, '17:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-004'), 2, '20:00:00', 3);

-- ---- FR-CD-M2-006 · Check list de limpeza e inspeções - Transporte e Resfriamento de Chapas ----
insert into checklist_templates (codigo, titulo, area, slug, setor_id, tipo_area, revisao)
select 'FR-CD-M2-006', 'Check list de limpeza e inspeções - Transporte e Resfriamento de Chapas', s.nome, 'check-list-de-limpeza-e-inspe-es-transporte-e-resfriamento-de-chapas', 7, 'interno', 'r02'
from setores_processo s where s.id = 7
on conflict (codigo) do update set titulo = excluded.titulo, tipo_area = excluded.tipo_area, revisao = excluded.revisao;

delete from checklist_template_itens where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-006');
insert into checklist_template_itens (template_id, ordem, pergunta, criticidade, tipo_resposta) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-006'), 1, 'Chapa está tendo algum problema ao longo do transporte até final dos viradores?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-006'), 2, 'Algum rolo está com ruído?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-006'), 3, 'Área de rejeio de chapas externas está organizado?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-006'), 4, 'Área de classificação online está organizada e limpa?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-006'), 5, 'Grades de proteção estão em boas condições?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-006'), 6, 'Portões estão com identificações corretas?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-006'), 7, 'Bancada de medição, makita e painel IHM estão organizadas?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-006'), 8, 'Todos os portões estão com dispositivos de bloqueios no local?', 'media', 'sim_nao');

delete from checklist_template_horarios where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-006');
insert into checklist_template_horarios (template_id, turno_id, horario, ordem) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-006'), 3, '23:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-006'), 3, '01:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-006'), 3, '04:00:00', 3),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-006'), 1, '07:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-006'), 1, '09:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-006'), 1, '12:00:00', 3),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-006'), 2, '15:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-006'), 2, '17:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-006'), 2, '20:00:00', 3);

-- ---- FR-CD-M2-010 · Checklist de inspeções - Tanques de Resina e Secador ----
insert into checklist_templates (codigo, titulo, area, slug, setor_id, tipo_area, revisao)
select 'FR-CD-M2-010', 'Checklist de inspeções - Tanques de Resina e Secador', s.nome, 'checklist-de-inspe-es-tanques-de-resina-e-secador', 4, 'interno', 'r02'
from setores_processo s where s.id = 4
on conflict (codigo) do update set titulo = excluded.titulo, tipo_area = excluded.tipo_area, revisao = excluded.revisao;

delete from checklist_template_itens where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-010');
insert into checklist_template_itens (template_id, ordem, pergunta, criticidade, tipo_resposta) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-010'), 1, 'Verificar se existe vazamento nas bombas de transferência e abastecimento de resina e parafina.', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-010'), 2, 'Verificar se vàlvulas de abastecimento e consumo estão de acordo com suas utilizações', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-010'), 3, 'Realizado limpeza dos filtros de resina e parafina?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-010'), 4, 'Portas do secador estão devidamente fechadas e sem vazamento?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-010'), 5, 'Válvulas de dreno do sistema de inundação estão fechadas? Existe água no sistema de inundação acumulada?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-010'), 6, 'Bombas de combate, processo e inundação estão sem vazamentos?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-010'), 7, 'Bunker de fibra reciclada está com material?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-010'), 8, 'Portas dos tanques de resina estão sem vazamento?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-010'), 9, 'Posição das válvulas do sistema de abastecimento dos tanques estão adequadas?', 'media', 'sim_nao');

delete from checklist_template_horarios where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-010');
insert into checklist_template_horarios (template_id, turno_id, horario, ordem) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-010'), 3, '23:30:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-010'), 3, '03:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-010'), 1, '07:30:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-010'), 1, '11:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-010'), 2, '15:30:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-010'), 2, '19:30:00', 2);

-- ---- FR-CD-M2-011 · Checklist de inspeções - Sifter ----
insert into checklist_templates (codigo, titulo, area, slug, setor_id, tipo_area, revisao)
select 'FR-CD-M2-011', 'Checklist de inspeções - Sifter', s.nome, 'checklist-de-inspe-es-sifter', 2, 'externo', 'r02'
from setores_processo s where s.id = 2
on conflict (codigo) do update set titulo = excluded.titulo, tipo_area = excluded.tipo_area, revisao = excluded.revisao;

delete from checklist_template_itens where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-011');
insert into checklist_template_itens (template_id, ordem, pergunta, criticidade, tipo_resposta) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-011'), 1, 'Existe vazamento de fibra em algum ponto específico do prédio?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-011'), 2, 'Existe alguma porta de inspeção danificada ou acrilico quebrado?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-011'), 3, 'Existe algum vazamento de ar nos cilindros de acionamentos dos flaps existentes no processo do Sifter?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-011'), 4, 'Ferramentas armazenadas no local adequado?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-011'), 5, 'Realizado purga no cavalete de vapor dos radiadores de aquecimento do prédio?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-011'), 6, 'Verificar se tem água nos drenos do cavalete de inundação e manter fechado o mesmo.', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-011'), 7, 'Regulagem dos descartes estão apresentando que tipo de fibra?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-011'), 8, 'Bunkers de rejeito foram esvaziados?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-011'), 9, 'Algum ruído nos ventiladores do sifter?', 'media', 'sim_nao');

delete from checklist_template_horarios where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-011');
insert into checklist_template_horarios (template_id, turno_id, horario, ordem) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-011'), 3, '23:30:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-011'), 3, '03:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-011'), 1, '07:30:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-011'), 1, '11:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-011'), 2, '15:30:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-011'), 2, '19:30:00', 2);

-- ---- FR-CD-M2-012 · Checklist de inspeções - Refinador ----
insert into checklist_templates (codigo, titulo, area, slug, setor_id, tipo_area, revisao)
select 'FR-CD-M2-012', 'Checklist de inspeções - Refinador', s.nome, 'checklist-de-inspe-es-refinador', 4, 'interno', 'r02'
from setores_processo s where s.id = 4
on conflict (codigo) do update set titulo = excluded.titulo, tipo_area = excluded.tipo_area, revisao = excluded.revisao;

delete from checklist_template_itens where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-012');
insert into checklist_template_itens (template_id, ordem, pergunta, criticidade, tipo_resposta) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-012'), 1, 'Fluxos e pressões, painel água e selagem estão de acordo com parâmetros de funcionamento padrão?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-012'), 2, 'Está sendo usado tanque de água quente para lavagem da PLUG?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-012'), 3, 'Existe vazamento de vapor nas tubulações ou nos equipamentos do circuito de aquecimento e cozimento do sistema de refinação?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-012'), 4, 'Portas de inspeções do PA e digestor estão em boas condições e sem vazamentos?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-012'), 5, 'Contenção de residuos atrás do refinador está vazia?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-012'), 6, 'Bunker da PLUG e peneira hidrostatica foram esvaziados?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-012'), 7, 'Quadro PCEP está limpo e organizado?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-012'), 8, 'Fluxos da unidade indiana estão de acordo com set point recomendado?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-012'), 9, 'Tanque de água de limpeza dos bicos tem nível de água?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-012'), 10, 'Está sendo dosado os 30kg de uréia no inicio do turno?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-012'), 11, 'Existe vazamento no sistema do ecoresinator ou bombas de resina e parafina?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-012'), 12, 'Mangueiras da lavagem da plug estão desobstruidas?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-012'), 13, 'Temos IBCs com resíduos para dosar na linha?', 'media', 'sim_nao');

delete from checklist_template_horarios where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-012');
insert into checklist_template_horarios (template_id, turno_id, horario, ordem) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-012'), 3, '23:30:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-012'), 3, '03:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-012'), 1, '07:30:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-012'), 1, '11:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-012'), 2, '15:30:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-012'), 2, '19:30:00', 2);

-- ---- FR-CD-M2-013 · Checklist de inspeções - Pátio Biomassa ----
insert into checklist_templates (codigo, titulo, area, slug, setor_id, tipo_area, revisao)
select 'FR-CD-M2-013', 'Checklist de inspeções - Pátio Biomassa', s.nome, 'checklist-de-inspe-es-p-tio-biomassa', 3, 'externo', 'r02'
from setores_processo s where s.id = 3
on conflict (codigo) do update set titulo = excluded.titulo, tipo_area = excluded.tipo_area, revisao = excluded.revisao;

delete from checklist_template_itens where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-013');
insert into checklist_template_itens (template_id, ordem, pergunta, criticidade, tipo_resposta) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-013'), 1, 'Silo de pó e trimming apresentam vazamento?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-013'), 2, 'Existe algum rolo nas esteiras de transportes gerando ruido?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-013'), 3, 'Flaps, roscas e portas de inspeções estão sem problemas?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-013'), 4, 'Raspadores e escovas de limpeza das esteiras estão em boas condições?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-013'), 5, 'Badanas das esteiras estão danificadas?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-013'), 6, 'Catracas silo de finos e lippel estão funcionando corretamente?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-013'), 7, 'Existe vazamento em algum dos silos de biomassa?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-013'), 8, 'Está saindo vapor do ciclone de partida?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-013'), 9, 'Existe algum problema na tremonha auxiliar?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-013'), 10, 'Existe algum problema em todos sistemas de aliminetação do silo Lippel?', 'media', 'sim_nao');

delete from checklist_template_horarios where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-013');
insert into checklist_template_horarios (template_id, turno_id, horario, ordem) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-013'), 3, '23:30:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-013'), 3, '03:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-013'), 1, '07:30:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-013'), 1, '11:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-013'), 2, '15:30:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-013'), 2, '19:30:00', 2);

-- ---- FR-CD-M2-014 · Check list de inspeções - Planta Térmica ----
insert into checklist_templates (codigo, titulo, area, slug, setor_id, tipo_area, revisao)
select 'FR-CD-M2-014', 'Check list de inspeções - Planta Térmica', s.nome, 'check-list-de-inspe-es-planta-t-rmica', 3, 'interno', 'r02'
from setores_processo s where s.id = 3
on conflict (codigo) do update set titulo = excluded.titulo, tipo_area = excluded.tipo_area, revisao = excluded.revisao;

delete from checklist_template_itens where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-014');
insert into checklist_template_itens (template_id, ordem, pergunta, criticidade, tipo_resposta) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-014'), 1, 'Redlers de cinzas estão com nivel de água adequado?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-014'), 2, 'Passado posição do fogo e condição da camada para operação da sala?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-014'), 3, 'Existe algum vazamento no sistema determo fluido da plante térmica?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-014'), 4, 'Verificado todas pressões das bombas dos sistemas auxiliares da planta térmica?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-014'), 5, 'Verificar se cone da pedra está sem obstrução', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-014'), 6, 'Cinzas estão com cavacos ou pedras muito acima do normal?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-014'), 7, 'Existe algum vazamento de vapor nas tubulações de vapor da planta térmica?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-014'), 8, 'Existe algum vazamento no sistema de água da planta térmica?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-014'), 9, 'Portas de inspeções dos cilclones, redlers, shuts, fornalha e roscas estão bem fechadas e sem vazamentos?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-014'), 10, 'Verificar se sensores de niveis das calhas das gavetas estão sem Jump', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-014'), 11, 'Sistema de quimicos está sem vazamentos e funcionamento pleno?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-014'), 12, 'Foi realizado inspeção das temperaturas dos multicilones de cinzas?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-014'), 13, 'Descarga continua está com vazão adequada?', 'media', 'sim_nao');

delete from checklist_template_horarios where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-014');
insert into checklist_template_horarios (template_id, turno_id, horario, ordem) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-014'), 3, '23:30:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-014'), 3, '03:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-014'), 1, '07:30:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-014'), 1, '11:30:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-014'), 2, '15:30:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-014'), 2, '19:30:00', 2);

-- ---- FR-CD-M2-015 · Check list de inspeções - Preparação Cavaco ----
insert into checklist_templates (codigo, titulo, area, slug, setor_id, tipo_area, revisao)
select 'FR-CD-M2-015', 'Check list de inspeções - Preparação Cavaco', s.nome, 'check-list-de-inspe-es-prepara-o-cavaco', 2, 'interno', 'r02'
from setores_processo s where s.id = 2
on conflict (codigo) do update set titulo = excluded.titulo, tipo_area = excluded.tipo_area, revisao = excluded.revisao;

delete from checklist_template_itens where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-015');
insert into checklist_template_itens (template_id, ordem, pergunta, criticidade, tipo_resposta) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-015'), 1, 'Badanas, escova de limpeza e raspadores das esteiras estão adequados?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-015'), 2, 'Existe algum rolo nas esteiras de transportes gerando ruido?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-015'), 3, 'Shuts entre esteiras estão com portas de inspeção fechadas?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-015'), 4, 'Existe algum mangote da peneira com vazamento de cavaco ou finos?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-015'), 5, 'Grades de proteção estão sem avarias?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-015'), 6, 'Peneira está em operação ?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-015'), 7, 'Existe vazamento de finos na tubulação de transporte?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-015'), 8, 'Bporta do bunker de finos está fechada?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-015'), 9, 'Repicador está em operação?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-015'), 10, 'Foram coletados metais para pesagem ?', 'media', 'sim_nao');

delete from checklist_template_horarios where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-015');
insert into checklist_template_horarios (template_id, turno_id, horario, ordem) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-015'), 3, '23:30:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-015'), 3, '04:00:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-015'), 1, '07:30:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-015'), 1, '12:00:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-015'), 2, '15:30:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-015'), 2, '20:30:00', 2);
