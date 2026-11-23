"""Rotina de Inspeção — Ecoresinator (cozinha de cola).

Formulário dedicado (não usa o motor genérico de checklist): leitura
técnica por bico injetor + parâmetros gerais, uma vez por turno.
Aba Histórico: como está o preenchimento + abrir qualquer registro.
"""
import streamlit as st

from src.auth import exigir_login
from src.ecoresinator_hist_ui import renderizar_historico_ecoresinator
from src.ecoresinator_ui import renderizar_ecoresinator
from src.tema import aplicar_tema, desativar_traducao_automatica
from src.sidebar import mostrar_usuario_logado

st.set_page_config(page_title="Ecoresinator", page_icon="🧪", layout="wide")

desativar_traducao_automatica()
usuario = exigir_login()
aplicar_tema(usuario)
mostrar_usuario_logado(usuario)

aba_preencher, aba_historico = st.tabs(["🧪 Preencher", "📜 Histórico"])
with aba_preencher:
    renderizar_ecoresinator(usuario)
with aba_historico:
    renderizar_historico_ecoresinator()
