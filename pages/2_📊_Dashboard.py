"""Dashboard — resultados do dia atual ou de qualquer dia passado."""
import io
import time
from collections import Counter

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.auth import exigir_login
from src.models import (
    checklists_do_dia,
    horarios_do_turno,
    rondas_com_resposta,
    listar_templates,
    dados_usuarios,
    nomes_usuarios,
    obter_checklist_completo,
    obter_logo_bytes_com_fallback,
    respostas_por_data,
)
from src.historico_ui import botao_pdf_checklist, renderizar_checklist_folha, renderizar_checklist_somente_leitura
from src.atrasos import formatar_atraso, rondas_pendentes
from src.pdf_dashboard import gerar_pdf_dashboard
from src.turnos import agora_local, formatar_datahora_local, turno_e_data_referencia
from src.tema import aplicar_tema, desativar_traducao_automatica
from src.sidebar import mostrar_usuario_logado

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

desativar_traducao_automatica()
usuario = exigir_login()
aplicar_tema(usuario)
mostrar_usuario_logado(usuario)

if not usuario.pode_ver_dashboard:
    st.error("Seu nível de acesso (produção) não permite visualizar o dashboard.")
    st.stop()

st.title("📊 Dashboard de Checklists")

# Paleta de status (mesmos papéis em todo o app: Sim=good, Não=critical, N/A=neutro)
COR_SIM, COR_NAO, COR_NA = "#0ca30c", "#d03b3b", "#8a8a86"
COR_PENDENCIA = "#d03b3b"

# ---------------------------------------------------------------------
# Atualização automática (só no dia de hoje): quem acompanha a tela vê o
# andamento sem apertar F5 e consegue cobrar no turno certo. As rondas são de
# 2 em 2 horas; atualiza a cada 15 min (nunca passa de 2 h defasado).
# ---------------------------------------------------------------------
INTERVALO_ATUALIZACAO = "15m"
_SEGUNDOS_MIN = 14 * 60

st.session_state["_dash_carregado_em"] = time.time()


@st.fragment(run_every=INTERVALO_ATUALIZACAO)
def _barra_atualizacao():
    # O timer só repete este trecho; se já passou o intervalo desde a última
    # carga completa, recarrega a página inteira (busca dados novos).
    if time.time() - st.session_state.get("_dash_carregado_em", time.time()) >= _SEGUNDOS_MIN:
        st.cache_data.clear()
        st.rerun(scope="app")
    col_txt, col_btn = st.columns([4, 1])
    col_txt.caption(f"🕒 Atualizado às {agora_local().strftime('%H:%M')} · atualiza sozinho a cada 15 min")
    if col_btn.button("🔄 Atualizar agora", use_container_width=True):
        st.cache_data.clear()
        st.rerun(scope="app")


_barra_atualizacao()

# ---------------------------------------------------------------------
# Filtros
# ---------------------------------------------------------------------
templates = listar_templates()
col_data, col_tipo, col_area = st.columns([1, 1, 2])
with col_data:
    data_ref = st.date_input("Data (dia de produção)", value=turno_e_data_referencia().data_referencia, max_value=turno_e_data_referencia().data_referencia)
with col_tipo:
    filtro_tipo_area = st.radio("Área", ["Todos", "🏭 Interno", "🌳 Externo"], key="filtro_tipo_area_dash")
if filtro_tipo_area != "Todos":
    alvo_tipo_area = "interno" if "Interno" in filtro_tipo_area else "externo"
    templates = [t for t in templates if t.get("tipo_area", "interno") == alvo_tipo_area]
with col_area:
    nomes_areas = ["Todas as áreas"] + [t["titulo"] for t in templates]
    area_escolhida = st.selectbox("Área", nomes_areas)

checklists_todos = checklists_do_dia(data_ref)
if filtro_tipo_area != "Todos":
    checklists_todos = [
        c for c in checklists_todos
        if (c["checklist_templates"] or {}).get("tipo_area", "interno") == alvo_tipo_area
    ]
