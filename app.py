"""Ponto de entrada do app — Checklist Diário Rotineiro (Streamlit + Supabase)."""
import streamlit as st

from src.auth import exigir_login, logout

st.set_page_config(
    page_title="Checklist de Produção",
    page_icon="✅",
    layout="centered",
    initial_sidebar_state="expanded",
)

usuario = exigir_login()

# QR code fixo por área: quem escaneia chega direto na tela de preenchimento
if st.query_params.get("area"):
    st.switch_page("pages/1_📋_Preencher_Checklist.py")

with st.sidebar:
    st.markdown(f"**{usuario.nome}**")
    st.caption(f"Matrícula {usuario.matricula} · {usuario.papel.capitalize()}")
    if st.button("Sair", use_container_width=True):
        logout()
        st.rerun()

st.title("✅ Checklist Diário Rotineiro")
st.markdown(
    """
Bem-vindo(a) ao sistema de checklists de inspeção.

- **📋 Preencher Checklist** — abra pelo QR Code fixado na área, ou escolha manualmente
  aqui no menu lateral.
- **📊 Dashboard** — acompanhe os checklists do dia atual ou de qualquer dia passado.
"""
)

if usuario.eh_supervisor_ou_admin:
    st.markdown("- **🖨️ Gerar QR Codes** — imprima os cartões para colar nas áreas.")

st.info("Use o menu à esquerda para navegar entre as páginas.")
