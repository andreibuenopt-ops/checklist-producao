"""Histórico de checklists (somente leitura, todos os papéis) e assinatura
de checklists de turnos passados que ficaram sem assinar."""
from datetime import timedelta

import streamlit as st

from src.auth import exigir_login
from src.historico_ui import botao_pdf_checklist, renderizar_checklist_somente_leitura
from src.paradas import TIPOS_CURTOS, listar_paradas_periodo, obter_parada_completa
from src.paradas_ui import botao_pdf_parada, renderizar_parada_somente_leitura
from src.models import (
    concluir_checklist,
    dados_usuarios,
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
aba_hist, aba_pend, aba_par = st.tabs(["📜 Histórico", "✍️ Pendentes de assinatura", "🛑 Paradas"])


def _rotulo(c: dict, pessoas: dict | None = None) -> str:
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
    quem = (pessoas or {}).get(c.get("colaborador_id")) or {}
    pessoa = f" · {quem['nome'].split()[0]}" + (f" (Turma {quem['turma']})" if quem.get("turma") else "") if quem.get("nome") else ""
    return f"{dia} · {turno} · {area} · {marca}{pessoa}"


# ---------------------------------------------------------------------
# Histórico
# ---------------------------------------------------------------------
with aba_hist:
    templates = listar_templates()
    nomes_areas = {"Todas as áreas": None, **{t["area"] + " — " + t["codigo"]: t["id"] for t in templates}}

    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
    area_sel = c1.selectbox("Área", list(nomes_areas.keys()), key="hist_area")
    periodo = c2.date_input(
        "Período (dia de produção)",
        value=(hoje_producao - timedelta(days=3), hoje_producao),
        max_value=hoje_producao, key="hist_periodo",
    )
    turno_sel = c3.selectbox("Turno", ["Todos", "A Manhã", "B Tarde", "C Noite"], key="hist_turno",
                             help="Horário em que o checklist foi feito.")
    turma_sel = c4.selectbox("Turma", ["Todas", "A", "B", "C", "D"], key="hist_turma",
                             help="Turma fixa do colaborador que preencheu (cadastro).")

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

        pessoas = dados_usuarios({c.get("colaborador_id") for c in linhas})
        if turma_sel != "Todas":
            linhas = [c for c in linhas if (pessoas.get(c.get("colaborador_id")) or {}).get("turma") == turma_sel]

        if not linhas:
            st.info("Nenhum checklist nesse filtro.")
        else:
            st.caption(f"{len(linhas)} checklist(s) encontrado(s).")
            escolhido = st.selectbox(
                "Abrir checklist", options=linhas, format_func=lambda c: _rotulo(c, pessoas), key="hist_escolhido",
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
        pessoas_pend = dados_usuarios({c.get("colaborador_id") for c in pendentes})

        def _rotulo_pendente(c):
            extra = f" — faltam {c['faltando']}" if c["faltando"] else ""
            return f"{_rotulo(c, pessoas_pend)}{extra}"

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

# ---------------------------------------------------------------------
# Paradas de linha (histórico)
# ---------------------------------------------------------------------
with aba_par:
    p1, p2 = st.columns([2, 1])
    per_par = p1.date_input(
        "Período (dia de produção)", value=(hoje_producao - timedelta(days=7), hoje_producao),
        max_value=hoje_producao, key="par_periodo",
    )
    tipo_sel = p2.selectbox("Tipo", ["Todos", *TIPOS_CURTOS], format_func=lambda t: t if t == "Todos" else TIPOS_CURTOS[t], key="par_tipo")
    if not (isinstance(per_par, (tuple, list)) and len(per_par) == 2):
        st.info("Escolha a data inicial e a final.")
    else:
        paradas_hist = listar_paradas_periodo(per_par[0], per_par[1], None if tipo_sel == "Todos" else tipo_sel)
        if not paradas_hist:
            st.info("Nenhuma parada registrada nesse filtro.")
        else:
            st.caption(f"{len(paradas_hist)} parada(s) encontrada(s).")

            def _rotulo_parada(pr):
                d = str(pr["data"])[:10]
                turno = f"{LETRA_TURNO.get(pr['turno_id'], '')} {NOME_TURNO.get(pr['turno_id'], '')}"
                estado = "✅" if pr["status"] == "completo" else "🟡 em andamento"
                return f"{d[8:10]}/{d[5:7]} · {turno} · {TIPOS_CURTOS[pr['tipo']]} · {str(pr['iniciada_em'])[11:16]} · {estado}"

            parada_escolhida = st.selectbox("Abrir parada", paradas_hist, format_func=_rotulo_parada, key="par_escolhida")
            renderizar_parada_somente_leitura(obter_parada_completa(parada_escolhida["id"], com_bytes=False))
            botao_pdf_parada(parada_escolhida["id"], obter_logo_bytes_com_fallback(), "hist")
