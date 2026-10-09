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

# Posição fixa de cada página na barra lateral (1=app, depois pages/1..6
# na ordem do nome do arquivo). Se reordenar/renomear arquivo em pages/,
# atualiza aqui também.
_POSICAO_DASHBOARD = 3
_POSICAO_QRCODES = 4
_POSICAO_ADMINISTRACAO = 5


def _css_ocultar_paginas(usuario) -> str:
    """Esconde da barra lateral o link de página que o usuário não pode
    usar. É só cosmético — quem digitar a URL direto ainda esbarra no
    bloqueio de dentro da própria página, que é a proteção de verdade."""
    ocultar = []
    if not usuario.pode_ver_dashboard:
        ocultar.append(_POSICAO_DASHBOARD)
    if not usuario.pode_gerar_qrcodes:
        ocultar.append(_POSICAO_QRCODES)
    if not usuario.pode_gerenciar_sistema:
        ocultar.append(_POSICAO_ADMINISTRACAO)
    if not ocultar:
        return ""
    seletores = ", ".join(
        f'[data-testid="stSidebarNav"] li:nth-child({n})' for n in ocultar
    )
    return f"{seletores} {{ display: none !important; }}"


def desativar_traducao_automatica():
    """Evita que o navegador (Chrome/tradutor automático) traduza a página
    e corrompa os emojis/acentos do menu lateral. Chame ANTES de
    `exigir_login()`, no topo de cada arquivo — assim cobre até a tela
    de login, que roda antes de `aplicar_tema()`."""
    st.markdown(
        """
        <script>
        (function() {
            var meta = document.createElement('meta');
            meta.name = 'google';
            meta.content = 'notranslate';
            document.head.appendChild(meta);
            document.documentElement.setAttribute('translate', 'no');
            document.documentElement.classList.add('notranslate');
        })();
        </script>
        """,
        unsafe_allow_html=True,
    )


def aplicar_tema(usuario=None):
    """Chame logo após `exigir_login()`, no topo de cada página."""
    cor = obter_cor_primaria()
    css_paginas = _css_ocultar_paginas(usuario) if usuario else ""
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
        {css_paginas}
        </style>
        """,
        unsafe_allow_html=True,
    )
