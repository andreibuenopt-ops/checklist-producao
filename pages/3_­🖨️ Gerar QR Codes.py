"""Área administrativa: gera o QR Code fixo de cada checklist para impressão."""
from itertools import groupby

import streamlit as st

from src.auth import exigir_login
from src.db import app_base_url
from src.models import listar_templates, obter_logo_bytes_com_fallback
from src.qrcode_gen import gerar_cartaz_pdf, gerar_etiqueta_png, url_do_checklist, validar_url_base
from src.tema import aplicar_tema, desativar_traducao_automatica
from src.sidebar import mostrar_usuario_logado

st.set_page_config(page_title="Gerar QR Codes", page_icon="🖨️", layout="centered")

desativar_traducao_automatica()
usuario = exigir_login()
aplicar_tema(usuario)
mostrar_usuario_logado(usuario)

if not usuario.pode_gerar_qrcodes:
    st.warning("Seu nível de acesso não permite gerar QR Codes.")
    st.stop()

st.title("🖨️ Gerar QR Codes")
st.markdown(
    """
Cada área tem **um único QR Code fixo** — imprime uma vez só e cola no local.
Ao escanear, o sistema detecta automaticamente a data e o turno atual e abre
o checklist certo (não é preciso trocar o papel a cada turno ou dia).
"""
)

base_url = st.text_input("URL pública do app (após o deploy)", value=app_base_url())

url_valida, erro_url = validar_url_base(base_url)
if not url_valida:
    st.error(f"⚠️ {erro_url}")
    st.info("A geração de QR Code fica bloqueada até a URL estar correta — evita imprimir e colar o QR errado.")
    st.stop()

logo_bytes = obter_logo_bytes_com_fallback()

templates = listar_templates()
if not templates:
    st.info("Nenhum checklist cadastrado ainda.")
    st.stop()

for setor_nome, grupo in groupby(
    templates, key=lambda t: (t.get("setores_processo") or {}).get("nome", "Outros")
):
    st.markdown(f"### {setor_nome}")
    for template in grupo:
        url = url_do_checklist(base_url, template["slug"])
        with st.container(border=True):
            st.subheader(template["titulo"])
            st.caption(f"{template['area']} · {template['codigo']} · {url}")

            col_img, col_botoes = st.columns([1, 1])
            etiqueta_png = gerar_etiqueta_png(
                template["titulo"], template["area"], template["codigo"], url, logo_bytes,
            )
            with col_img:
                st.image(etiqueta_png, width=220)

            with col_botoes:
                st.download_button(
                    "⬇️ Baixar PNG (rápido)",
                    data=etiqueta_png,
                    file_name=f"qrcode_{template['slug']}.png",
                    mime="image/png",
                    use_container_width=True,
                    key=f"png_{template['id']}",
                )
                cartaz_pdf = gerar_cartaz_pdf(
                    template["titulo"], template["area"], template["codigo"], url, logo_bytes,
                )
                st.download_button(
                    "⬇️ Baixar cartaz PDF (A5, para impressão)",
                    data=cartaz_pdf,
                    file_name=f"cartaz_{template['slug']}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"pdf_{template['id']}",
                )
