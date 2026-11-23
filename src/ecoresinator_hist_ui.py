"""Aba 'Histórico' do Ecoresinator: como está o preenchimento (grade dia × turno),
abrir qualquer registro na tela e acompanhar a evolução dos parâmetros."""
from datetime import timedelta

import pandas as pd
import streamlit as st

from src.ecoresinator import ecoresinator_historico
from src.ecoresinator_hist import contar_falhas, montar_grade, resumo, rotulo_turno
from src.ecoresinator_ui import ROTULOS_GLOBAIS, botao_pdf_ecoresinator, renderizar_ecoresinator_somente_leitura
from src.models import nomes_usuarios
from src.turnos import NOME_TURNO, ORDEM_NO_DIA, turno_e_data_referencia

TTL = 180


@st.cache_data(ttl=TTL, show_spinner="Carregando histórico…")
def _historico_cache(inicio, fim):
    return ecoresinator_historico(inicio, fim)


@st.cache_data(ttl=TTL, show_spinner=False)
def _nomes_cache(ids: tuple):
    return nomes_usuarios(ids)


def renderizar_historico_ecoresinator():
    ref = turno_e_data_referencia()
    col_a, col_b, col_c = st.columns([2, 2, 1])
    inicio = col_a.date_input("De", value=ref.data_referencia - timedelta(days=13), max_value=ref.data_referencia, key="eco_h_ini")
    fim = col_b.date_input("Até", value=ref.data_referencia, max_value=ref.data_referencia, key="eco_h_fim")
    if col_c.button("🔄 Atualizar", use_container_width=True, key="eco_h_att"):
        st.cache_data.clear()
        st.rerun()
    if inicio > fim:
        st.error("A data inicial não pode ser depois da final.")
        return
    if (fim - inicio).days > 92:
        st.warning("Período muito grande — mostrando só os últimos 92 dias.")
        inicio = fim - timedelta(days=92)

    registros = _historico_cache(inicio, fim)
    r = resumo(registros, inicio, fim, ref.data_referencia, ref.turno_id)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Esperados", r["esperados"])
    m2.metric("✅ Concluídos", r["concluidos"])
    m3.metric("🟡 Em andamento", r["andamento"])
    m4.metric("❌ Sem registro", r["sem_registro"])

    st.markdown("**Preenchimento por dia e turno**")
    grade = pd.DataFrame(montar_grade(registros, inicio, fim, ref.data_referencia, ref.turno_id))
    st.dataframe(grade, hide_index=True, use_container_width=True)

    if not registros:
        st.info("Nenhum registro do Ecoresinator nesse período.")
        return

    st.divider()
    st.markdown("**Abrir um registro**")
    opcoes = {
        f"{str(x['data'])[8:10]}/{str(x['data'])[5:7]} · {rotulo_turno(x['turno_id'])} · "
        f"{'✅' if x['status'] == 'completo' else '🟡'}"
        + (f" · ⚠️ {contar_falhas(x)} falha(s)" if contar_falhas(x) else ""): x
        for x in registros
    }
    escolhido = opcoes[st.selectbox("Registro", list(opcoes), key="eco_h_sel")]
    nomes = _nomes_cache((escolhido.get("colaborador_id"), escolhido.get("supervisor_id")))
    renderizar_ecoresinator_somente_leitura(escolhido, NOME_TURNO[escolhido["turno_id"]], nomes)
    botao_pdf_ecoresinator(escolhido, NOME_TURNO[escolhido["turno_id"]], nomes, f"hist_{escolhido['id']}")

    st.divider()
    with st.expander("📈 Evolução de um parâmetro ao longo dos turnos"):
        numericos = {c: ROTULOS_GLOBAIS[c] for c in ROTULOS_GLOBAIS if any(x.get(c) not in (None, "") and _eh_num(x.get(c)) for x in registros)}
        if not numericos:
            st.caption("Ainda não há leituras numéricas registradas.")
            return
        campo = st.selectbox("Parâmetro", list(numericos), format_func=numericos.get, key="eco_h_param")
        pontos = sorted(
            ((str(x["data"])[:10], x["turno_id"], float(x[campo])) for x in registros if _eh_num(x.get(campo)) and float(x[campo]) != 0),
            key=lambda t: (t[0], ORDEM_NO_DIA[t[1]]),
        )
        if pontos:
            df = pd.DataFrame({"leitura": [p[2] for p in pontos]},
                              index=[f"{p[0][8:10]}/{p[0][5:7]} {rotulo_turno(p[1])[0]}" for p in pontos])
            st.line_chart(df)
        else:
            st.caption("Sem valores diferentes de zero nesse parâmetro.")


def _eh_num(v) -> bool:
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False