if area_escolhida != "Todas as áreas":
    checklists_todos = [c for c in checklists_todos if c["checklist_templates"]["titulo"] == area_escolhida]

# Só o que foi assinado conta ou aparece em qualquer lugar — em andamento
# não debita de "não iniciados" nem entra na tabela/exportação.
checklists = [c for c in checklists_todos if c["status"] == "completo"]
ids_completos = {c["id"] for c in checklists}

@st.cache_data(ttl=120, show_spinner=False)
def _respostas_do_dia(dia):
    # Um dia tem milhares de respostas — cache de 2 min poupa o tráfego do Supabase.
    return respostas_por_data(dia)


respostas = _respostas_do_dia(data_ref)
if area_escolhida != "Todas as áreas":
    respostas = [
        r for r in respostas
        if r["checklists"]["checklist_templates"]["titulo"] == area_escolhida
    ]
respostas = [r for r in respostas if r["checklist_id"] in ids_completos]

# ---------------------------------------------------------------------
# Cards (métricas do dia)
# ---------------------------------------------------------------------
n_templates = len(templates) if area_escolhida == "Todas as áreas" else 1
esperados = n_templates * 3  # 3 turnos por dia
completos = len(checklists)
nao_iniciados = max(esperados - completos, 0)

contagem_resp = Counter(r["resposta"] for r in respostas if r["resposta"])
sim, nao, na = contagem_resp.get("Sim", 0), contagem_resp.get("Não", 0), contagem_resp.get("N/A", 0)
base_conformidade = sim + nao
conformidade = (sim / base_conformidade * 100) if base_conformidade else None

