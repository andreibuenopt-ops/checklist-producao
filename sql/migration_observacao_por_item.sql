-- Migration: adiciona observação específica por item de resposta.
-- Rodar UMA VEZ no SQL Editor do Supabase (projeto pmwpawnmjnxtvixebfap).
-- Idempotente — pode rodar de novo sem erro se já tiver sido aplicada.

alter table checklist_respostas
    add column if not exists observacao text not null default '';
