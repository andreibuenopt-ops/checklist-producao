"""Sidebar padrão do app: logo, nome/matrícula/papel de quem está logado
e botão de sair. Chame em toda página, logo após exigir_login().
"""
import streamlit as st

from src.auth import logout
from src.models import obter_logo_url_com_fallback


def mostrar_usuario_logado(usuario):
    with st.sidebar:
        logo = obter_logo_url_com_fallback()
        if logo:
            st.image(logo, use_container_width=True)
        st.markdown(f"**{usuario.nome}**")
        st.caption(f"Matrícula {usuario.matricula} · {usuario.papel.capitalize()}")
        if st.button("Sair", use_container_width=True, key="logout_sidebar"):
            logout()
            st.rerun()
