"""App de teste: renderizar_preenchimento() com dependências mockadas.

Usado por tests/test_preenchimento.py via AppTest.from_file(). A variável
de ambiente TESTE_STATUS controla o status do checklist fake
("em_andamento" ou "completo") pra cada cenário de teste.
"""
import os
import sys
from datetime import date
from types import SimpleNamespace

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent.parent))

import streamlit as st

import src.preenchimento_ui as pui

CHAMADAS_SALVAR = []
STATUS_CHECKLIST = os.environ.get("TESTE_STATUS", "em_andamento")

if "ja_configurou_area" not in st.session_state:
    st.query_params["area"] = "silo-cavaco"
    st.session_state["ja_configurou_area"] = True


def _fake_turno_e_data_referencia():
    return SimpleNamespace(turno_id=1, nome="Manhã", data_referencia=date(2026, 8, 31))


def _fake_obter_ou_criar_checklist(template_id, turno_id, data_referencia):
    return {"id": "checklist-1", "status": STATUS_CHECKLIST, "comentario": ""}


def _fake_definir_colaborador(checklist_id, usuario_id):
    pass


def _fake_buscar_checklist(checklist_id):
    return {
        "id": "checklist-1", "status": STATUS_CHECKLIST, "comentario": "",
        "colaborador_id": "u1", "supervisor_id": "sup1" if STATUS_CHECKLIST == "completo" else None,
    }


def _fake_listar_itens(template_id):
    return [
        {"id": "item-1", "pergunta": "Pergunta 1?", "criticidade": "critica"},
        {"id": "item-2", "pergunta": "Pergunta 2?", "criticidade": "media"},
    ]


def _fake_listar_horarios(template_id, turno_id):
    return [{"id": "horario-1", "horario": "07:30:00"}]


def _fake_listar_respostas(checklist_id):
    return {}


def _fake_salvar_respostas_em_lote(respostas):
    CHAMADAS_SALVAR.append(list(respostas))
    return len(respostas)


def _fake_nomes_usuarios(ids):
    return {"u1": "Colaborador Teste", "sup1": "Supervisor Teste"}


def _fake_autenticar(identificador, senha):
    return SimpleNamespace(id="sup1", nome="Supervisor Teste", pode_assinar_checklist=True), None


def _fake_concluir_checklist(*a, **k):
    pass


pui.turno_e_data_referencia = _fake_turno_e_data_referencia
pui.obter_ou_criar_checklist = _fake_obter_ou_criar_checklist
pui.definir_colaborador = _fake_definir_colaborador
pui.buscar_checklist = _fake_buscar_checklist
pui.listar_itens = _fake_listar_itens
pui.listar_horarios = _fake_listar_horarios
pui.listar_respostas = _fake_listar_respostas
pui.salvar_respostas_em_lote = _fake_salvar_respostas_em_lote
pui.nomes_usuarios = _fake_nomes_usuarios
pui.autenticar = _fake_autenticar
pui.concluir_checklist = _fake_concluir_checklist

usuario_fake = SimpleNamespace(id="u1", nome="Teste", papel="producao", pode_assinar_checklist=False)
template_fake = {"id": "template-1", "area": "Área Teste", "codigo": "COD001"}

pui.renderizar_preenchimento(usuario_fake, template_fake)

st.session_state["_chamadas_salvar_debug"] = CHAMADAS_SALVAR
