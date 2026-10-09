"""Ponto de entrada do app — Checklist Diário Rotineiro (Streamlit + Supabase)."""
import streamlit as st

from src.auth import exigir_login, logout, trocar_senha
from src.models import buscar_template_por_slug
from src.preenchimento_ui import renderizar_preenchimento
from src.sidebar import mostrar_usuario_logado
from src.tema import aplicar_tema, desativar_traducao_automatica

st.set_page_config(
    page_title="Checklist de Produção",
    page_icon="✅",
    layout="centered",
    initial_sidebar_state="expanded",
)

desativar_traducao_automatica()
usuario = exigir_login()
aplicar_tema(usuario)

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

# QR code fixo por área: renderiza o preenchimento AQUI MESMO, sem trocar
# de página. st.switch_page() apaga o ?area= da URL do navegador durante
# a troca (bug conhecido do Streamlit, streamlit/streamlit#9050) — isso
# fazia a tela de preenchimento não saber mais qual checklist abrir.
area_slug = st.query_params.get("area")
if area_slug:
    mostrar_usuario_logado(usuario)
    template = buscar_template_por_slug(area_slug)
    if not template:
        st.error("QR Code inválido ou checklist desativado. Fale com o administrador.")
        st.stop()
    st.title("📋 Preencher Checklist")
    st.caption(f"Preenchendo como **{usuario.nome}** · {usuario.papel.capitalize()}")
    renderizar_preenchimento(usuario, template)
    st.stop()

mostrar_usuario_logado(usuario)

st.title("✅ Checklist Diário Rotineiro")

if usuario.pode_escolher_checklist_manualmente:
    texto_preencher = (
        "- **📋 Preencher Checklist** — abra pelo QR Code fixado na área, ou escolha manualmente "
        "aqui no menu lateral."
    )
else:
    texto_preencher = "- **📋 Preencher Checklist** — escaneie o QR Code fixado na área para abrir o checklist."

st.markdown(f"""
Bem-vindo(a) ao sistema de checklists de inspeção.

{texto_preencher}
""")

if usuario.pode_ver_dashboard:
    st.markdown("- **📊 Dashboard** — acompanhe os checklists do dia atual ou de qualquer dia passado.")
if usuario.pode_gerar_qrcodes:
    st.markdown("- **🖨️ Gerar QR Codes** — imprima os cartões para colar nas áreas.")
st.markdown("- **💡 Sugestões** — proponha novos itens de inspeção com base no que observar em campo.")
st.markdown("- **🔍 5 Porquês** — análise de causa raiz para não-conformidades críticas.")
if usuario.eh_master:
    st.markdown("- **🛠️ Administração** — usuários, áreas/equipamentos, checklists e aprovação de sugestões.")

st.info("Use o menu à esquerda para navegar entre as páginas.")
