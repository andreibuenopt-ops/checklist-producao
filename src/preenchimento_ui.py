"""Renderiza o formulário de preenchimento de um checklist já resolvido
(template já identificado — por slug do QR Code ou escolha manual).

Usado por dois pontos de entrada:
- app.py, quando a URL já chega com ?area=slug (QR Code) — renderiza
  DIRETO ali, sem trocar de página. Isso é proposital: st.switch_page()
  tem um bug conhecido do Streamlit (streamlit/streamlit#9050) que apaga
  o parâmetro ?area= da URL do navegador durante a troca de página,
  fazendo a tela de preenchimento não saber mais qual checklist abrir.
- pages/1_📋_Preencher_Checklist.py, para quem chega por navegação manual
  (sidebar) — aí sim é uma página normal, sem esse problema.

IMPORTANTE sobre o formulário de respostas: as perguntas ficam dentro de
um único st.form(). Isso é proposital — sem form, CADA clique num chip
Sim/Não/N-A dispara uma reexecução inteira da página (o indicador "Stop"
piscando no topo do navegador a cada toque), mesmo sem gravar nada no
banco. Dentro de um form, nenhum clique dispara nada — só quando aperta
"Atualizar respostas" é que tudo é processado de uma vez (confirmado por
teste com AppTest do Streamlit: segmented_control funciona normalmente
dentro de form). É o mesmo princípio de "só recalcula quando confirma",
como no projeto da carta Gantt.
"""
from collections import Counter

import streamlit as st

from src.auth import autenticar
from src.models import (
    buscar_checklist,
    concluir_checklist,
    definir_colaborador,
    listar_horarios,
    listar_itens,
    listar_respostas,
    nomes_usuarios,
    obter_checklist_completo,
    obter_logo_bytes_com_fallback,
    obter_ou_criar_checklist,
    salvar_respostas_em_lote,
)
from src.pdf_checklist import gerar_pdf_checklist
from src.turnos import turno_e_data_referencia


