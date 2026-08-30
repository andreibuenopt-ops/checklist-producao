"""Ponto de entrada do app — Checklist Diário Rotineiro (Streamlit + Supabase)."""
import streamlit as st

from src.auth import exigir_login, logout, trocar_senha
from src.sidebar import mostrar_usuario_logado
from src.tema import aplicar_tema

st.set_page_config(
    page_title="Checklist de Produção",
    page_icon="✅",
    layout="centered",
    initial_sidebar_state="expanded",
)

usuario = exigir_login()
aplicar_tema()

# Senha resetada pelo master: troca obrigatória antes de qualquer outra ação
if usuario.senha_temporaria:
    st.warning("Sua senha foi resetada pelo administrador. Defina uma nova senha para continuar.")
    with st.form("form_trocar_senha"):
        nova = st.text_input("Nova senha", type="password")
        confirmar = st.text_input("Confirmar nova senha", type="password")
        salvar = st.form_submit_button("Salvar nova senha", type="primary", use_container_width=True)

    if salvar:
        if len(nova) < 6:
            st.error("A senha deve ter no mínimo 6 caracteres.")
        elif nova != confirmar:
            st.error("As senhas não conferem.")
        else:
            trocar_senha(usuario.id, nova)
            st.success("Senha atualizada. Faça login novamente.")
            logout()
            st.rerun()
    st.stop()

# QR code fixo por área: quem escaneia chega direto na tela de preenchimento
if st.query_params.get("area"):
    st.switch_page("pages/1_📋_Preencher_Checklist.py")

mostrar_usuario_logado(usuario)

st.title("✅ Checklist Diário Rotineiro")
st.markdown(
    """
Bem-vindo(a) ao sistema de checklists de inspeção.

- **📋 Preencher Checklist** — abra pelo QR Code fixado na área, ou escolha manualmente
  aqui no menu lateral.
"""
)

if usuario.pode_ver_dashboard:
    st.markdown("- **📊 Dashboard** — acompanhe os checklists do dia atual ou de qualquer dia passado.")
if usuario.pode_gerar_qrcodes:
    st.markdown("- **🖨️ Gerar QR Codes** — imprima os cartões para colar nas áreas.")
st.markdown("- **💡 Sugestões** — proponha novos itens de inspeção com base no que observar em campo.")
st.markdown("- **🔍 5 Porquês** — análise de causa raiz para não-conformidades críticas.")
if usuario.eh_master:
    st.markdown("- **🛠️ Administração** — usuários, áreas/equipamentos, checklists e aprovação de sugestões.")

st.info("Use o menu à esquerda para navegar entre as páginas.")
