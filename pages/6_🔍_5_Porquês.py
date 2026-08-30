"""Análise de causa raiz — 5 Porquês.

ESTRUTURA PROVISÓRIA. Criada agora conforme solicitado; especificação
final (campos, fluxo, permissões exatas) ainda será enviada e pode
substituir este conteúdo. Nada mais no sistema depende desta página.
"""
import streamlit as st

from src.auth import exigir_login
from src.models import (
    atualizar_analise_5_porques,
    criar_analise_5_porques,
    listar_analises_5_porques,
    respostas_nao_criticas_sem_analise,
)

st.set_page_config(page_title="5 Porquês", page_icon="🔍", layout="wide")

usuario = exigir_login()
st.title("🔍 Análise 5 Porquês")
st.caption("Estrutura provisória — aguardando especificação final para refinar campos e fluxo.")

tab_abertas, tab_nova, tab_historico = st.tabs(["🟡 Em aberto", "➕ Nova análise", "📋 Histórico"])

# ---------------------------------------------------------------------
with tab_nova:
    st.subheader("'Não' em itens críticos sem análise (últimos 30 dias)")
    pendentes = respostas_nao_criticas_sem_analise(dias=30)

    if not pendentes:
        st.info("Nenhuma resposta 'Não' crítica pendente de análise no período.")
    else:
        for r in pendentes:
            item = r["checklist_template_itens"]
            checklist = r["checklists"]
            template = checklist["checklist_templates"]
            with st.container(border=True):
                st.write(f"🔴 **{item['pergunta']}**")
                st.caption(
                    f"{template['titulo']} ({template['area']}) · "
                    f"{checklist['data']} · registrado em {r['respondido_em'][:16].replace('T', ' ')}"
                )
                if usuario.pode_assinar_checklist and st.button("Abrir análise", key=f"abrir_{r['id']}"):
                    criar_analise_5_porques(
                        r["id"], checklist["template_id"], item["pergunta"], usuario.id,
                    )
                    st.success("Análise criada. Continue em '🟡 Em aberto'.")
                    st.rerun()

# ---------------------------------------------------------------------
with tab_abertas:
    abertas = [a for a in listar_analises_5_porques() if a["status"] != "concluida"]
    if not abertas:
        st.info("Nenhuma análise em aberto.")

    for a in abertas:
        titulo_template = (a.get("checklist_templates") or {}).get("titulo", "—")
        with st.container(border=True):
            st.write(f"**{a['problema']}**")
            st.caption(f"{titulo_template} · Status: {a['status']}")

            with st.form(f"form_analise_{a['id']}"):
                porque_1 = st.text_area("1º Por quê?", value=a.get("porque_1") or "")
                porque_2 = st.text_area("2º Por quê?", value=a.get("porque_2") or "")
                porque_3 = st.text_area("3º Por quê?", value=a.get("porque_3") or "")
                porque_4 = st.text_area("4º Por quê?", value=a.get("porque_4") or "")
                porque_5 = st.text_area("5º Por quê?", value=a.get("porque_5") or "")
                causa_raiz = st.text_area("Causa raiz identificada", value=a.get("causa_raiz") or "")
                acao_corretiva = st.text_area("Ação corretiva", value=a.get("acao_corretiva") or "")
                prazo = st.date_input("Prazo", value=a.get("prazo"))
                status = st.selectbox(
                    "Status", ["aberta", "em_andamento", "concluida"],
                    index=["aberta", "em_andamento", "concluida"].index(a["status"]),
                )
                if st.form_submit_button("Salvar", type="primary"):
                    atualizar_analise_5_porques(a["id"], {
                        "porque_1": porque_1, "porque_2": porque_2, "porque_3": porque_3,
                        "porque_4": porque_4, "porque_5": porque_5,
                        "causa_raiz": causa_raiz, "acao_corretiva": acao_corretiva,
                        "prazo": prazo.isoformat() if prazo else None,
                        "status": status,
                    })
                    st.success("Análise atualizada.")
                    st.rerun()

# ---------------------------------------------------------------------
with tab_historico:
    concluidas = listar_analises_5_porques(status="concluida")
    if not concluidas:
        st.info("Nenhuma análise concluída ainda.")
    for a in concluidas:
        titulo_template = (a.get("checklist_templates") or {}).get("titulo", "—")
        with st.expander(f"✅ {a['problema']} · {titulo_template}"):
            st.write(f"**Causa raiz:** {a.get('causa_raiz') or '—'}")
            st.write(f"**Ação corretiva:** {a.get('acao_corretiva') or '—'}")
            st.caption(f"Prazo: {a.get('prazo') or '—'}")
