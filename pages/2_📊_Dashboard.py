"""Dashboard — resultados do dia atual ou de qualquer dia passado."""
import io
from collections import Counter

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.auth import exigir_login
from src.models import checklists_do_dia, listar_templates, nomes_usuarios, respostas_por_data
from src.turnos import agora_local

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

usuario = exigir_login()

if not usuario.pode_ver_dashboard:
    st.error("Seu nível de acesso (produção) não permite visualizar o dashboard.")
    st.stop()

st.title("📊 Dashboard de Checklists")

# Paleta de status (mesmos papéis em todo o app: Sim=good, Não=critical, N/A=neutro)
COR_SIM, COR_NAO, COR_NA = "#0ca30c", "#d03b3b", "#8a8a86"
COR_PENDENCIA = "#d03b3b"

# ---------------------------------------------------------------------
# Filtros
# ---------------------------------------------------------------------
templates = listar_templates()
col_data, col_area = st.columns([1, 2])
with col_data:
    data_ref = st.date_input("Data", value=agora_local().date(), max_value=agora_local().date())
with col_area:
    nomes_areas = ["Todas as áreas"] + [t["titulo"] for t in templates]
    area_escolhida = st.selectbox("Área", nomes_areas)

checklists = checklists_do_dia(data_ref)
if area_escolhida != "Todas as áreas":
    checklists = [c for c in checklists if c["checklist_templates"]["titulo"] == area_escolhida]

respostas = respostas_por_data(data_ref)
if area_escolhida != "Todas as áreas":
    respostas = [
        r for r in respostas
        if r["checklists"]["checklist_templates"]["titulo"] == area_escolhida
    ]

# ---------------------------------------------------------------------
# Cards (métricas do dia)
# ---------------------------------------------------------------------
n_templates = len(templates) if area_escolhida == "Todas as áreas" else 1
esperados = n_templates * 3  # 3 turnos por dia
criados = len(checklists)
completos = sum(1 for c in checklists if c["status"] == "completo")
nao_iniciados = max(esperados - criados, 0)

contagem_resp = Counter(r["resposta"] for r in respostas if r["resposta"])
sim, nao, na = contagem_resp.get("Sim", 0), contagem_resp.get("Não", 0), contagem_resp.get("N/A", 0)
base_conformidade = sim + nao
conformidade = (sim / base_conformidade * 100) if base_conformidade else None

criticas_nao = sum(
    1 for r in respostas
    if r["resposta"] == "Não" and r["checklist_template_itens"].get("criticidade") == "critica"
)

pendencias_sem_comentario = sum(
    1 for c in checklists
    if c["status"] != "completo" and not (c.get("comentario") or "").strip()
    and any(r["resposta"] == "Não" for r in respostas if r["checklist_id"] == c["id"])
)

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Checklists esperados", esperados)
c2.metric("Concluídos", completos, delta=f"{criados - completos} em andamento" if criados > completos else None)
c3.metric("Não iniciados", nao_iniciados)
c4.metric("Conformidade (Sim)", f"{conformidade:.0f}%" if conformidade is not None else "—")
c5.metric("Pendências sem comentário", pendencias_sem_comentario)
c6.metric("'Não' em itens críticos", criticas_nao, delta_color="inverse")

st.divider()

# ---------------------------------------------------------------------
# Tabela de checklists do dia
# ---------------------------------------------------------------------
st.subheader("Checklists do dia")
linhas = []
if not checklists:
    st.info("Nenhum checklist iniciado para essa data/área ainda.")
else:
    ids_usuarios = tuple(
        uid for c in checklists for uid in (c.get("colaborador_id"), c.get("supervisor_id"))
    )
    nomes = nomes_usuarios(ids_usuarios)

    linhas = [
        {
            "Área": c["checklist_templates"]["area"],
            "Turno": c["turnos"]["nome"],
            "Status": {"completo": "✅ Completo", "em_andamento": "🟡 Em andamento", "pendente": "⚪ Pendente"}[c["status"]],
            "Colaborador": nomes.get(c.get("colaborador_id"), "-"),
            "Assinado por": nomes.get(c.get("supervisor_id"), "-"),
            "Concluído em": (c.get("concluido_em") or "-")[:16].replace("T", " "),
        }
        for c in checklists
    ]
    st.dataframe(pd.DataFrame(linhas), use_container_width=True, hide_index=True)

# Exportação — apenas supervisor e master
if usuario.pode_exportar_dashboard and linhas:
    csv_buf = io.StringIO()
    pd.DataFrame(linhas).to_csv(csv_buf, index=False)
    st.download_button(
        "⬇️ Exportar CSV",
        data=csv_buf.getvalue(),
        file_name=f"checklists_{data_ref.isoformat()}.csv",
        mime="text/csv",
    )
elif not usuario.pode_exportar_dashboard:
    st.caption("Exportação disponível apenas para supervisores e master.")

st.divider()

# ---------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------
col_pizza, col_barras = st.columns(2)

with col_pizza:
    st.subheader("Distribuição das respostas")
    if sim + nao + na == 0:
        st.info("Ainda não há respostas registradas nessa data/área.")
    else:
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=["Sim", "Não", "N/A"],
                    values=[sim, nao, na],
                    hole=0.55,
                    marker=dict(colors=[COR_SIM, COR_NAO, COR_NA], line=dict(color="#fcfcfb", width=2)),
                    textinfo="label+percent",
                    textfont=dict(color="#0b0b0b", size=13),
                    sort=False,
                )
            ]
        )
        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=340,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

with col_barras:
    st.subheader("Perguntas com mais 'Não'")
    contagem_perguntas = Counter()
    for r in respostas:
        if r["resposta"] == "Não":
            pergunta = r["checklist_template_itens"]["pergunta"]
            contagem_perguntas[pergunta] += 1

    if not contagem_perguntas:
        st.info("Nenhuma resposta 'Não' registrada — ótimo sinal. ✅")
    else:
        top = contagem_perguntas.most_common(10)
        top.sort(key=lambda x: x[1])  # menor -> maior para barra horizontal de leitura natural
        rotulos = [p if len(p) <= 55 else p[:52] + "…" for p, _ in top]
        valores = [v for _, v in top]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=valores,
                    y=rotulos,
                    orientation="h",
                    marker=dict(color=COR_PENDENCIA),
                    text=valores,
                    textposition="outside",
                )
            ]
        )
        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=30),
            height=340,
            xaxis=dict(title="Ocorrências de 'Não'", showgrid=True, gridcolor="#ececeb"),
            yaxis=dict(title=""),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)
