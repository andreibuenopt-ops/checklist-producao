-- Migration: desativa os checklists de demonstração/genéricos que foram
-- usados pra construir e testar o sistema — agora substituídos pelos
-- 16 formulários reais da Guararapes (FR-CD-M2-xxx).
--
-- Usa "desativar" (ativo=false), não delete: preserva qualquer checklist
-- já preenchido/assinado contra esses templates (histórico/auditoria
-- continua intacto, só não aparece mais como opção pra preencher hoje).
-- Rodar UMA VEZ no SQL Editor do Supabase, DEPOIS dos seeds novos.

update checklist_templates
set ativo = false
where codigo in (
    'FRCDM2003.r02', 'FRCDM2004.r01', 'FRCDM2005.r01', 'FRCDM2006.r01',
    'FRCDM2007.r01', 'FRCDM2008.r01', 'FRCDM2009.r01', 'FRCDM2010.r01',
    'FRCDM2011.r02'
);
