"""App de teste: página "Parada de linha" com um banco falso em session_state."""
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

import src.auth as auth_mod
import src.models as models_mod
import src.paradas as paradas_mod
import src.paradas_ui as pui
import src.sidebar as sidebar_mod
import src.turno_ui as turno_ui_mod
from src.turnos import Turno

_PNG = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7\x9a\xa0\xa0\x00\x00\x00\x00IEND\xaeB`\x82")

PARADAS = st.session_state.setdefault("_db_paradas", [])
RESPOSTAS = st.session_state.setdefault("_db_pr", {})
ITENS = [
    {"id": "i1", "tipo": "corretiva", "ordem": 1, "pergunta": "Local da parada está limpo?", "exige_foto": True, "ativo": True},
    {"id": "i2", "tipo": "corretiva", "ordem": 2, "pergunta": "Ferramentas recolhidas?", "exige_foto": False, "ativo": True},
]


def _buscar(pid):
    return next((p for p in PARADAS if p["id"] == pid), None)


def _criar(tipo, turno_id, data_ref, colaborador_id, descricao=""):
    p = {"id": f"p{len(PARADAS) + 1}", "tipo": tipo, "turno_id": turno_id, "data": data_ref.isoformat(),
         "iniciada_em": "2026-08-31T10:00:00+00:00", "status": "em_andamento", "descricao": descricao, "comentario": "",
         "colaborador_id": colaborador_id, "turnos": {"nome": "Manhã"}}
    PARADAS.append(p)
    return p


def _salvar(resps):
    for r in resps:
        RESPOSTAS[(r["parada_id"], r["item_id"])] = {"resposta": r["resposta"], "observacao": r["observacao"]}
    return len(resps)


def _concluir(pid, uid, comentario):
    p = _buscar(pid)
    p.update(status="completo", supervisor_id=uid, comentario=comentario, concluido_em="2026-08-31T11:00:00+00:00")


# --- login/sidebar/turno
auth_mod.exigir_login = lambda: SimpleNamespace(
    id="u1", nome="Operador Teste", papel="producao", matricula="1", turma=None,
    pode_ver_dashboard=False, pode_gerar_qrcodes=False, pode_gerenciar_sistema=False, pode_abrir_5_porques=False)
models_mod.obter_cor_primaria = lambda: "#667f38"
models_mod.obter_logo_url_com_fallback = lambda: None
models_mod.obter_logo_bytes_com_fallback = lambda: None
sidebar_mod.obter_logo_url_com_fallback = lambda: None
sidebar_mod.atualizar_turma_usuario = lambda *a: None
turno_ui_mod.turno_e_data_referencia = lambda: Turno(1, "Manhã", date(2026, 8, 31))

# --- banco falso (na página e na tela)
paradas_mod.criar_parada = _criar
paradas_mod.listar_paradas_do_turno = lambda turno_id, data_ref: list(PARADAS)
pui.buscar_parada = _buscar
pui.listar_itens_parada = lambda tipo, apenas_ativos=True: [i for i in ITENS if i["tipo"] == tipo]
pui.listar_respostas_parada = lambda pid: {k[1]: v for k, v in RESPOSTAS.items() if k[0] == pid}
pui.salvar_respostas_parada = _salvar
pui.listar_fotos_parada = lambda pid: [f for f in st.session_state.get("_db_pfotos", []) if f["parada_id"] == pid]
pui.concluir_parada = _concluir
pui.atualizar_descricao_parada = lambda pid, d: _buscar(pid).update(descricao=d)
pui.baixar_miniatura = lambda caminho: _PNG
pui.enviar_foto_parada = lambda *a, **k: None
pui.obter_parada_completa = lambda pid, com_bytes=True: {
    "parada": _buscar(pid), "tipo_nome": "Parada corretiva", "turno_nome": "Manhã", "itens": ITENS,
    "respostas": {k[1]: v for k, v in RESPOSTAS.items() if k[0] == pid}, "fotos": [],
    "colaborador_nome": "Operador Teste", "supervisor_nome": "Operador Teste"}

exec(open(Path(__file__).resolve().parent.parent.parent / "pages" / "10_🛑_Parada_de_Linha.py", encoding="utf-8").read())
