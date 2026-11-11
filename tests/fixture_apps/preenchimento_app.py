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

CHAMADAS_SALVAR = st.session_state.setdefault("_chamadas_salvar_debug", [])  # sobrevive ao st.rerun()
STATUS_CHECKLIST = os.environ.get("TESTE_STATUS", "em_andamento")

if "ja_configurou_area" not in st.session_state:
    st.query_params["area"] = "silo-cavaco"
    st.session_state["ja_configurou_area"] = True


def _fake_turno_e_data_referencia():
    return SimpleNamespace(turno_id=1, nome="Manhã", data_referencia=date(2026, 8, 31))


def _fake_obter_ou_criar_checklist(template_id, turno_id, data_referencia):
    return {"id": "checklist-1", "status": STATUS_CHECKLIST, "comentario": "", "data": "2026-08-31"}


def _fake_definir_colaborador(checklist_id, usuario_id):
    pass


def _fake_buscar_checklist(checklist_id):
    return {
        "id": "checklist-1", "status": STATUS_CHECKLIST, "comentario": "", "data": "2026-08-31",
        "colaborador_id": "u1", "supervisor_id": "sup1" if STATUS_CHECKLIST == "completo" else None,
    }


_GATE = os.environ.get("TESTE_GATE", "0") == "1"
# PNG 1x1 válido pra st.image nas miniaturas
_PNG = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7\x9a\xa0\xa0\x00\x00\x00\x00IEND\xaeB`\x82")


def _fake_listar_itens(template_id):
    itens = [
        {"id": "item-1", "pergunta": "Pergunta 1?", "criticidade": "critica"},
        {"id": "item-2", "pergunta": "Pergunta 2?", "criticidade": "media"},
    ]
    if _GATE:
        itens += [
            {"id": "gate", "pergunta": "Houve parada programada no turno?", "criticidade": "alta", "tipo_resposta": "sim_nao"},
            {"id": "filho", "pergunta": "Local da parada está limpo?", "criticidade": "alta", "tipo_resposta": "sim_nao",
             "pai_item_id": "gate", "exige_foto": True},
        ]
    return itens


def _fake_listar_horarios(template_id, turno_id):
    return [{"id": "horario-1", "horario": "07:30:00"}]


def _db_respostas():
    return st.session_state.setdefault("_db_respostas", {})


def _fake_listar_respostas(checklist_id):
    return dict(_db_respostas()) if _GATE else {}


def _fake_listar_fotos(checklist_id):
    return list(st.session_state.get("_db_fotos", []))


def _fake_remover_respostas(checklist_id, horario_id, item_ids):
    for i in item_ids:
        _db_respostas().pop((i, horario_id), None)


def _fake_salvar_respostas_em_lote(respostas):
    CHAMADAS_SALVAR.append(list(respostas))
    if _GATE:
        for r in respostas:
            _db_respostas()[(r["item_id"], r["horario_id"])] = {"resposta": r["resposta"], "observacao": r["observacao"]}
    return len(respostas)


# Controlado por TESTE_ATRASADO — desacopla o teste do relógio real.
# "0" (padrão): nenhuma ronda atrasada. "1": a ronda única do fixture
# (horario-1) está sempre atrasada, pra testar o fluxo de justificativa.
_ATRASADO_TESTE = os.environ.get("TESTE_ATRASADO", "0") == "1"
JUSTIFICATIVAS_SALVAS = []


def _fake_esta_atrasado(data_referencia, horario_str, turno_nome, referencia_agora=None):
    return _ATRASADO_TESTE


def _fake_listar_justificativas_atraso(checklist_id):
    return {}


def _fake_salvar_justificativa_atraso(checklist_id, horario_id, justificativa, usuario_id):
    JUSTIFICATIVAS_SALVAS.append((checklist_id, horario_id, justificativa, usuario_id))


def _fake_nomes_usuarios(ids):
    return {"u1": "Colaborador Teste", "sup1": "Supervisor Teste"}


def _fake_autenticar(identificador, senha):
    return SimpleNamespace(id="sup1", nome="Supervisor Teste", pode_assinar_checklist=True), None


def _fake_concluir_checklist(*a, **k):
    pass


def _fake_obter_checklist_completo(checklist_id, com_bytes=True):
    return {
        "checklist": _fake_buscar_checklist(checklist_id),
        "template": {"titulo": "Checklist Teste", "area": "Área Teste", "codigo": "COD001"},
        "turno_nome": "Manhã",
        "itens": _fake_listar_itens("template-1"),
        "horarios": _fake_listar_horarios("template-1", 1),
        "respostas": {},
        "justificativas_atraso": {},
        "colaborador_nome": "Colaborador Teste",
        "supervisor_nome": "Supervisor Teste",
    }


def _fake_obter_logo_bytes_com_fallback():
    return None


def _fake_gerar_pdf_checklist(dados, logo_bytes=None):
    return b"%PDF-fake-content"


pui.turno_e_data_referencia = _fake_turno_e_data_referencia
pui.obter_ou_criar_checklist = _fake_obter_ou_criar_checklist
pui.definir_colaborador = _fake_definir_colaborador
pui.buscar_checklist = _fake_buscar_checklist
pui.listar_itens = _fake_listar_itens
pui.listar_horarios = _fake_listar_horarios
pui.listar_respostas = _fake_listar_respostas
pui.salvar_respostas_em_lote = _fake_salvar_respostas_em_lote
pui.esta_atrasado = _fake_esta_atrasado
pui.listar_fotos = _fake_listar_fotos
pui.remover_respostas = _fake_remover_respostas
pui.remover_fotos_de_itens = lambda *a, **k: 0
pui.baixar_miniatura = lambda caminho: _PNG
pui.checklist_anterior = lambda *a, **k: st.session_state.setdefault("_anterior_chamadas", []).append(a) or None
pui.listar_justificativas_atraso = _fake_listar_justificativas_atraso
pui.salvar_justificativa_atraso = _fake_salvar_justificativa_atraso
pui.nomes_usuarios = _fake_nomes_usuarios
pui.autenticar = _fake_autenticar
pui.concluir_checklist = _fake_concluir_checklist
pui.obter_checklist_completo = _fake_obter_checklist_completo
pui.obter_logo_bytes_com_fallback = _fake_obter_logo_bytes_com_fallback
pui.gerar_pdf_checklist = _fake_gerar_pdf_checklist

_PAPEL_TESTE = os.environ.get("TESTE_PAPEL", "producao")
usuario_fake = SimpleNamespace(
    id="u1", nome="Teste", papel=_PAPEL_TESTE,
    pode_assinar_checklist=(_PAPEL_TESTE != "producao"),
)
template_fake = {"id": "template-1", "area": "Área Teste", "codigo": "COD001"}

pui.renderizar_preenchimento(usuario_fake, template_fake)

st.session_state["_justificativas_salvas_debug"] = JUSTIFICATIVAS_SALVAS
