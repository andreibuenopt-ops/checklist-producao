"""Painel do administrador master: usuários e checklists."""
from datetime import time

import streamlit as st

from src.auth import alternar_status, criar_usuario, exigir_login, resetar_senha
from src.models import (
    COR_PADRAO_GUARARAPES,
    adicionar_itens,
    alternar_equipamento,
    atualizar_cor_primaria,
    atualizar_logo,
    criar_equipamento,
    criar_template,
    definir_horarios_turnos,
    desativar_template,
    editar_horario,
    editar_item,
    listar_equipamentos,
    listar_horarios_todos_turnos,
    listar_itens,
    listar_setores,
    listar_templates,
    listar_turnos,
    listar_usuarios,
    obter_configuracoes,
    obter_cor_primaria,
    obter_logo_url_com_fallback,
    reativar_template,
    remover_equipamento,
    remover_item,
    remover_logo,
    restaurar_cor_padrao,
)
from src.tema import aplicar_tema
from src.sidebar import mostrar_usuario_logado

st.set_page_config(page_title="Administração", page_icon="🛠️", layout="wide")

usuario = exigir_login()
aplicar_tema()
mostrar_usuario_logado(usuario)
if not usuario.pode_gerenciar_sistema:
    st.error("Acesso restrito ao administrador master.")
    st.stop()

st.title("🛠️ Administração")
tab_visual, tab_usuarios, tab_equipamentos, tab_novo_checklist, tab_checklists = st.tabs(
    ["🎨 Identidade Visual", "👤 Usuários", "🔧 Áreas/Equipamentos", "➕ Novo Checklist", "📋 Checklists Cadastrados"]
)

NIVEIS = {
    "producao": "Produção — preenche checklists",
    "supervisor": "Supervisor — assina, visualiza e exporta dashboard, gera QR",
    "coordenacao": "Coordenação — visualiza tudo, sem exportar",
    "master": "Master — acesso total, ajusta o sistema",
}

# =====================================================================
# TAB 0 — Identidade Visual (logo + cor)
# =====================================================================
with tab_visual:
    st.subheader("Logo da empresa")
    st.caption("Aparece no menu lateral do app e nos cartazes/etiquetas de QR Code para impressão.")

    config = obter_configuracoes()
    if config and config.get("logo_url"):
        st.image(config["logo_url"], width=240)
        st.caption("Logo personalizada (enviada por aqui).")
        if st.button("Remover logo e voltar para a padrão"):
            remover_logo()
            st.success("Logo removida. O sistema volta a usar a logo padrão do projeto.")
            st.rerun()
    else:
        logo_padrao = obter_logo_url_com_fallback()
        if logo_padrao:
            st.image(logo_padrao, width=240)
            st.caption("Logo padrão do projeto (Guararapes). Envie uma abaixo para substituir.")
        else:
            st.info("Nenhuma logo cadastrada ainda.")

    arquivo_logo = st.file_uploader("Enviar logo (PNG ou JPG)", type=["png", "jpg", "jpeg"])
    if arquivo_logo and st.button("Salvar logo", type="primary"):
        try:
            atualizar_logo(arquivo_logo.getvalue(), arquivo_logo.name)
            st.success("Logo atualizada.")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao enviar a logo: {e}")

    st.divider()
    st.subheader("Cor principal do sistema")
    st.caption(
        "Usada em botões e destaques. Padrão de fábrica: o verde da Guararapes "
        f"({COR_PADRAO_GUARARAPES}). Aplica na hora, sem precisar mexer em código."
    )
    st.caption(
        "⚠️ Cobre a maioria dos botões, mas o Streamlit não garante troca de tema "
        "em tempo real para 100% dos elementos. Se algo não acompanhar a cor, "
        "o método garantido é editar `primaryColor` em `.streamlit/config.toml` "
        "e fazer redeploy (veja o GUIA_MANUTENCAO.md)."
    )

    cor_atual = obter_cor_primaria()
    nova_cor = st.color_picker("Cor principal", value=cor_atual)

    col_salvar_cor, col_restaurar_cor = st.columns(2)
    if col_salvar_cor.button("Salvar cor", type="primary"):
        atualizar_cor_primaria(nova_cor)
        st.success("Cor atualizada.")
        st.rerun()
    if col_restaurar_cor.button("Restaurar verde Guararapes"):
        restaurar_cor_padrao()
        st.success("Cor restaurada para o padrão Guararapes.")
        st.rerun()

