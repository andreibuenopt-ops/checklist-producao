"""Sugestões de novos itens de checklist — qualquer usuário sugere, master aprova."""
import streamlit as st

from src.auth import exigir_login
from src.models import (
    aprovar_sugestao,
    criar_sugestao,
    listar_sugestoes,
    listar_templates,
    rejeitar_sugestao,
)
from src.tema import aplicar_tema, desativar_traducao_automatica
from src.sidebar import mostrar_usuario_logado

st.set_page_config(page_title="Sugestões", page_icon="💡", layout="centered")

desativar_traducao_automatica()
usuario = exigir_login()
aplicar_tema(usuario)
mostrar_usuario_logado(usuario)
st.title("💡 Sugestões de Itens de Checklist")
st.caption("Identificou algo em campo que deveria virar item de verificação? Sugira aqui.")

abas = ["✍️ Enviar sugestão"]
if usuario.eh_master:
    abas.append("📋 Analisar pendentes")

tabs = st.tabs(abas)

# ---------------------------------------------------------------------
with tabs[0]:
    templates = listar_templates()
    mapa = {t["titulo"]: t["id"] for t in templates}

    with st.form("form_sugestao", clear_on_submit=True):
        checklist_escolhido = st.selectbox("Checklist", list(mapa.keys()))
        pergunta = st.text_area("Item sugerido (redija como uma pergunta de checklist)")
        justificativa = st.text_area("Por que esse item deveria existir? (situação identificada em campo)")
        criticidade = st.selectbox("Criticidade sugerida", ["media", "alta", "critica"])
        if st.form_submit_button("Enviar sugestão", type="primary"):
            if not pergunta.strip() or not justificativa.strip():
                st.error("Pergunta e justificativa são obrigatórias.")
            else:
                criar_sugestao(mapa[checklist_escolhido], usuario.id, pergunta, justificativa, criticidade)
                st.success("Sugestão enviada. O master irá analisar.")

    st.divider()
    st.subheader("Minhas sugestões enviadas")
    minhas = [s for s in listar_sugestoes() if s["sugerido_por"] == usuario.id]
    if not minhas:
        st.info("Você ainda não enviou nenhuma sugestão.")
    for s in minhas:
        icone = {"pendente": "🟡", "aprovada": "✅", "rejeitada": "🔴"}[s["status"]]
        with st.container(border=True):
            st.write(f"{icone} **{s['pergunta_sugerida']}**")
            st.caption(f"{s['checklist_templates']['titulo']} · {s['status'].capitalize()}")
            if s["status"] == "rejeitada" and s.get("motivo_rejeicao"):
                st.caption(f"Motivo: {s['motivo_rejeicao']}")

# ---------------------------------------------------------------------
if usuario.eh_master:
    with tabs[1]:
        pendentes = listar_sugestoes(status="pendente")
        if not pendentes:
            st.success("Nenhuma sugestão pendente. ✅")

        for s in pendentes:
            with st.container(border=True):
                st.write(f"**{s['pergunta_sugerida']}**")
                st.caption(
                    f"Checklist: {s['checklist_templates']['titulo']} · "
                    f"Sugerido por: {s['usuarios']['nome']} · Criticidade sugerida: {s['criticidade_sugerida']}"
                )
                st.write(s["justificativa"])

                col1, col2 = st.columns(2)
                with col1:
                    criticidade_final = st.selectbox(
                        "Criticidade ao aprovar", ["media", "alta", "critica"],
                        index=["media", "alta", "critica"].index(s["criticidade_sugerida"]),
                        key=f"crit_{s['id']}",
                    )
                    if st.button("✅ Aprovar e adicionar ao checklist", key=f"aprovar_{s['id']}"):
                        aprovar_sugestao(
                            s["id"], s["template_id"], usuario.id,
                            s["pergunta_sugerida"], criticidade_final,
                        )
                        st.success("Item adicionado ao checklist.")
                        st.rerun()
                with col2:
                    motivo = st.text_input("Motivo (se rejeitar)", key=f"motivo_{s['id']}")
                    if st.button("🔴 Rejeitar", key=f"rejeitar_{s['id']}"):
                        rejeitar_sugestao(s["id"], usuario.id, motivo or "Não especificado")
                        st.rerun()
