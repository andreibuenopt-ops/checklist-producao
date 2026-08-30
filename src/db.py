"""Cliente Supabase único para todo o app."""
import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def _client() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


supabase = _client()


def app_base_url() -> str:
    return st.secrets.get("APP_BASE_URL", "")