# =====================================================================
# TAB 1 — Usuários
# =====================================================================
with tab_usuarios:
    st.subheader("Cadastrar usuário")
    st.caption("Cada colaborador tem registro próprio: crachá (matrícula), e-mail da empresa e senha pessoal.")
    with st.form("form_novo_usuario", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome completo")
        email = c2.text_input("E-mail da empresa")
        c3, c4 = st.columns(2)
        matricula = c3.text_input("Número do crachá (matrícula)")
        papel = c4.selectbox("Nível de acesso", list(NIVEIS.keys()), format_func=lambda p: NIVEIS[p])
        senha_inicial = st.text_input("Senha inicial", type="password")
        if st.form_submit_button("Cadastrar", type="primary"):
            if not all([nome, email, matricula, senha_inicial]):
                st.error("Preencha todos os campos.")
            elif len(senha_inicial) < 6:
                st.error("Senha muito curta (mínimo 6 caracteres).")
            else:
                try:
                    criar_usuario(nome, email, matricula, senha_inicial, papel, usuario.id)
                    st.success(f"Usuário {nome} cadastrado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar (e-mail/matrícula já existe?): {e}")

    st.divider()
    st.subheader("Usuários cadastrados")
    usuarios = listar_usuarios()
    st.dataframe(
        [
            {
                "Nome": u["nome"], "E-mail": u["email"], "Matrícula": u["matricula"],
                "Papel": NIVEIS.get(u["papel"], u["papel"]),
                "Ativo": "✅" if u["ativo"] else "⛔",
                "Senha temporária": "⚠️" if u["senha_temporaria"] else "-",
            }
            for u in usuarios
        ],
        use_container_width=True, hide_index=True,
    )

    st.divider()
    mapa_usuarios = {f"{u['nome']} ({u['matricula']})": u["id"] for u in usuarios}

    col_reset, col_status = st.columns(2)
    with col_reset:
        st.subheader("Resetar senha")
        with st.form("form_reset_senha"):
            alvo = st.selectbox("Usuário", list(mapa_usuarios.keys()))
            nova_senha = st.text_input("Nova senha temporária", type="password")
            if st.form_submit_button("Resetar senha"):
                if len(nova_senha) < 6:
                    st.error("Senha muito curta.")
                else:
                    resetar_senha(mapa_usuarios[alvo], nova_senha)
                    st.success(f"Senha de {alvo} resetada. Troca obrigatória no próximo login.")

    with col_status:
        st.subheader("Ativar / Desativar")
        with st.form("form_status_usuario"):
            alvo2 = st.selectbox("Usuário", list(mapa_usuarios.keys()), key="sel_status")
            acao = st.radio("Ação", ["Ativar", "Desativar"], horizontal=True)
            if st.form_submit_button("Aplicar"):
                alternar_status(mapa_usuarios[alvo2], acao == "Ativar")
                st.success(f"{alvo2}: {acao.lower()} com sucesso.")
                st.rerun()

# =====================================================================
# TAB 2 — Áreas/Equipamentos
# Catálogo de área/equipamento específico por setor (ex.: setor "Silo
# de Cavaco" -> Descascador, Esteira de Cavaco, Picador, Esteira Silo 1).
# Você mantém essa lista aqui; ela alimenta o campo "área" na criação
# de um checklist novo, na aba seguinte.
# =====================================================================
with tab_equipamentos:
    setores = listar_setores()
    mapa_setores_eq = {s["nome"]: s["id"] for s in setores}

    st.subheader("Adicionar equipamento/área")
    with st.form("form_novo_equipamento", clear_on_submit=True):
        c1, c2 = st.columns(2)
        setor_eq_nome = c1.selectbox("Setor", list(mapa_setores_eq.keys()), key="setor_novo_equip")
        nome_equipamento = c2.text_input("Nome (ex: Picador, Esteira Silo 1)")
        if st.form_submit_button("Adicionar", type="primary"):
            if not nome_equipamento.strip():
                st.error("Informe o nome do equipamento/área.")
            else:
                try:
                    criar_equipamento(mapa_setores_eq[setor_eq_nome], nome_equipamento)
                    st.success(f"'{nome_equipamento}' adicionado a {setor_eq_nome}.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao adicionar (nome já existe nesse setor?): {e}")

    st.divider()
    st.subheader("Catálogo atual")
    for setor in setores:
        equipamentos = listar_equipamentos(setor["id"], apenas_ativos=False)
        if not equipamentos:
            continue
        st.markdown(f"**{setor['nome']}**")
        for eq in equipamentos:
            c1, c2, c3 = st.columns([4, 1, 1])
            c1.write(("🟢 " if eq["ativo"] else "⚪ ") + eq["nome"])
            if eq["ativo"]:
                if c2.button("Desativar", key=f"deact_eq_{eq['id']}"):
                    alternar_equipamento(eq["id"], False)
                    st.rerun()
            else:
                if c2.button("Reativar", key=f"react_eq_{eq['id']}"):
                    alternar_equipamento(eq["id"], True)
                    st.rerun()
            if c3.button("Remover", key=f"rm_eq_{eq['id']}"):
                try:
                    remover_equipamento(eq["id"])
                    st.rerun()
                except Exception as e:
                    st.error(f"Não é possível remover (em uso por um checklist?): {e}")

# =====================================================================
# TAB 3 — Novo Checklist
# =====================================================================
with tab_novo_checklist:
    setores = listar_setores()
    turnos = listar_turnos()
    mapa_setores = {s["nome"]: s["id"] for s in setores}

    st.subheader("Dados do checklist")
    c1, c2 = st.columns(2)
    codigo = c1.text_input("Código (ex: FRCDM2012.r01)")
    titulo = c2.text_input("Título (ex: Checklist de inspeções - Prensa)")
    setor_nome = st.selectbox("Setor do processo", list(mapa_setores.keys()))

    equipamentos_do_setor = listar_equipamentos(mapa_setores[setor_nome])
    mapa_equipamentos = {e["nome"]: e["id"] for e in equipamentos_do_setor}
    opcoes_area = ["— Usar nome do setor —"] + list(mapa_equipamentos.keys())
    area_escolhida = st.selectbox(
        "Área/Equipamento específico",
        opcoes_area,
        help="Lista vem da aba 'Áreas/Equipamentos'. Se o setor ainda não tem itens cadastrados, use o nome do setor.",
    )
    equipamento_id = mapa_equipamentos.get(area_escolhida)  # None se "usar nome do setor"

    revisao = st.text_input("Revisão", value="r01")
    observacao = st.text_area(
        "Observação padrão",
        value="Obs.: toda resposta Não exige comentário sobre a situação, resolução ou pendência.",
    )

    st.subheader("Itens de inspeção")
    st.caption("Uma pergunta por linha.")
    perguntas_texto = st.text_area("Perguntas", height=200)
    criticidade_padrao = st.selectbox("Criticidade padrão dos itens", ["media", "alta", "critica"])

    st.subheader("Horário de verificação por turno")
    st.caption("Um horário de checagem por turno — os 3 turnos da planta.")
    horarios_input = {}
    cols = st.columns(len(turnos))
    for col, turno in zip(cols, turnos):
        horarios_input[turno["id"]] = col.time_input(turno["nome"], key=f"horario_{turno['id']}")

    if st.button("Criar checklist", type="primary"):
        if not codigo or not titulo or not perguntas_texto.strip():
            st.error("Código, título e ao menos uma pergunta são obrigatórios.")
        else:
            try:
                template = criar_template(
                    codigo, titulo, mapa_setores[setor_nome], revisao, observacao,
                    equipamento_id=equipamento_id,
                )
                perguntas = [p.strip() for p in perguntas_texto.split("\n") if p.strip()]
                adicionar_itens(template["id"], perguntas, criticidade_padrao)
                horarios_str = {tid: h.strftime("%H:%M") for tid, h in horarios_input.items()}
                definir_horarios_turnos(template["id"], horarios_str)
                st.success(f"Checklist '{titulo}' criado com {len(perguntas)} itens.")
                st.balloons()
            except Exception as e:
                st.error(f"Erro ao criar checklist (código/slug já existe?): {e}")

# =====================================================================
# TAB 4 — Checklists cadastrados
# =====================================================================
with tab_checklists:
    CRITICIDADES = ["media", "alta", "critica"]

    templates = listar_templates(apenas_ativos=False)
    for t in templates:
        setor_nome = (t.get("setores_processo") or {}).get("nome", "—")
        equipamento_nome = (t.get("equipamentos") or {}).get("nome")
        rotulo_area = f"{setor_nome} · {equipamento_nome}" if equipamento_nome else setor_nome
        with st.expander(f"{'🟢' if t['ativo'] else '⚪'} {t['titulo']} · {rotulo_area}"):
            st.caption(f"{t['codigo']} · slug: {t['slug']}")

            # -----------------------------------------------------------
            # Horários de checagem por turno — editável
            # -----------------------------------------------------------
            st.markdown("**🕒 Horário de checagem por turno**")
            horarios = listar_horarios_todos_turnos(t["id"])
            for h in horarios:
                chave_edit_h = f"editando_horario_{h['id']}"
                turno_nome = h["turnos"]["nome"]

                if not st.session_state.get(chave_edit_h, False):
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"{turno_nome}: {h['horario'][:5]}")
                    if c2.button("Editar", key=f"edit_h_{h['id']}"):
                        st.session_state[chave_edit_h] = True
                        st.rerun()
                else:
                    partes = h["horario"].split(":")
                    hora_atual = time(int(partes[0]), int(partes[1]))
                    with st.form(f"form_edit_horario_{h['id']}"):
                        novo_horario = st.time_input(f"Novo horário — {turno_nome}", value=hora_atual)
                        col_salvar, col_cancelar = st.columns(2)
                        salvar_h = col_salvar.form_submit_button("Salvar", type="primary")
                        cancelar_h = col_cancelar.form_submit_button("Cancelar")
                    if salvar_h:
                        editar_horario(h["id"], novo_horario.strftime("%H:%M"))
                        st.session_state[chave_edit_h] = False
                        st.rerun()
                    if cancelar_h:
                        st.session_state[chave_edit_h] = False
                        st.rerun()

            st.divider()

            # -----------------------------------------------------------
            # Itens de inspeção — editável (pergunta + criticidade)
            # -----------------------------------------------------------
            st.markdown("**Itens de inspeção**")
            itens = listar_itens(t["id"])
            for item in itens:
                chave_edit_i = f"editando_item_{item['id']}"

                if not st.session_state.get(chave_edit_i, False):
                    c1, c2, c3 = st.columns([5, 1, 1])
                    c1.write(f"**[{item['criticidade']}]** {item['pergunta']}")
                    if c2.button("Editar", key=f"edit_i_{item['id']}"):
                        st.session_state[chave_edit_i] = True
                        st.rerun()
                    if c3.button("Remover", key=f"rm_{item['id']}"):
                        remover_item(item["id"])
                        st.rerun()
                else:
                    with st.form(f"form_edit_item_{item['id']}"):
                        nova_pergunta = st.text_area("Pergunta", value=item["pergunta"])
                        nova_criticidade = st.selectbox(
                            "Criticidade", CRITICIDADES,
                            index=CRITICIDADES.index(item["criticidade"]),
                        )
                        col_salvar, col_cancelar = st.columns(2)
                        salvar_i = col_salvar.form_submit_button("Salvar", type="primary")
                        cancelar_i = col_cancelar.form_submit_button("Cancelar")
                    if salvar_i:
                        if not nova_pergunta.strip():
                            st.error("A pergunta não pode ficar vazia.")
                        else:
                            editar_item(item["id"], nova_pergunta, nova_criticidade)
                            st.session_state[chave_edit_i] = False
                            st.rerun()
                    if cancelar_i:
                        st.session_state[chave_edit_i] = False
                        st.rerun()

            st.divider()
            if t["ativo"]:
                if st.button("Desativar checklist", key=f"deact_{t['id']}"):
                    desativar_template(t["id"])
                    st.rerun()
            else:
                if st.button("Reativar checklist", key=f"react_{t['id']}"):
                    reativar_template(t["id"])
                    st.rerun()
