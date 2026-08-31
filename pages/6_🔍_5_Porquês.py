"""Análise de causa raiz — Formulário 5 Porquês (Parada de Linha).

Espelha o formulário físico da Guararapes: cabeçalho da parada, descrição
do problema, tabela dos 5 porquês, causa raiz, plano de ação (múltiplas
linhas), verificação de eficácia pelo coordenador, e exportação em PDF
com o mesmo layout.
"""
from datetime import date

import streamlit as st

from src.auth import exigir_login
from src.models import (
    JANELA_MINUTOS_MAX,
    JANELA_MINUTOS_MIN,
    adicionar_acao_5_porques,
    atualizar_analise_5_porques,
    buscar_analise_5_porques,
    criar_analise_5_porques,
    listar_acoes_5_porques,
    listar_analises_5_porques,
    listar_equipamentos,
    listar_setores,
    obter_logo_bytes_com_fallback,
    registrar_verificacao_eficacia,
    remover_acao_5_porques,
    respostas_nao_criticas_sem_analise,
)
from src.pdf_5_porques import gerar_pdf_5_porques
from src.tema import aplicar_tema
from src.sidebar import mostrar_usuario_logado

st.set_page_config(page_title="5 Porquês", page_icon="🔍", layout="wide")

# Dicas de ajuda pra quem é novo em RCA — aparecem no "?" ao lado de cada
# campo. Baseado no exemplo padrão: fusível queimado → sobrecarga →
# lubrificação inadequada → bomba de óleo → eixo gasto → falta de filtro.
AJUDA_PORQUE = {
    1: (
        "**Sintoma direto** — a falha mais óbvia e imediata que aconteceu.\n\n"
        "Exemplo: \"Por que a máquina parou?\" → \"Porque o fusível queimou "
        "por causa de uma sobrecarga.\""
    ),
    2: (
        "**Falha mecânica/operacional** — o motivo técnico ou gatilho direto "
        "do 1º porquê.\n\n"
        "Exemplo: \"Por que houve sobrecarga?\" → \"Porque a lubrificação "
        "do mancal era inadequada.\""
    ),
    3: (
        "**Processo falho** — começa a se afastar da máquina em si e olhar "
        "pra rotina/regra por trás.\n\n"
        "Exemplo: \"Por que a lubrificação era inadequada?\" → \"Porque a "
        "bomba de óleo não estava bombeando óleo suficiente.\""
    ),
    4: (
        "**Falha humana/sistêmica** — examina se houve falha de manutenção "
        "ou desgaste não planejado.\n\n"
        "Exemplo: \"Por que a bomba não estava funcionando bem?\" → \"Porque "
        "o eixo da bomba estava totalmente gasto.\""
    ),
    5: (
        "**Causa raiz real** — a origem estrutural, que exige mudança "
        "definitiva de processo ou gestão (não só trocar a peça).\n\n"
        "Exemplo: \"Por que o eixo estava gasto?\" → \"Porque não havia "
        "filtro instalado na bomba, permitindo entrada de resíduos.\" "
        "(Solução definitiva: instalar filtro adequado.)"
    ),
}

usuario = exigir_login()
aplicar_tema()
mostrar_usuario_logado(usuario)
st.title("🔍 Formulário 5 Porquês — Parada de Linha")
st.caption("Preencher para paradas entre 30 minutos e 1h30min.")

tab_nova, tab_abertas, tab_historico = st.tabs(["➕ Nova análise", "🟡 Em aberto", "📋 Histórico"])

