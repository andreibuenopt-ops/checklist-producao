"""Modo offline: preparar o celular (com internet) e enviar o que foi
preenchido sem sinal. O preenchimento offline em si fica em offline_pwa/offline.html."""
import streamlit as st

from src.auth import exigir_login
from src.offline import gravar_foto, gravar_ronda, pacote_do_usuario
from src.offline_ui import BASE_PWA, sincronizador
from src.sidebar import mostrar_usuario_logado
from src.tema import aplicar_tema, desativar_traducao_automatica

st.set_page_config(page_title="Modo offline", page_icon="📴", layout="centered")

desativar_traducao_automatica()
usuario = exigir_login()
aplicar_tema(usuario)
mostrar_usuario_logado(usuario)

st.title("📴 Modo offline")
st.caption("Para a área externa, sem sinal: baixe os checklists antes, preencha sem internet e envie quando o sinal voltar.")

ss = st.session_state
ss.setdefault("off_enviar", False)
ss.setdefault("off_resultado", None)
ss.setdefault("off_log", [])
ss.setdefault("off_pacote", None)
ss.setdefault("off_n_proc", 0)
ss.setdefault("off_auto", False)

res = sincronizador(pacote=ss["off_pacote"], enviar=ss["off_enviar"], resultado=ss["off_resultado"])

# --- o celular pediu para gravar uma ronda/foto ---------------------------------
item = res.item
if item and item.get("n") != ss["off_n_proc"]:
    ss["off_n_proc"] = item["n"]
    try:
        saida = (gravar_foto if item.get("tipo") == "foto" else gravar_ronda)(item, usuario)
    except Exception as e:                       # rede/banco: o item continua no celular
        saida = {"estado": "erro", "msg": f"Falha ao gravar ({type(e).__name__}). Tente de novo."}
    ss["off_resultado"] = {"n": item["n"], "tipo": item.get("tipo"), "key": item.get("key"),
                           "id": item.get("id"), "v": item.get("v"), "estado": saida["estado"], "msg": saida["msg"]}
    ss["off_log"].append((item.get("tipo"), saida["estado"], saida["msg"]))
    st.rerun()

if res.fim and ss["off_enviar"]:
    ss["off_enviar"] = False
    st.rerun()
if res.preparo and ss.get("off_preparo_id") != res.preparo.get("id"):   # estado persiste entre reruns: tratar 1 vez só
    ss["off_preparo_id"] = res.preparo.get("id")
    ss["off_preparo"] = dict(res.preparo)
    ss["off_pacote"] = None
    st.rerun()

resumo = res.resumo or {}
pendentes = (resumo.get("rondas") or 0) + (resumo.get("fotos") or 0)

# Enviar sozinho assim que a página abre e há algo guardado no aparelho.
if pendentes and not ss["off_auto"] and not ss["off_enviar"]:
    ss["off_auto"] = True
    ss["off_enviar"] = True
    st.rerun()

# ---------------------------------------------------------------- 1) enviar
st.subheader("📤 Enviar o que foi preenchido sem internet")
if res.erro:
    st.error(res.erro)
outros = [u for u in (resumo.get("usuarios") or []) if u != usuario.id]
if outros:
    st.warning("Há preenchimento neste aparelho feito por **outra pessoa**. Ele só é enviado quando ela entrar com o login dela.")
if res.resumo is None and not res.erro:
    st.info("⏳ Verificando o que está guardado neste aparelho…")
elif pendentes:
    st.info(f"{resumo.get('rondas', 0)} checklist(s) e {resumo.get('fotos', 0)} foto(s) aguardando envio."
            + (" Enviando…" if ss["off_enviar"] else ""))
    if not ss["off_enviar"]:
        if st.button("📤 Enviar agora", type="primary", use_container_width=True):
            ss["off_enviar"] = True
            st.rerun()
else:
    st.success("✅ Nada aguardando envio neste aparelho.")
if resumo.get("erros"):
    st.error(f"{resumo['erros']} item(ns) não foram aceitos pelo sistema. Abra a tela offline para ver o motivo.")
for tipo, estado, msg in ss["off_log"][-8:]:
    getattr(st, "caption")(f"{'📷' if tipo == 'foto' else '📋'} {'✅' if estado == 'ok' else '⚠️'} {msg}")

st.divider()

# ---------------------------------------------------------------- 2) preparar
st.subheader("📥 Preparar este aparelho (precisa de internet)")
st.markdown(
    "1. Toque em **Preparar** — o celular guarda os checklists dos próximos turnos.\n"
    "2. Abra a **tela offline** e use normalmente, **sem sinal**.\n"
    "3. Quando voltar o sinal, abra esta página: o envio é automático."
)
incluir_internos = st.checkbox("Incluir também os checklists de área interna", value=False)
if st.button("📥 Preparar este aparelho", type="primary", use_container_width=True):
    with st.spinner("Baixando checklists…"):
        ss["off_pacote"] = pacote_do_usuario(usuario, incluir_internos)
    st.rerun()

preparo = ss.get("off_preparo")
if preparo:
    st.success(f"✅ Aparelho preparado: {preparo['checklists']} checklist(s) guardados"
               + ("" if preparo.get("sw") else " — ⚠️ o navegador não liberou o uso sem internet; abra a tela offline uma vez agora, com sinal."))
st.markdown(f"[📋 Abrir a tela offline]({BASE_PWA}/offline.html)")
st.caption("Dica: no celular, no menu do navegador, escolha **Adicionar à tela inicial** para abrir como um aplicativo. "
           "O pacote vale ~36 horas — prepare de novo a cada turno.")
