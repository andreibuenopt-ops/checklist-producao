"""Login que sobrevive a recarregar a página / reconectar.

O Streamlit guarda o login em st.session_state — que se perde quando a rede
cai e o navegador reconecta (ou a página recarrega): o operador volta pra tela
de login e perde o que estava preenchendo. Aqui o login ganha um token ASSINADO
(HMAC) na URL (?s=...), válido por algumas horas. Ao recarregar, a URL ainda
tem o token e o login volta sozinho.

O token só contém o id do usuário + validade + assinatura (não a senha). Quem
copiar a URL inteira entra como aquele usuário até o token vencer — por isso
a validade é curta (um turno) e o botão "Sair" remove o token.
"""
import hashlib
import hmac
import time

import streamlit as st

PARAM = "s"
VALIDADE_HORAS = 14   # um turno + folga


def _segredo() -> bytes:
    try:
        base = st.secrets.get("SESSION_SECRET") or st.secrets["SUPABASE_KEY"]
    except Exception:
        base = "sem-segredo"
    return ("checklist-sessao|" + str(base)).encode()


def _assinar(payload: str) -> str:
    return hmac.new(_segredo(), payload.encode(), hashlib.sha256).hexdigest()[:40]


def gerar_token(usuario_id: str, agora: float | None = None, validade_h: int = VALIDADE_HORAS) -> str:
    exp = int((agora if agora is not None else time.time()) + validade_h * 3600)
    payload = f"{usuario_id}.{exp}"
    return f"{payload}.{_assinar(payload)}"


def validar_token(token: str | None, agora: float | None = None) -> str | None:
    """Devolve o id do usuário se o token for autêntico e não tiver vencido."""
    try:
        usuario_id, exp, assinatura = (token or "").rsplit(".", 2)
        if not hmac.compare_digest(assinatura, _assinar(f"{usuario_id}.{exp}")):
            return None
        if int(exp) < (agora if agora is not None else time.time()):
            return None
        return usuario_id or None
    except Exception:
        return None


def gravar_token_na_url(usuario_id: str):
    """Põe (ou renova) o token na URL. Só mexe se faltar/estiver vencido, pra
    não reescrever a URL a cada rerun."""
    if validar_token(st.query_params.get(PARAM)) != usuario_id:
        st.query_params[PARAM] = gerar_token(usuario_id)


def remover_token_da_url():
    if PARAM in st.query_params:
        del st.query_params[PARAM]