# =====================================================================
# TAB — Nova análise
# =====================================================================
with tab_nova:
    st.subheader("Atalho: partir de um 'Não' crítico já registrado")
    pendentes = respostas_nao_criticas_sem_analise(dias=30)
    origem_escolhida = None
    if pendentes:
        opcoes_origem = {"— Preencher do zero —": None}
        for r in pendentes:
            item = r["checklist_template_itens"]
            checklist = r["checklists"]
            template = checklist["checklist_templates"]
            rotulo = f"{template['titulo']} · {item['pergunta'][:50]} ({checklist['data']})"
            opcoes_origem[rotulo] = r
        escolha = st.selectbox("Origem (opcional)", list(opcoes_origem.keys()))
        origem_escolhida = opcoes_origem[escolha]
    else:
        st.caption("Nenhum 'Não' crítico pendente — pode preencher do zero abaixo.")

    st.divider()
    st.subheader("Dados da parada")

    setores = listar_setores()
    mapa_setores = {s["nome"]: s["id"] for s in setores}

    c1, c2 = st.columns(2)
    data_parada = c1.date_input("Data", value=date.today())
    setor_nome = c2.selectbox("Setor", list(mapa_setores.keys()))

    equipamentos_do_setor = listar_equipamentos(mapa_setores[setor_nome])
    opcoes_equip = [e["nome"] for e in equipamentos_do_setor] or []
    c3, c4 = st.columns(2)
    if opcoes_equip:
        equipamento = c3.selectbox("Equipamento", opcoes_equip + ["Outro (digitar)"])
        if equipamento == "Outro (digitar)":
            equipamento = c3.text_input("Nome do equipamento")
    else:
        equipamento = c3.text_input("Equipamento")

    c5, c6 = c4.columns(2)
    horas_parada = c5.number_input("Horas de parada", min_value=0, max_value=23, value=0)
    minutos_parada = c6.number_input("Minutos", min_value=0, max_value=59, value=30)
    tempo_total_minutos = horas_parada * 60 + minutos_parada

    if not (JANELA_MINUTOS_MIN <= tempo_total_minutos <= JANELA_MINUTOS_MAX):
        st.warning(
            f"⚠️ O formulário é pra paradas entre {JANELA_MINUTOS_MIN}min e "
            f"{JANELA_MINUTOS_MAX}min (1h30). Tempo informado: {horas_parada:02d}:{minutos_parada:02d}. "
            "Pode preencher mesmo assim se for o caso."
        )

    descricao_problema = st.text_area(
        "Descrição do Problema — descreva de forma objetiva o que ocorreu",
        value=(
            f"{origem_escolhida['checklist_template_itens']['pergunta']}"
            if origem_escolhida else ""
        ),
        height=100,
    )

    st.divider()
    st.subheader("Os 5 Porquês")
    st.caption("Toque no ❔ ao lado de cada campo pra ver o significado e um exemplo.")
    problema = st.text_input("Problema — O que aconteceu? (resumo)")
    porque_1 = st.text_area("1º Porquê (O Sintoma Direto) — Por que aconteceu?", height=70, help=AJUDA_PORQUE[1])
    porque_2 = st.text_area("2º Porquê (A Falha Mecânica/Operacional) — Por que isso aconteceu?", height=70, help=AJUDA_PORQUE[2])
    porque_3 = st.text_area("3º Porquê (O Processo Falho) — Por que isso aconteceu?", height=70, help=AJUDA_PORQUE[3])
    porque_4 = st.text_area("4º Porquê (A Falha Humana/Sistêmica) — Por que isso aconteceu?", height=70, help=AJUDA_PORQUE[4])
    porque_5 = st.text_area("5º Porquê (A Causa Raiz Real) — Por que isso aconteceu?", height=70, help=AJUDA_PORQUE[5])
    causa_raiz = st.text_area("Causa Raiz Identificada", height=70)

    st.divider()
    st.subheader("Plano de Ação")
    st.caption("Pode deixar em branco e adicionar as ações depois de criar a análise.")
    acao_inicial = st.text_input("Ação corretiva imediata (opcional)")
    responsavel_acao_inicial = st.text_input("Responsável pela ação")
    prazo_acao_inicial = st.date_input("Prazo", value=None)

    if st.button("Criar análise", type="primary"):
        if not equipamento or not descricao_problema.strip():
            st.error("Equipamento e descrição do problema são obrigatórios.")
        else:
            dados = {
                "data_parada": data_parada.isoformat(),
                "equipamento": equipamento,
                "setor": setor_nome,
                "responsavel_id": usuario.id,
                "tempo_parada_minutos": tempo_total_minutos,
                "descricao_problema": descricao_problema.strip(),
                "problema": problema.strip() or None,
                "porque_1": porque_1.strip() or None,
                "porque_2": porque_2.strip() or None,
                "porque_3": porque_3.strip() or None,
                "porque_4": porque_4.strip() or None,
                "porque_5": porque_5.strip() or None,
                "causa_raiz": causa_raiz.strip() or None,
            }
            if origem_escolhida:
                dados["checklist_resposta_id"] = origem_escolhida["id"]
                dados["template_id"] = origem_escolhida["checklists"]["template_id"]

            nova = criar_analise_5_porques(dados, usuario.id)

            if acao_inicial.strip():
                adicionar_acao_5_porques(
                    nova["id"], acao_inicial,
                    responsavel_acao_inicial,
                    prazo_acao_inicial.isoformat() if prazo_acao_inicial else None,
                )
            st.success("Análise criada. Continue em '🟡 Em aberto' pra adicionar mais ações ou concluir.")
            st.rerun()