criticas_nao = sum(
    1 for r in respostas
    if r["resposta"] == "Não" and r["checklist_template_itens"].get("criticidade") == "critica"
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Checklists esperados", esperados)
c2.metric("Concluídos", completos)
c3.metric("Não iniciados", nao_iniciados)
c4.metric("Conformidade (Sim)", f"{conformidade:.0f}%" if conformidade is not None else "—")
c5.metric("'Não' em itens críticos", criticas_nao, delta_color="inverse")

# Quem ainda não assinou no turno em andamento (pra cobrar na hora certa)
_ref = turno_e_data_referencia()
if data_ref == _ref.data_referencia:
    _assinados = {
        c["checklist_templates"]["titulo"] for c in checklists_todos
        if c["status"] == "completo" and c["turno_id"] == _ref.turno_id
    }
    _faltam = [t["titulo"] for t in templates if t["titulo"] not in _assinados]
    if area_escolhida != "Todas as áreas":
        _faltam = [t for t in _faltam if t == area_escolhida]
    # Rondas em atraso (horário já passou e nada foi respondido)
    _ids_turno = [c["id"] for c in checklists_todos if c["turno_id"] == _ref.turno_id]
    _pend = rondas_pendentes(
        templates, horarios_do_turno(_ref.turno_id), checklists_todos,
        rondas_com_resposta(_ids_turno), _ref.data_referencia, _ref.turno_id, _ref.nome, agora_local(),
    )
    _atrasadas = [p for p in _pend if p["atrasada"]]
    _na_hora = [p for p in _pend if not p["atrasada"]]
    if _atrasadas:
        with st.expander(f"🚨 Rondas em ATRASO no turno atual ({_ref.nome}) — {len(_atrasadas)}", expanded=True):
            for p in _atrasadas:
                st.write(f"• **{p['titulo']}** — ronda das {p['horario']} · atrasada {formatar_atraso(p['atraso_min'])}"
                         + ("" if p["iniciado"] else " · não iniciado"))
    if _na_hora:
        with st.expander(f"🕒 Rondas na hora de fazer (ainda dentro da margem) — {len(_na_hora)}", expanded=False):
            for p in _na_hora:
                st.write(f"• {p['titulo']} — ronda das {p['horario']}")
    if not _pend:
        st.success("Nenhuma ronda pendente no turno atual. ✅")
    if _faltam:
        with st.expander(f"⏳ Ainda sem assinatura no turno atual ({_ref.nome}) — {len(_faltam)}", expanded=False):
            for t in _faltam:
                st.write(f"• {t}")
    else:
        st.success(f"Todos os checklists do turno atual ({_ref.nome}) já foram assinados. ✅")

st.divider()

# ---------------------------------------------------------------------
# Tabela de checklists do dia (só os concluídos)
# ---------------------------------------------------------------------
st.subheader("Checklists do dia")
linhas = []
if not checklists:
    st.info("Nenhum checklist concluído para essa data/área ainda.")
else:
    ids_usuarios = tuple(
        uid for c in checklists for uid in (c.get("colaborador_id"), c.get("supervisor_id"))
    )
    nomes = nomes_usuarios(ids_usuarios)
    pessoas = dados_usuarios(ids_usuarios)

    linhas = [
        {
            "Área": c["checklist_templates"]["area"],
            "Turno": c["turnos"]["nome"],
            "Status": (
                "⚠️ Completo (incompleto)" if c.get("incompleto") and c["status"] == "completo"
                else {"completo": "✅ Completo", "em_andamento": "🟡 Em andamento", "pendente": "⚪ Pendente"}[c["status"]]
            ),
            "Colaborador": nomes.get(c.get("colaborador_id"), "-"),
            "Turma": (pessoas.get(c.get("colaborador_id")) or {}).get("turma") or "-",
            "Assinado por": nomes.get(c.get("supervisor_id"), "-"),
            "Concluído em": formatar_datahora_local(c.get("concluido_em")),
        }
        for c in checklists
    ]
    st.dataframe(pd.DataFrame(linhas), use_container_width=True, hide_index=True)

# Exportação — apenas supervisor, administrador e master
if usuario.pode_exportar_dashboard and linhas:
    col_csv, col_pdf_dash = st.columns(2)

    csv_buf = io.StringIO()
    pd.DataFrame(linhas).to_csv(csv_buf, index=False)
    col_csv.download_button(
        "⬇️ Exportar CSV",
        data=csv_buf.getvalue(),
        file_name=f"checklists_{data_ref.isoformat()}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    def _pdf_dashboard():
        return gerar_pdf_dashboard(
        data_ref, area_escolhida,
        cards={
            "esperados": esperados, "completos": completos, "nao_iniciados": nao_iniciados,
            "conformidade": conformidade,
            "criticas_nao": criticas_nao,
        },
        linhas=linhas,
        contagem_resp=dict(contagem_resp),
        top_perguntas_nao=list(Counter(
            r["checklist_template_itens"]["pergunta"] for r in respostas if r["resposta"] == "Não"
        ).most_common(10)),
        logo_bytes=obter_logo_bytes_com_fallback(),
        )
    col_pdf_dash.download_button(
        "⬇️ Exportar PDF (resumo)",
        data=_pdf_dashboard, on_click="ignore",
        file_name=f"dashboard_{data_ref.isoformat()}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
elif not usuario.pode_exportar_dashboard:
    st.caption("Exportação disponível apenas para supervisores, administradores e master.")

# Exportar um checklist específico em PDF (com todas as respostas)
if checklists:
    st.divider()
    st.subheader("Ver um checklist específico")
    ICONE_STATUS = {"completo": "✅", "em_andamento": "🟡", "pendente": "⚪"}
    mapa_checklists = {
        f"{c['checklist_templates']['titulo']} · {c['turnos']['nome']} · {ICONE_STATUS[c['status']]}": c["id"]
        for c in checklists
    }
    checklist_escolhido = st.selectbox("Checklist", list(mapa_checklists.keys()))
    renderizar_checklist_folha(obter_checklist_completo(mapa_checklists[checklist_escolhido], com_bytes=False))
    st.caption("Quer uma cópia? Gere o PDF (opcional):")
    botao_pdf_checklist(mapa_checklists[checklist_escolhido], obter_logo_bytes_com_fallback(), obter_checklist_completo, "dash")

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
