"""Formulário do operador — preenche o checklist do turno atual."""
from collections import Counter
from itertools import groupby

import streamlit as st

from src.auth import autenticar, exigir_login
from src.models import (
    buscar_checklist,
    buscar_template_por_slug,
    concluir_checklist,
    definir_colaborador,
    listar_horarios,
    listar_itens,
    listar_respostas,
    listar_templates,
    nomes_usuarios,
    obter_ou_criar_checklist,
    salvar_respostas_em_lote,
)
from src.turnos import turno_e_data_referencia
from src.tema import aplicar_tema
from src.sidebar import mostrar_usuario_logado

st.set_page_config(page_title="Preencher Checklist", page_icon="📋", layout="centered")

usuario = exigir_login()
aplicar_tema()
mostrar_usuario_logado(usuario)
st.title("📋 Preencher Checklist")
st.caption(f"Preenchendo como **{usuario.nome}** · {usuario.papel.capitalize()}")

# ---------------------------------------------------------------------
# 1) Escolher a área (via QR Code ?area=slug, ou manualmente por setor
#    — manual só disponível pra supervisor/coordenação/master; produção
#    é obrigada a vir de um QR Code fixo na área)
# ---------------------------------------------------------------------
slug = st.query_params.get("area")
template = buscar_template_por_slug(slug) if slug else None

if not template:
    if not usuario.pode_escolher_checklist_manualmente:
        st.error("📷 Escaneie o QR Code fixado na área para abrir o checklist correspondente.")
        st.info("Seu nível de acesso (Produção) só permite preencher pelo QR Code — não é possível escolher manualmente.")
        st.stop()

    templates = listar_templates()
    if not templates:
        st.warning("Nenhum checklist cadastrado ainda.")
        st.stop()

    chave_setor = lambda t: (t.get("setores_processo") or {}).get("nome", "Outros")
    grupos = {setor: list(itens) for setor, itens in groupby(templates, key=chave_setor)}
    setor_escolhido = st.selectbox("Setor do processo", list(grupos.keys()))
    opcoes = {t["titulo"]: t for t in grupos[setor_escolhido]}
    escolha = st.selectbox("Checklist", list(opcoes.keys()))
    template = opcoes[escolha]

turno = turno_e_data_referencia()
st.caption(
    f"**{template['area']}** · {template['codigo']} · "
    f"Turno **{turno.nome}** · Data de referência **{turno.data_referencia.strftime('%d/%m/%Y')}**"
)

checklist = obter_ou_criar_checklist(template["id"], turno.turno_id, turno.data_referencia)
definir_colaborador(checklist["id"], usuario.id)
checklist = buscar_checklist(checklist["id"])  # recarrega com colaborador já setado

if checklist["status"] == "completo":
    st.success("Este checklist já foi concluído e assinado. ✅")
    nomes = nomes_usuarios((checklist.get("colaborador_id"), checklist.get("supervisor_id")))
    col1, col2 = st.columns(2)
    col1.metric("Colaborador", nomes.get(checklist.get("colaborador_id"), "-"))
    col2.metric("Assinado por", nomes.get(checklist.get("supervisor_id"), "-"))
    st.stop()

itens = listar_itens(template["id"])
horarios = listar_horarios(template["id"], turno.turno_id)
respostas_salvas = listar_respostas(checklist["id"])

if not itens or not horarios:
    st.error("Este modelo de checklist ainda não tem perguntas/horário cadastrados.")
    st.stop()

st.divider()

# ---------------------------------------------------------------------
# 2) Perguntas x horário de checagem do turno
# Preenche tudo localmente primeiro — nada é gravado no banco a cada
# clique (isso que travava a tela). Só grava quando aperta "Atualizar".
# ---------------------------------------------------------------------
ICONE_CRITICIDADE = {"critica": "🔴", "alta": "🟠", "media": "⚪"}
ICONES_RESPOSTA = {"Sim": "✅ Sim", "Não": "❌ Não", "N/A": "➖ N/A"}
OPCOES = ["Sim", "Não", "N/A"]
tem_nao = False
faltando = 0
mudancas = []  # só o que difere do que já está salvo, pra gravar em lote

for horario in horarios:
    st.subheader(f"🕒 Ronda das {horario['horario'][:5]}")
    for item in itens:
        chave = f"resp_{checklist['id']}_{item['id']}_{horario['id']}"
        valor_atual = respostas_salvas.get((item["id"], horario["id"]))

        icone = ICONE_CRITICIDADE.get(item.get("criticidade", "media"), "⚪")
        st.markdown(f"{icone} **{item['pergunta']}**")
        resposta = st.segmented_control(
            "Resposta",
            OPCOES,
            format_func=lambda v: ICONES_RESPOSTA[v],
            default=valor_atual if valor_atual in OPCOES else None,
            key=chave,
            label_visibility="collapsed",
        )

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
    st.markdown("---")

col_atualizar, col_status = st.columns([1, 3])
if col_atualizar.button("💾 Atualizar respostas", type="primary", use_container_width=True):
    qtd_salva = salvar_respostas_em_lote(mudancas)
    for m in mudancas:
        respostas_salvas[(m["item_id"], m["horario_id"])] = m["resposta"]

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

with col_status:
    st.caption(f"{faltando} pergunta(s) ainda sem resposta." if faltando else "Todas as perguntas respondidas. ✅")

# ---------------------------------------------------------------------
# 3) Comentários do turno (obrigatório se alguma resposta = Não)
# ---------------------------------------------------------------------
comentario = st.text_area(
    "Comentários"
    + (" — obrigatório: existe(m) resposta(s) 'Não' acima" if tem_nao else " (opcional)"),
    value=checklist.get("comentario", "") or "",
    help="Explique a situação: se foi resolvido, como foi resolvido, ou se ficará pendente.",
)

# ---------------------------------------------------------------------
# 4) Assinatura (supervisor, coordenação ou master) e conclusão
# ---------------------------------------------------------------------
st.divider()
st.subheader("✍️ Assinatura de conclusão")
st.warning(
    "⚠️ **Depois de concluído e assinado, este checklist não pode mais ser editado.** "
    "Confira todas as respostas com atenção antes de assinar — a dupla checagem "
    "da informação é importante."
)
st.caption("O checklist só é considerado concluído após a confirmação de um supervisor, coordenador ou master.")

with st.form("form_concluir"):
    identificador_sup = st.text_input("E-mail ou matrícula de quem assina")
    senha_sup = st.text_input("Senha", type="password")
    concluir = st.form_submit_button("Concluir checklist", type="primary", use_container_width=True)

if concluir:
    # Salva qualquer alteração pendente antes de validar — evita perder
    # resposta por esquecer de apertar "Atualizar" antes de concluir.
    if mudancas:
        salvar_respostas_em_lote(mudancas)

    if faltando:
        st.error(f"Ainda faltam {faltando} pergunta(s) sem resposta.")
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
            st.success(f"Checklist concluído e assinado por {assinante.nome}. ✅")
            st.balloons()
            st.rerun()
