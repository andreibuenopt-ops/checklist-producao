"""Seletor de equipe usado no Histórico, Dashboard e Aderência."""
import streamlit as st

from src.equipes import indice_da_equipe, listar_equipes


@st.cache_data(ttl=120, show_spinner=False)
def _equipes_cache():
    return listar_equipes()


@st.cache_data(ttl=120, show_spinner=False)
def _indice_cache(equipe_id: str):
    return indice_da_equipe(equipe_id)


def seletor_equipe(chave: str, obrigatoria: bool = False, container=None):
    """Mostra o filtro 'Equipe' e devolve (equipe | None, indice | None).
    Sem nenhuma equipe cadastrada, não mostra nada (filtro desligado)."""
    equipes = _equipes_cache()
    if not equipes:
        return None, None
    alvo = container or st
    opcoes = ([] if obrigatoria else [None]) + [e["id"] for e in equipes]
    por_id = {e["id"]: e for e in equipes}
    escolhida = alvo.selectbox(
        "Equipe", opcoes, key=f"equipe_{chave}",
        format_func=lambda i: "Todas as equipes" if i is None else por_id[i]["nome"],
        help="Mostra o que foi preenchido OU assinado por pessoas da equipe (respeita a data de entrada/saída de cada um).",
    )
    if escolhida is None:
        return None, None
    return por_id[escolhida], _indice_cache(escolhida)