def renderizar_preenchimento(usuario, template: dict):
    turno = turno_e_data_referencia()
    st.caption(
        f"**{template['area']}** · {template['codigo']} · "
        f"Turno **{turno.nome}** · Data de referência **{turno.data_referencia.strftime('%d/%m/%Y')}**"
    )

    checklist = obter_ou_criar_checklist(template["id"], turno.turno_id, turno.data_referencia)
    definir_colaborador(checklist["id"], usuario.id)
    checklist = buscar_checklist(checklist["id"])  # recarrega com colaborador já setado

    if checklist["status"] == "completo":
        # Tira o ?area= da URL — reabrir essa mesma aba depois não mostra
        # mais esse checklist antigo (só limpa a URL, não é controle de
        # acesso: login continua sendo a proteção real).
        if "area" in st.query_params:
            del st.query_params["area"]
        st.success("Este checklist já foi concluído e assinado. ✅")
        nomes = nomes_usuarios((checklist.get("colaborador_id"), checklist.get("supervisor_id")))
        col1, col2 = st.columns(2)
        col1.metric("Colaborador", nomes.get(checklist.get("colaborador_id"), "-"))
        col2.metric("Assinado por", nomes.get(checklist.get("supervisor_id"), "-"))

        dados_completos = obter_checklist_completo(checklist["id"])
        if dados_completos:
            pdf_bytes = gerar_pdf_checklist(dados_completos, obter_logo_bytes_com_fallback())
            st.download_button(
                "⬇️ Exportar PDF deste checklist",
                data=pdf_bytes,
                file_name=f"checklist_{checklist['id']}.pdf",
                mime="application/pdf",
            )
        return

    itens = listar_itens(template["id"])
    horarios = listar_horarios(template["id"], turno.turno_id)
    respostas_salvas = listar_respostas(checklist["id"])

    if not itens or not horarios:
        st.error("Este modelo de checklist ainda não tem perguntas/horário cadastrados.")
        return

    st.divider()

    ICONE_CRITICIDADE = {"critica": "🔴", "alta": "🟠", "media": "⚪"}
    ICONES_RESPOSTA = {"Sim": "✅ Sim", "Não": "❌ Não", "N/A": "➖ N/A"}
    OPCOES = ["Sim", "Não", "N/A"]

    # Estado de tem_nao/faltando só é recalculado quando "Atualizar
    # respostas" é confirmado — por isso fica em session_state, não numa
    # variável local (a página não reroda a cada clique dentro do form).
    chave_estado = f"estado_preenchimento_{checklist['id']}"
    if chave_estado not in st.session_state:
        st.session_state[chave_estado] = {
            "tem_nao": any(v == "Não" for v in respostas_salvas.values()),
            "faltando": sum(
                1 for horario in horarios for item in itens
                if (item["id"], horario["id"]) not in respostas_salvas
            ),
        }

    # -------------------------------------------------------------
    # Perguntas x horário de checagem do turno, dentro de um único
    # formulário — ver explicação no topo do arquivo.
    # -------------------------------------------------------------
    with st.form(f"form_respostas_{checklist['id']}"):
        for horario in horarios:
            st.subheader(f"🕒 Ronda das {horario['horario'][:5]}")
            for item in itens:
                chave = f"resp_{checklist['id']}_{item['id']}_{horario['id']}"
                valor_atual = respostas_salvas.get((item["id"], horario["id"]))

                icone = ICONE_CRITICIDADE.get(item.get("criticidade", "media"), "⚪")
                st.markdown(f"{icone} **{item['pergunta']}**")
                st.segmented_control(
                    "Resposta",
                    OPCOES,
                    format_func=lambda v: ICONES_RESPOSTA[v],
                    default=valor_atual if valor_atual in OPCOES else None,
                    key=chave,
                    label_visibility="collapsed",
                )
            st.markdown("---")

        atualizar_clicado = st.form_submit_button(
            "💾 Atualizar respostas", type="primary", use_container_width=True,
        )

    if atualizar_clicado:
        mudancas = []
        tem_nao = False
        faltando = 0
        for horario in horarios:
            for item in itens:
                chave = f"resp_{checklist['id']}_{item['id']}_{horario['id']}"
                resposta = st.session_state.get(chave)
                valor_atual = respostas_salvas.get((item["id"], horario["id"]))

                if resposta and resposta != valor_atual:
                    mudancas.append({
                        "checklist_id": checklist["id"], "item_id": item["id"],
                        "horario_id": horario["id"], "resposta": resposta,
                        "respondido_por": usuario.id,
                    })
                if resposta == "Não":
                    tem_nao = True
                if not resposta:
                    faltando += 1

        qtd_salva = salvar_respostas_em_lote(mudancas)
        for m in mudancas:
            respostas_salvas[(m["item_id"], m["horario_id"])] = m["resposta"]
        st.session_state[chave_estado] = {"tem_nao": tem_nao, "faltando": faltando}

        if qtd_salva == 0:
            st.info("Nenhuma alteração nova para salvar.")
        else:
            contagem = Counter(m["resposta"] for m in mudancas)
            resumo = f"{qtd_salva} resposta(s) salva(s): "
            resumo += ", ".join(f"{v} {k}" for k, v in contagem.items())
            st.success(resumo)
            if contagem.get("Não"):
                st.warning(
                    f"⚠️ {contagem['Não']} item(ns) marcado(s) como **Não** (não conforme) — "
                    "detalhe a situação no campo de Comentários abaixo antes de concluir."
                )

    estado = st.session_state[chave_estado]
    tem_nao = estado["tem_nao"]
    faltando = estado["faltando"]

    st.caption(
        (f"{faltando} pergunta(s) ainda sem resposta." if faltando else "Todas as perguntas respondidas. ✅")
        + " (contagem atualizada só depois de apertar \"Atualizar respostas\" acima)"
    )

    # -------------------------------------------------------------
    # Comentários (obrigatório se alguma resposta = Não)
    # -------------------------------------------------------------
    comentario = st.text_area(
        "Comentários"
        + (" — obrigatório: existe(m) resposta(s) 'Não' acima" if tem_nao else " (opcional)"),
        value=checklist.get("comentario", "") or "",
        help="Explique a situação: se foi resolvido, como foi resolvido, ou se ficará pendente.",
        key=f"comentario_{checklist['id']}",
    )

    # -------------------------------------------------------------
    # Assinatura (supervisor, coordenação ou master) e conclusão
    # -------------------------------------------------------------
    st.divider()
    st.subheader("✍️ Assinatura de conclusão")
    st.warning(
        "⚠️ **Depois de concluído e assinado, este checklist não pode mais ser editado.** "
        "Confira todas as respostas com atenção antes de assinar — a dupla checagem "
        "da informação é importante. Aperte \"Atualizar respostas\" antes de concluir, "
        "pra garantir que tudo que você marcou foi confirmado."
    )
    st.caption("O checklist só é considerado concluído após a confirmação de um supervisor, coordenador ou master.")

    with st.form(f"form_concluir_{checklist['id']}"):
        identificador_sup = st.text_input("E-mail ou matrícula de quem assina")
        senha_sup = st.text_input("Senha", type="password")
        concluir = st.form_submit_button("Concluir checklist", type="primary", use_container_width=True)

    if concluir:
        if faltando:
            st.error(f"Ainda faltam {faltando} pergunta(s) sem resposta. Confirme com \"Atualizar respostas\" primeiro.")
        elif tem_nao and not comentario.strip():
            st.error("Existe(m) resposta(s) 'Não' — o comentário é obrigatório.")
        else:
            assinante, erro = autenticar(identificador_sup, senha_sup)
            if not assinante:
                st.error(erro or "Não foi possível validar o usuário.")
            elif not assinante.pode_assinar_checklist:
                st.error("Esse usuário não tem permissão para assinar checklists.")
            else:
                concluir_checklist(checklist["id"], assinante.id, comentario.strip())
                if "area" in st.query_params:
                    del st.query_params["area"]
                st.success(f"Checklist concluído e assinado por {assinante.nome}. ✅")
                st.balloons()
                st.rerun()
