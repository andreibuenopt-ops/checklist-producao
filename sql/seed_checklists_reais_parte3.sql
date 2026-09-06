-- ============================================================
-- CARGA DOS CHECKLISTS REAIS DA GUARARAPES — PARTE 3/3
-- Operador Prensa (turnos recalculados p/ 22-05/05-14/14-22) e
-- Supervisor de Turno (com itens de texto livre).
-- ============================================================

insert into setores_processo (id, nome, ordem) values (10, 'Supervisão de Turno', 10)
on conflict (id) do nothing;

-- ---- FR-CD-M2-017 · Rotina de Inspeção Operador Prensa ----
insert into checklist_templates (codigo, titulo, area, slug, setor_id, tipo_area, revisao)
select 'FR-CD-M2-017', 'Rotina de Inspeção Operador Prensa', s.nome, 'rotina-de-inspe-o-operador-prensa', 6, 'interno', 'r01'
from setores_processo s where s.id = 6
on conflict (codigo) do update set titulo = excluded.titulo, tipo_area = excluded.tipo_area, revisao = excluded.revisao;

delete from checklist_template_itens where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-017');
insert into checklist_template_itens (template_id, ordem, pergunta, criticidade, tipo_resposta) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 1, 'Qual produto está sendo produzido?', 'media', 'texto_livre'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 2, 'Equalizadora auto ou manual?', 'media', 'texto_livre'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 3, 'Pressão da saída da pré prensa?', 'media', 'texto_livre'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 4, 'Temperatura Unidade Hidraulica pré prensa?', 'media', 'texto_livre'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 5, 'Lubrificação das correntes e cinta aço estão ok?', 'alta', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 6, 'Sicoscan funcionando?', 'critica', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 7, 'Rompedor está de acordo com produto?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 8, 'Intermediaria na posição correta?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 9, 'Ângulo de entrada >1mm<2mm do solicitado?', 'alta', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 10, 'Lavador de gases tem algum problema?', 'alta', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 11, 'Pistas detector bolhas com falhas?', 'critica', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 12, 'Pistas espessurometro com falhas?', 'critica', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 13, 'Sistema de aquecimento correto?', 'alta', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 14, 'Curva real de abertura da prensa está de acordo com teórica?', 'alta', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 15, 'Alinhamento das cintas aço estão ficando entre +-3mm?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 16, 'Silo de fibra reciclada sem falhas?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 17, 'Stenografico sem falhas?', 'alta', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 18, 'Pressão do sistema de trimming?', 'media', 'texto_livre'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 19, 'Algum motor da prensa com alarme de temperatura?', 'critica', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 20, 'Amperagem das serras estão de acordo?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 21, 'Sistema de dosagem dos spray''s sem problemas?', 'alta', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 22, 'Sistema Grecon', 'critica', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 23, 'Sistema IEP', 'critica', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 24, 'Sistema minimax', 'critica', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 25, 'Compressores', 'alta', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 26, 'Tivemos algum desvio de qualidade?', 'alta', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 27, 'Ritmo está acima do orçamento?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 28, 'Houve redução de resina? Qts kg?', 'media', 'texto_livre'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 29, 'Houve redução de parafina? Qts kg?', 'media', 'texto_livre'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 30, 'Descarte de chapas por espessura no finos habilitado?', 'media', 'sim_nao');

delete from checklist_template_horarios where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-017');
insert into checklist_template_horarios (template_id, turno_id, horario, ordem) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 3, '22:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 3, '01:00:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 3, '04:30:00', 3),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 1, '06:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 1, '09:00:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 1, '12:30:00', 3),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 2, '14:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 2, '17:00:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-017'), 2, '21:00:00', 3);

-- ---- FR-CD-M2-019 · Rotina de Inspeção Supervisor de Turno ----
insert into checklist_templates (codigo, titulo, area, slug, setor_id, tipo_area, revisao)
select 'FR-CD-M2-019', 'Rotina de Inspeção Supervisor de Turno', s.nome, 'rotina-de-inspe-o-supervisor-de-turno', 10, 'interno', 'r00'
from setores_processo s where s.id = 10
on conflict (codigo) do update set titulo = excluded.titulo, tipo_area = excluded.tipo_area, revisao = excluded.revisao;

delete from checklist_template_itens where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-019');
insert into checklist_template_itens (template_id, ordem, pergunta, criticidade, tipo_resposta) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 1, 'Qual produto está sendo produzido na prensa?', 'media', 'texto_livre'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 2, 'Qual produto está sendo produzido na lixadeira?', 'media', 'texto_livre'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 3, 'Performance da prensa?', 'media', 'texto_livre'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 4, 'Performance da lixadeira?', 'media', 'texto_livre'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 5, 'Dosagem de Eucalipto está dentro da meta para o produto? Se não, por que? O que foi feito para melhorar?', 'alta', 'texto_livre'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 6, 'Houve redução de consumo de resina no turno?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 7, 'Houve redução de consumo de parafina no turno?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 8, 'Resultados de trações estão abaixo ou acima do alvo?', 'alta', 'texto_livre'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 9, 'Inchamento 24h está abaixo do limite especificado?', 'alta', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 10, 'Produção do refinador está no máximo atingível?', 'media', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 11, 'Shives está dentro do especificado?', 'alta', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 12, 'Foi necessário atuações no processo para melhorar shives, consumo de resina e produtividade? Quais?', 'media', 'texto_livre'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 13, 'Consumo de biomassa está dentro da meta proposta? Foi feito algum ajuste para melhorar consumo de biomassa?', 'media', 'texto_livre'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 14, 'Por quanto tempo foi usado Schrader no turno em 100%?', 'media', 'texto_livre'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 15, 'Houve algum desvio de qualidade superficial na prensa? Qual? O que foi feito para normalizar?', 'alta', 'texto_livre'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 16, 'Houve algum desvio de qualidade na lixadeira? Qual? O que foi feito para normalizar?', 'alta', 'texto_livre'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 17, 'Foi verificado e assinado todos checklists do turno?', 'alta', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 18, 'Foi verificado alguma situação insegura, ato inseguro e aberto cartão radar?', 'critica', 'sim_nao'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 19, 'Faltou algum funcionário? Quem? Motivo?', 'media', 'texto_livre'),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 20, 'Rejeito ficou acima da % meta? Porque? Ação?', 'alta', 'texto_livre');

delete from checklist_template_horarios where template_id = (select id from checklist_templates where codigo = 'FR-CD-M2-019');
insert into checklist_template_horarios (template_id, turno_id, horario, ordem) values
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 3, '23:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 3, '01:00:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 1, '06:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 1, '08:00:00', 2),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 2, '14:00:00', 1),
  ((select id from checklist_templates where codigo = 'FR-CD-M2-019'), 2, '16:00:00', 2);
