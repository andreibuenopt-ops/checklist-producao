"""App de teste: página de Histórico + pendentes de assinatura."""
import os
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

import src.auth as auth_mod
import src.models as models_mod

PAPEL = os.environ.get("TESTE_PAPEL", "producao")
ASSINADOS = st.session_state.setdefault("_assinados_debug", [])  # sobrevive ao st.rerun()


def _usuario():
    return SimpleNamespace(
        id="u1", nome="Operador Teste", papel=PAPEL, matricula="1",
        pode_ver_dashboard=PAPEL != "producao", pode_gerar_qrcodes=False, pode_gerenciar_sistema=False,
        pode_abrir_5_porques=False, pode_exportar_dashboard=False,
    )


CK = {
    "id": "ck1", "template_id": "t1", "turno_id": 2, "data": "2026-10-13", "status": "em_andamento",
    "incompleto": False, "colaborador_id": "u1", "comentario": "",
    "checklist_templates": {"area": "Área das Serras", "codigo": "FR-CD-M2-001"},
    "respondidas": 3, "esperadas": 8, "faltando": 5,
}
CK_OK = {**CK, "id": "ck2", "status": "completo", "faltando": 0}


def _completo(checklist_id, com_bytes=True):
    return {
        "checklist": {**(CK_OK if checklist_id == "ck2" else CK)},
        "template": {"area": "Área das Serras", "codigo": "FR-CD-M2-001"},
        "turno_nome": "Tarde",
        "itens": [{"id": "i1", "pergunta": "Correia com danos?", "tipo_resposta": "sim_nao"}],
        "horarios": [{"id": "h1", "horario": "15:00:00"}],
        "respostas": {("i1", "h1"): {"resposta": "Não", "observacao": "Trocar amanhã"}},
        "justificativas_atraso": {}, "fotos": [],
        "colaborador_nome": "Fulano", "supervisor_nome": "Beltrano",
    }


auth_mod.exigir_login = _usuario
models_mod.obter_cor_primaria = lambda: "#667f38"
models_mod.obter_logo_url_com_fallback = lambda: None
models_mod.obter_logo_bytes_com_fallback = lambda: None
models_mod.listar_templates = lambda apenas_ativos=True: [
    {"id": "t1", "area": "Área das Serras", "codigo": "FR-CD-M2-001"}]
models_mod.listar_checklists_periodo = lambda ini, fim, template_id=None, status=None: [CK_OK, CK]
models_mod.obter_checklist_completo = _completo
models_mod.listar_pendentes_assinatura = lambda colaborador_id=None, dias=30: [CK]
models_mod.concluir_checklist = lambda cid, uid, com, incompleto=False: ASSINADOS.append((cid, uid, incompleto))

exec(open(Path(__file__).resolve().parent.parent.parent / "pages" / "8_📜_Histórico.py", encoding="utf-8").read())