# =====================================================================
# TAB — Em aberto
# =====================================================================
with tab_abertas:
    abertas = [a for a in listar_analises_5_porques() if a["status"] != "concluida"]
    if not abertas:
        st.info("Nenhuma análise em aberto.")

    for a in abertas:
        responsavel_nome = (a.get("responsavel") or {}).get("nome", "—")
        with st.container(border=True):
            st.write(f"**{a.get('problema') or a.get('descricao_problema', '')[:60]}**")
            st.caption(
                f"{a['equipamento']} · {a['setor']} · {a['data_parada']} · "
                f"Responsável: {responsavel_nome} · Status: {a['status']}"
            )

            with st.expander("Editar análise"):
                with st.form(f"form_analise_{a['id']}"):
                    problema_e = st.text_input("Problema", value=a.get("problema") or "")
                    porque_1_e = st.text_area("1º Porquê (O Sintoma Direto)", value=a.get("porque_1") or "", help=AJUDA_PORQUE[1])
                    porque_2_e = st.text_area("2º Porquê (A Falha Mecânica/Operacional)", value=a.get("porque_2") or "", help=AJUDA_PORQUE[2])
                    porque_3_e = st.text_area("3º Porquê (O Processo Falho)", value=a.get("porque_3") or "", help=AJUDA_PORQUE[3])
                    porque_4_e = st.text_area("4º Porquê (A Falha Humana/Sistêmica)", value=a.get("porque_4") or "", help=AJUDA_PORQUE[4])
                    porque_5_e = st.text_area("5º Porquê (A Causa Raiz Real)", value=a.get("porque_5") or "", help=AJUDA_PORQUE[5])
                    causa_raiz_e = st.text_area("Causa raiz", value=a.get("causa_raiz") or "")
                    if st.form_submit_button("Salvar", type="primary"):
                        atualizar_analise_5_porques(a["id"], {
                            "problema": problema_e, "porque_1": porque_1_e, "porque_2": porque_2_e,
                            "porque_3": porque_3_e, "porque_4": porque_4_e, "porque_5": porque_5_e,
                            "causa_raiz": causa_raiz_e,
                        })
                        st.success("Atualizado.")
                        st.rerun()

            st.markdown("**Plano de Ação**")
            acoes = listar_acoes_5_porques(a["id"])
            for acao in acoes:
                ac1, ac2, ac3, ac4 = st.columns([4, 2, 2, 1])
                ac1.write(acao["acao_corretiva"])
                ac2.write(acao.get("responsavel") or "-")
                ac3.write(acao.get("prazo") or "-")
                if ac4.button("🗑️", key=f"rm_acao_{acao['id']}"):
                    remover_acao_5_porques(acao["id"])
                    st.rerun()

            with st.form(f"form_nova_acao_{a['id']}", clear_on_submit=True):
                nc1, nc2, nc3 = st.columns([4, 2, 2])
                nova_acao = nc1.text_input("Nova ação corretiva")
                novo_resp = nc2.text_input("Responsável")
                novo_prazo = nc3.date_input("Prazo", value=None, key=f"prazo_{a['id']}")
                if st.form_submit_button("Adicionar ação"):
                    if nova_acao.strip():
                        adicionar_acao_5_porques(
                            a["id"], nova_acao, novo_resp,
                            novo_prazo.isoformat() if novo_prazo else None,
                        )
                        st.rerun()

            if usuario.pode_assinar_checklist:
                st.markdown("**Verificação da Eficácia** (Coordenador de produção)")
                with st.form(f"form_eficacia_{a['id']}"):
                    eficaz_opcao = st.radio("Foi eficaz?", ["Sim", "Não"], horizontal=True, key=f"ef_{a['id']}")
                    evidencias = st.text_area("Evidências", key=f"evid_{a['id']}")
                    if st.form_submit_button("Registrar verificação", type="primary"):
                        registrar_verificacao_eficacia(a["id"], eficaz_opcao == "Sim", evidencias, usuario.id)
                        if eficaz_opcao == "Não":
                            st.warning("Marcado como não eficaz — reabra a análise ou trate no Qualiex se for recorrente.")
                        st.success("Verificação registrada.")
                        st.rerun()

            analise_completa = buscar_analise_5_porques(a["id"])
            pdf_bytes = gerar_pdf_5_porques(analise_completa, acoes, obter_logo_bytes_com_fallback())
            st.download_button(
                "⬇️ Exportar PDF",
                data=pdf_bytes,
                file_name=f"5porques_{a['equipamento']}_{a['data_parada']}.pdf",
                mime="application/pdf",
                key=f"pdf_{a['id']}",
            )

# =====================================================================
# TAB — Histórico
# =====================================================================
with tab_historico:
    concluidas = listar_analises_5_porques(status="concluida")
    if not concluidas:
        st.info("Nenhuma análise concluída ainda.")
    for a in concluidas:
        responsavel_nome = (a.get("responsavel") or {}).get("nome", "—")
        with st.expander(f"✅ {a.get('problema') or a['equipamento']} · {a['setor']} · {a['data_parada']}"):
            st.write(f"**Causa raiz:** {a.get('causa_raiz') or '—'}")
            st.write(f"**Responsável:** {responsavel_nome}")
            st.caption(f"Eficaz: {'Sim' if a.get('eficaz') else 'Não' if a.get('eficaz') is False else '—'}")

            acoes = listar_acoes_5_porques(a["id"])
            analise_completa = buscar_analise_5_porques(a["id"])
            pdf_bytes = gerar_pdf_5_porques(analise_completa, acoes, obter_logo_bytes_com_fallback())
            st.download_button(
                "⬇️ Exportar PDF",
                data=pdf_bytes,
                file_name=f"5porques_{a['equipamento']}_{a['data_parada']}.pdf",
                mime="application/pdf",
                key=f"pdf_hist_{a['id']}",
            )
