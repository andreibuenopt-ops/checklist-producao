"""Formulário do operador — preenche o checklist do turno atual."""
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
    salvar_resposta,
)
from src.turnos import turno_e_data_referencia

st.set_page_config(page_title="Preencher Checklist", page_icon="📋", layout="centered")

usuario = exigir_login()
st.title("📋 Preencher Checklist")

# ---------------------------------------------------------------------
# 1) Escolher a área (via QR Code ?area=slug, ou manualmente)
# ---------------------------------------------------------------------
slug = st.query_params.get("area")
template = buscar_template_por_slug(slug) if slug else None

if not template:
    templates = listar_templates()
    if not templates:
        st.warning("Nenhum checklist cadastrado ainda.")
        st.stop()
    opcoes = {t["titulo"]: t for t in templates}
    escolha = st.selectbox("Selecione a área / checklist", list(opcoes.keys()))
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
    st.success("Este checklist já foi concluído e assinado pelo supervisor. ✅")
    nomes = nomes_usuarios((checklist.get("colaborador_id"), checklist.get("supervisor_id")))
    col1, col2 = st.columns(2)
    col1.metric("Colaborador", nomes.get(checklist.get("colaborador_id"), "-"))
    col2.metric("Supervisor", nomes.get(checklist.get("supervisor_id"), "-"))
    st.stop()

itens = listar_itens(template["id"])
horarios = listar_horarios(template["id"], turno.turno_id)
respostas_salvas = listar_respostas(checklist["id"])

if not itens or not horarios:
    st.error("Este modelo de checklist ainda não tem perguntas/horários cadastrados.")
    st.stop()

st.divider()

# ---------------------------------------------------------------------
# 2) Grade de perguntas x horários (rondas do turno)
# ---------------------------------------------------------------------
OPCOES = ["", "Sim", "Não", "N/A"]
tem_nao = False
faltando = 0

for horario in horarios:
    st.subheader(f"🕒 Ronda das {horario['horario'][:5]}")
    for item in itens:
        chave = f"resp_{checklist['id']}_{item['id']}_{horario['id']}"
        valor_atual = respostas_salvas.get((item["id"], horario["id"]), "")
        idx = OPCOES.index(valor_atual) if valor_atual in OPCOES else 0

        resposta = st.radio(
            item["pergunta"],
            OPCOES,
            index=idx,
            key=chave,
            horizontal=True,
            format_func=lambda v: "Selecione" if v == "" else v,
        )
        if resposta and resposta != valor_atual:
            salvar_resposta(checklist["id"], item["id"], horario["id"], resposta, usuario.id)
            respostas_salvas[(item["id"], horario["id"])] = resposta

        if resposta == "Não":
            tem_nao = True
        if not resposta:
            faltando += 1
    st.markdown("---")

# ---------------------------------------------------------------------
# 3) Comentários do turno (obrigatório se alguma resposta = Não)
# ---------------------------------------------------------------------
comentario = st.text_area(
    "Comentários"
    + (" — obrigatório: existe(m) resposta(s) 'Não' acima" if tem_nao else " (opcional)"),
    value=checklist.get("comentario", "") or "",
    help="Explique a situação: se foi resolvido, como foi resolvido, ou se ficará pendente.",
)

st.caption(f"{faltando} pergunta(s) ainda sem resposta." if faltando else "Todas as perguntas respondidas. ✅")

# ---------------------------------------------------------------------
# 4) Assinatura do supervisor e conclusão
# ---------------------------------------------------------------------
st.divider()
st.subheader("✍️ Assinatura do supervisor")
st.caption("O checklist só é considerado concluído após a confirmação do supervisor.")

with st.form("form_concluir"):
    identificador_sup = st.text_input("E-mail ou matrícula do supervisor")
    senha_sup = st.text_input("Senha do supervisor", type="password")
    concluir = st.form_submit_button("Concluir checklist", type="primary", use_container_width=True)

if concluir:
    if faltando:
        st.error(f"Ainda faltam {faltando} pergunta(s) sem resposta.")
    elif tem_nao and not comentario.strip():
        st.error("Existe(m) resposta(s) 'Não' — o comentário é obrigatório.")
    else:
        supervisor, erro = autenticar(identificador_sup, senha_sup)
        if not supervisor:
            st.error(erro or "Não foi possível validar o supervisor.")
        elif not supervisor.eh_supervisor_ou_admin:
            st.error("Esse usuário não tem permissão de supervisor.")
        else:
            concluir_checklist(checklist["id"], supervisor.id, comentario.strip())
            st.success(f"Checklist concluído e assinado por {supervisor.nome}. ✅")
            st.balloons()
            st.rerun()
