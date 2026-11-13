"""App de teste: Administração (sub-perguntas e armazenamento), usuário master."""
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

import src.auth as auth_mod
import src.fotos as fotos_mod
import src.models as models_mod
import src.paradas as paradas_mod

# Qualquer consulta ao banco devolve "nada" (listas vazias), menos o que for definido abaixo.
for modulo in (auth_mod, models_mod, fotos_mod):
    modulo.supabase = MagicMock()

CHAMADAS = st.session_state.setdefault("_admin_chamadas", [])
TEMPLATE = {
    "id": "t1", "codigo": "FR-CD-M2-019", "titulo": "Rotina de Inspeção Supervisor de Turno", "area": "Supervisão de Turno",
    "slug": "supervisor", "ativo": True, "tipo_area": "interno", "setor_id": 10,
    "setores_processo": {"nome": "Supervisão de Turno", "ordem": 10}, "equipamentos": None,
}
PAI = {"id": "pai", "template_id": "t1", "ordem": 1, "pergunta": "Houve parada programada no turno?",
       "criticidade": "alta", "tipo_resposta": "sim_nao", "pai_item_id": None, "exige_foto": False}
FILHA = {"id": "filha", "template_id": "t1", "ordem": 2, "pergunta": "Local da parada está limpo?",
         "criticidade": "alta", "tipo_resposta": "sim_nao", "pai_item_id": "pai", "exige_foto": True}

auth_mod.exigir_login = lambda: SimpleNamespace(
    id="u1", nome="Master", papel="master", matricula="1", eh_master=True, pode_gerenciar_masters=True,
    pode_ver_dashboard=True, pode_gerar_qrcodes=True, pode_gerenciar_sistema=True, pode_abrir_5_porques=True,
    pode_exportar_dashboard=True)
models_mod.obter_cor_primaria = lambda: "#667f38"
models_mod.obter_configuracoes = lambda: {"cor_primaria": "#667f38", "logo_url": None, "autocadastro_requer_aprovacao": False}
models_mod.obter_autocadastro_requer_aprovacao = lambda: False
models_mod.listar_usuarios = lambda: []
models_mod.listar_equipamentos = lambda *a, **k: []
models_mod.obter_logo_url_com_fallback = lambda: None
models_mod.listar_templates = lambda apenas_ativos=True: [TEMPLATE]
models_mod.listar_itens = lambda tid: [PAI, FILHA]
models_mod.listar_horarios_todos_turnos = lambda tid: []
models_mod.listar_turnos = lambda: [{"id": 1, "nome": "Manhã"}, {"id": 2, "nome": "Tarde"}, {"id": 3, "nome": "Noite"}]
models_mod.listar_setores = lambda: [{"id": 10, "nome": "Supervisão de Turno", "ordem": 10}]
paradas_mod.listar_itens_parada = lambda tipo, apenas_ativos=True: []
paradas_mod.adicionar_itens_parada = lambda tipo, perguntas, exige_foto=True: CHAMADAS.append(("adicionar_itens_parada", (tipo, perguntas, exige_foto)))
models_mod.adicionar_itens = lambda *a, **k: CHAMADAS.append(("adicionar_itens", a, k))
fotos_mod.uso_armazenamento = lambda: {"banco_mb": 380.0, "fotos_mb": 100.0, "fotos_qtd": 42}
fotos_mod.remover_fotos_antigas = lambda dias: CHAMADAS.append(("apagar_fotos", dias)) or 7

exec(open(Path(__file__).resolve().parent.parent.parent / "pages" / "4_🛠️_Administração.py", encoding="utf-8").read())
