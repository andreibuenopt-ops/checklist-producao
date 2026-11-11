"""Histórico de checklists (somente leitura, todos os papéis) e assinatura
de checklists de turnos passados que ficaram sem assinar."""
from datetime import timedelta

import streamlit as st

from src.auth import exigir_login
from src.historico_ui import botao_pdf_checklist, renderizar_checklist_somente_leitura
from src.models import (
    concluir_checklist,
    listar_checklists_periodo,
    listar_pendentes_assinatura,
    listar_templates,
    obter_checklist_completo,
    obter_logo_bytes_com_fallback,
)
from src.sidebar import mostrar_usuario_logado
from src.tema import aplicar_tema, desativar_traducao_automatica
from src.turnos import LETRA_TURNO, NOME_TURNO, turno_e_data_referencia

st.set_page_config(page_title="Histórico", page_icon="📜", layout="wide")

desativar_traducao_automatica()
usuario = exigir_login()
aplicar_tema(usuario)
mostrar_usuario_logado(usuario)

st.title("📜 Histórico de checklists")

hoje_producao = turno_e_data_referencia().data_referencia
aba_hist, aba_pend = st.tabs(["📜 Histórico", "✍️ Pendentes de assinatura"])


def _rotulo(c: dict) -> str:
    d = str(c["data"])[:10]
    dia = f"{d[8:10]}/{d[5:7]}"
    turno = f"{LETRA_TURNO.get(c['turno_id'], '')} {NOME_TURNO.get(c['turno_id'], '')}"
    if c["status"] != "completo":
        marca = "🟡 sem assinatura"
    elif c.get("incompleto"):
        marca = "⚠️ incompleto"
    else:
        marca = "✅"
    area = (c.get("checklist_templates") or {}).get("area", "-")
    return f"{dia} · {turno} · {area} · {marca}"


# ---------------------------------------------------------------------
# Histórico
# ---------------------------------------------------------------------
with aba_hist:
    templates = listar_templates()
    nomes_areas = {"Todas as áreas": None, **{t["area"] + " — " + t["codigo"]: t["id"] for t in templates}}

    c1, c2, c3 = st.columns([2, 2, 1])
    area_sel = c1.selectbox("Área", list(nomes_areas.keys()), key="hist_area")
    periodo = c2.date_input(
        "Período (dia de produção)",
        value=(hoje_producao - timedelta(days=3), hoje_producao),
        max_value=hoje_producao, key="hist_periodo",
    )
    turno_sel = c3.selectbox("Turno", ["Todos", "A Manhã", "B Tarde", "C Noite"], key="hist_turno")

    if not (isinstance(periodo, (tuple, list)) and len(periodo) == 2):
        st.info("Escolha a data inicial e a final.")
    else:
        inicio, fim = periodo
        linhas = [
            c for c in listar_checklists_periodo(inicio, fim, template_id=nomes_areas[area_sel])
            if c["status"] != "pendente"
        ]
        if turno_sel != "Todos":
            alvo = {"A Manhã": 1, "B Tarde": 2, "C Noite": 3}[turno_sel]
            linhas = [c for c in linhas if c["turno_id"] == alvo]

        if not linhas:
            st.info("Nenhum checklist nesse filtro.")
        else:
            st.caption(f"{len(linhas)} checklist(s) encontrado(s).")
            escolhido = st.selectbox(
                "Abrir checklist", options=linhas, format_func=_rotulo, key="hist_escolhido",
            )
            renderizar_checklist_somente_leitura(obter_checklist_completo(escolhido["id"], com_bytes=False))
            botao_pdf_checklist(escolhido["id"], obter_logo_bytes_com_fallback(), obter_checklist_completo, "hist")

# ---------------------------------------------------------------------
# Pendentes de assinatura (turnos que já acabaram)
# ---------------------------------------------------------------------
with aba_pend:
    st.caption(
        "Checklists de turnos que já acabaram e ficaram sem assinatura. Ao assinar aqui, o checklist "
        "**conta no dia em que foi feito**, não no dia da assinatura. Se ainda houver perguntas sem "
        "resposta, ele é assinado como **incompleto** (fica marcado)."
    )
    so_meus = usuario.papel == "producao"
    pendentes = listar_pendentes_assinatura(colaborador_id=usuario.id if so_meus else None)
    if so_meus:
        st.caption("Mostrando os checklists que você preencheu.")

    if not pendentes:
        st.success("Nenhum checklist pendente de assinatura. ✅")
    else:
        def _rotulo_pendente(c):
            extra = f" — faltam {c['faltando']}" if c["faltando"] else ""
            return f"{_rotulo(c)}{extra}"

        pend = st.selectbox("Checklist pendente", options=pendentes, format_func=_rotulo_pendente, key="pend_sel")
        renderizar_checklist_somente_leitura(obter_checklist_completo(pend["id"], com_bytes=False), resumido=True)

        if pend["faltando"]:
            st.warning(
                f"⚠️ Faltam {pend['faltando']} de {pend['esperadas']} respostas. Se assinar agora, "
                "o checklist conta como realizado, mas fica marcado como **incompleto**."
            )
        comentario = st.text_area(
            "Comentário (opcional)", value=pend.get("comentario") or "", key=f"pend_coment_{pend['id']}",
        )
        if st.button("✅ Assinar e concluir", type="primary", key=f"pend_assinar_{pend['id']}"):
            concluir_checklist(pend["id"], usuario.id, comentario.strip(), incompleto=pend["faltando"] > 0)
            st.success("Checklist assinado. ✅")
            st.rerun()
