"""Índice de aderência (quais checklists o pessoal mais esquece) e relatório
mensal de realização — visão de gestão (supervisor, coordenação e acima)."""
from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.aderencia import montar_relatorio
from src.auth import exigir_login
from src.models import obter_logo_bytes_com_fallback
from src.pdf_relatorio_mensal import gerar_csv_relatorio, gerar_pdf_relatorio_mensal
from src.sidebar import mostrar_usuario_logado
from src.tema import aplicar_tema, desativar_traducao_automatica
from src.turnos import turno_e_data_referencia

st.set_page_config(page_title="Aderência", page_icon="📈", layout="wide")

desativar_traducao_automatica()
usuario = exigir_login()
aplicar_tema(usuario)
mostrar_usuario_logado(usuario)

if not usuario.pode_ver_dashboard:
    st.error("Seu nível de acesso (produção) não permite ver o índice de aderência.")
    st.stop()

st.title("📈 Aderência dos checklists")
st.caption(
    "Mede quantos dos checklists que **deveriam** ter sido feitos (cada checklist x cada turno x cada dia) "
    "foram de fato **concluídos e assinados**. O turno em andamento não entra na conta."
)

hoje_producao = turno_e_data_referencia().data_referencia
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


@st.cache_data(ttl=120, show_spinner="Calculando…")
def _relatorio(inicio: date, fim: date) -> dict:
    return montar_relatorio(inicio, fim)


def _pct(v) -> str:
    return "—" if v is None else f"{v * 100:.0f}%"


def _metricas(g: dict):
    c = st.columns(5)
    c[0].metric("Aderência geral", _pct(g["aderencia"]))
    c[1].metric("Esperados", g["esperados"])
    c[2].metric("Realizados", g["realizados"])
    c[3].metric("Não realizados", g["nao_realizados"])
    c[4].metric("Assinados incompletos", g["incompletos"])


aba_indice, aba_mensal = st.tabs(["🏆 O que mais ficam sem preencher", "🗓️ Relatório mensal"])

# ---------------------------------------------------------------------
with aba_indice:
    periodo = st.date_input(
        "Período (dia de produção)",
        value=(hoje_producao.replace(day=1), hoje_producao),
        max_value=hoje_producao, key="ader_periodo",
    )
    if not (isinstance(periodo, (tuple, list)) and len(periodo) == 2):
        st.info("Escolha a data inicial e a final.")
    else:
        rel = _relatorio(periodo[0], periodo[1])
        if rel["geral"]["esperados"] == 0:
            st.info("Ainda não há turnos encerrados nesse período.")
        else:
            _metricas(rel["geral"])

            st.subheader("Por checklist — do que mais é esquecido ao que menos")
            piores = rel["por_checklist"][:10]
            fig = go.Figure(go.Bar(
                x=[(c["aderencia"] or 0) * 100 for c in piores][::-1],
                y=[c["area"] for c in piores][::-1],
                orientation="h",
                text=[_pct(c["aderencia"]) for c in piores][::-1], textposition="auto",
            ))
            fig.update_layout(xaxis_title="Aderência (%)", xaxis_range=[0, 100],
                              height=max(260, 40 * len(piores)), margin=dict(l=0, r=10, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(pd.DataFrame([{
                "Checklist": c["area"], "Código": c["codigo"], "Esperados": c["esperados"],
                "Realizados": c["realizados"], "Não realizados": c["nao_realizados"],
                "Incompletos": c["incompletos"], "Aderência": _pct(c["aderencia"]),
            } for c in rel["por_checklist"]]), hide_index=True, use_container_width=True)

            st.subheader("Por turno")
            st.dataframe(pd.DataFrame([{
                "Turno": t["turno"], "Esperados": t["esperados"], "Realizados": t["realizados"],
                "Não realizados": t["nao_realizados"], "Aderência": _pct(t["aderencia"]),
            } for t in rel["por_turno"]]), hide_index=True, use_container_width=True)

            st.subheader("Checklist x turno — onde mais falta")
            st.dataframe(pd.DataFrame([{
                "Checklist": l["area"], "Turno": l["turno"], "Esperados": l["esperados"],
                "Realizados": l["realizados"], "Não realizados": l["nao_realizados"],
                "Aderência": _pct(l["aderencia"]),
            } for l in rel["ranking"]]), hide_index=True, use_container_width=True)

# ---------------------------------------------------------------------
with aba_mensal:
    meses = []
    ano, mes = hoje_producao.year, hoje_producao.month
    for _ in range(12):
        meses.append((ano, mes))
        mes -= 1
        if mes == 0:
            ano, mes = ano - 1, 12
    ano_sel, mes_sel = st.selectbox(
        "Mês", meses, format_func=lambda am: f"{MESES[am[1] - 1].capitalize()}/{am[0]}", key="rel_mes",
    )
    inicio = date(ano_sel, mes_sel, 1)
    proximo = date(ano_sel + (mes_sel == 12), mes_sel % 12 + 1, 1)
    fim = min(proximo - timedelta(days=1), hoje_producao)

    rel = _relatorio(inicio, fim)
    titulo_periodo = f"{MESES[mes_sel - 1].capitalize()}/{ano_sel}"
    if rel["geral"]["esperados"] == 0:
        st.info("Sem turnos encerrados nesse mês.")
    else:
        _metricas(rel["geral"])
        c1, c2 = st.columns(2)
        c1.metric("Respostas \"Não\" no mês", rel["total_nao"])
        c2.metric("Rondas com atraso justificado", rel["total_atrasos"])

        if usuario.pode_exportar_dashboard:
            b1, b2 = st.columns(2)
            b1.download_button(
                "⬇️ Relatório mensal em PDF",
                data=gerar_pdf_relatorio_mensal(rel, titulo_periodo, obter_logo_bytes_com_fallback()),
                file_name=f"relatorio_checklists_{ano_sel}_{mes_sel:02d}.pdf", mime="application/pdf",
                use_container_width=True,
            )
            b2.download_button(
                "⬇️ Dados em CSV (Excel)", data=gerar_csv_relatorio(rel),
                file_name=f"relatorio_checklists_{ano_sel}_{mes_sel:02d}.csv", mime="text/csv",
                use_container_width=True,
            )
        else:
            st.caption("A exportação do relatório é liberada para supervisor, administrador e master.")

        if rel["itens_mais_nao"]:
            st.subheader("Itens com mais respostas \"Não\"")
            st.dataframe(pd.DataFrame([{
                "Checklist": i["area"], "Pergunta": i["pergunta"], "Qtd.": i["qtd"],
            } for i in rel["itens_mais_nao"]]), hide_index=True, use_container_width=True)
