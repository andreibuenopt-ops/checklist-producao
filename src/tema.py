"""Aplica a cor de identidade visual (Administração → Identidade Visual)
em cada página, sem precisar editar .streamlit/config.toml nem redeploy.

IMPORTANTE (leia antes de mexer): o Streamlit não tem, até hoje, uma API
oficial para trocar o tema em tempo real — é pedido em aberto no GitHub
deles (issue #14172). O que fazemos aqui é injetar CSS por cima dos
elementos nativos, o que cobre bem botões (a maior parte do "colorido" do
app), mas não é 100% garantido para todo widget em toda versão futura do
Streamlit. Se algum componente não acompanhar a cor trocada aqui, o
método garantido é editar `primaryColor` em `.streamlit/config.toml` e
fazer redeploy — esse sim sempre funciona, para qualquer widget.
"""
import streamlit as st

from src.models import obter_cor_primaria


def aplicar_tema():
    """Chame logo após `exigir_login()`, no topo de cada página."""
    cor = obter_cor_primaria()
    st.markdown(
        f"""
        <style>
        :root {{
            --st-primary-color: {cor} !important;
            --st-color-primary: {cor} !important;
        }}
        .stButton > button[kind="primary"],
        [data-testid="stBaseButton-primary"],
        [data-testid="baseButton-primary"] {{
            background-color: {cor} !important;
            border-color: {cor} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
