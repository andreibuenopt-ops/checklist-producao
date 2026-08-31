"""Formulário do operador — acesso manual (via sidebar).

A chegada via QR Code é tratada direto em app.py, sem trocar de página —
ver o comentário em src/preenchimento_ui.py sobre por quê.
"""
from itertools import groupby

import streamlit as st

from src.auth import exigir_login
from src.models import buscar_template_por_slug, listar_templates
from src.preenchimento_ui import renderizar_preenchimento
from src.sidebar import mostrar_usuario_logado
from src.tema import aplicar_tema

st.set_page_config(page_title="Preencher Checklist", page_icon="📋", layout="centered")

usuario = exigir_login()
aplicar_tema()
mostrar_usuario_logado(usuario)
st.title("📋 Preencher Checklist")
st.caption(f"Preenchendo como **{usuario.nome}** · {usuario.papel.capitalize()}")

# ---------------------------------------------------------------------
# Escolher a área — manual só pra supervisor/coordenação/master.
# Produção só chega aqui vindo de QR Code (tratado em app.py); se cair
# nesta página sem vir de QR, vê a lista dos checklists existentes só
# pra referência (não consegue abrir nenhum pra preencher).
# ---------------------------------------------------------------------
slug = st.query_params.get("area")
template = buscar_template_por_slug(slug) if slug else None

if not template:
    templates = listar_templates()
    if not templates:
        st.warning("Nenhum checklist cadastrado ainda.")
        st.stop()

    chave_setor = lambda t: (t.get("setores_processo") or {}).get("nome", "Outros")
    grupos = {setor: list(itens) for setor, itens in groupby(templates, key=chave_setor)}

    if not usuario.pode_escolher_checklist_manualmente:
        st.error("📷 Escaneie o QR Code fixado na área para abrir o checklist correspondente.")
        st.divider()
        st.subheader("Checklists existentes")
        st.caption(
            "Só pra você ver o que existe — o preenchimento só libera "
            "escaneando o QR Code fixado na área."
        )
        for setor_nome, itens in grupos.items():
            with st.container(border=True):
                st.markdown(f"**{setor_nome}**")
                for t in itens:
                    st.caption(f"📋 {t['titulo']} · {t['codigo']}")
        st.stop()

    setor_escolhido = st.selectbox("Setor do processo", list(grupos.keys()))
    opcoes = {t["titulo"]: t for t in grupos[setor_escolhido]}
    escolha = st.selectbox("Checklist", list(opcoes.keys()))
    template = opcoes[escolha]

renderizar_preenchimento(usuario, template)
