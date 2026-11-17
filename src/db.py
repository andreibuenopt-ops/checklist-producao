"""Cliente Supabase único para todo o app."""
import httpx
import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def _client() -> Client:
    url, chave = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
    try:
        # HTTP/1.1 em vez de HTTP/2: o Streamlit roda cada usuário numa thread
        # e uma conexão HTTP/2 compartilhada entre threads quebra de vez em
        # quando com "httpx.LocalProtocolError". HTTP/1.1 com pool é seguro.
        from supabase import ClientOptions
        opcoes = ClientOptions(httpx_client=httpx.Client(
            http2=False, timeout=httpx.Timeout(60.0, connect=10.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=5, keepalive_expiry=20),
        ))
        return create_client(url, chave, options=opcoes)
    except Exception:
        return create_client(url, chave)


supabase = _client()


def app_base_url() -> str:
    return st.secrets.get("APP_BASE_URL", "")
