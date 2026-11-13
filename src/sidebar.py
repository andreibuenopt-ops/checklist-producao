"""Sidebar padrão do app: logo, nome/matrícula/papel de quem está logado,
turma fixa (editável) e botão de sair. Chame em toda página, logo após
exigir_login().
"""
import streamlit as st

from src.auth import TURMAS_VALIDAS, atualizar_turma_usuario, logout
from src.models import obter_logo_url_com_fallback


def mostrar_usuario_logado(usuario):
    with st.sidebar:
        logo = obter_logo_url_com_fallback()
        if logo:
            st.image(logo, use_container_width=True)
        st.markdown(f"**{usuario.nome}**")
        st.caption(f"Matrícula {usuario.matricula} · {usuario.papel.capitalize()}")

        # Turma fixa do colaborador (A/B/C/D). Quem muda de turma atualiza aqui mesmo.
        atual = getattr(usuario, "turma", None)
        opcoes = ["", *TURMAS_VALIDAS]
        escolhida = st.selectbox(
            "Minha turma", opcoes, index=opcoes.index(atual) if atual in opcoes else 0,
            format_func=lambda t: t or "Não definida", key=f"minha_turma_{usuario.id}",
            help="A turma fixa em que você trabalha. Aparece no histórico, no dashboard e nos PDFs.",
        )
        if (escolhida or None) != atual:
            try:
                atualizar_turma_usuario(usuario.id, escolhida or None)
                usuario.turma = escolhida or None
                st.toast("Turma atualizada.")
            except Exception:
                st.caption("Não consegui salvar a turma (peça ao administrador rodar a atualização do banco).")

        if st.button("Sair", use_container_width=True, key="logout_sidebar"):
            logout()
            st.rerun()
