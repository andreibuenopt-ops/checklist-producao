"""Painel do administrador master: usuários e checklists."""
from collections import Counter
from datetime import time

import streamlit as st

from src.fotos import remover_fotos_antigas, uso_armazenamento
from src.itens import separar_itens
from src.paradas import (
    TIPOS, adicionar_itens_parada, desativar_item_parada, editar_item_parada, listar_itens_parada,
)
from src.auth import (
    TURMAS_VALIDAS, alternar_status, atualizar_papel_usuario, atualizar_turma_usuario, criar_usuario,
    exigir_login, resetar_senha,
)
from src.models import (
    COR_PADRAO_GUARARAPES,
    MAX_HORARIOS_POR_TURNO,
    adicionar_horario,
    adicionar_itens,
    alternar_equipamento,
    atualizar_autocadastro_requer_aprovacao,
    atualizar_cor_primaria,
    atualizar_logo,
    criar_equipamento,
    criar_template,
    definir_horarios_turnos,
    atualizar_nome_exibicao,
    desativar_template,
    editar_horario,
    editar_item,
    editar_setor_nome,
    listar_equipamentos,
    listar_horarios_todos_turnos,
    listar_itens,
    listar_setores,
    listar_templates,
    listar_turnos,
    listar_usuarios,
    mover_para_setor_proprio,
    obter_autocadastro_requer_aprovacao,
    obter_configuracoes,
    obter_cor_primaria,
    obter_logo_url_com_fallback,
    reativar_template,
    remover_equipamento,
    remover_horario,
    remover_item,
    remover_logo,
    restaurar_cor_padrao,
)
from src.tema import aplicar_tema, desativar_traducao_automatica
from src.sidebar import mostrar_usuario_logado

st.set_page_config(page_title="Administração", page_icon="🛠️", layout="wide")

desativar_traducao_automatica()
usuario = exigir_login()
aplicar_tema(usuario)
mostrar_usuario_logado(usuario)
if not usuario.pode_gerenciar_sistema:
    st.error("Acesso restrito a administrador ou master.")
    st.stop()

st.title("🛠️ Administração")
tab_visual, tab_usuarios, tab_equipamentos, tab_novo_checklist, tab_checklists, tab_armazenamento, tab_paradas = st.tabs(
    ["🎨 Identidade Visual", "👤 Usuários", "🔧 Áreas/Equipamentos", "➕ Novo Checklist",
     "📋 Checklists Cadastrados", "💾 Armazenamento", "🛑 Paradas"]
)

NIVEIS = {
    "producao": "Produção — preenche checklists",
    "supervisor": "Supervisor — assina, visualiza e exporta dashboard, gera QR",
    "coordenacao": "Coordenação — visualiza tudo, sem exportar",
    "administrador": "Administrador — administra o sistema no dia a dia",
    "master": "Master — comanda tudo, único que mexe em outro master",
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
    if usuario.pode_gerenciar_masters:
        requer_aprovacao_atual = obter_autocadastro_requer_aprovacao()
        nova_config_aprovacao = st.toggle(
            "Autocadastro fica pendente até o master aprovar",
            value=requer_aprovacao_atual,
            help=(
                "Desligado (padrão): quem se cadastra na aba \"Primeira vez aqui?\" "
                "já entra ativo como Produção. Ligado: a conta é criada mas fica "
                "inativa até você ativar aqui embaixo."
            ),
        )
        if nova_config_aprovacao != requer_aprovacao_atual:
            atualizar_autocadastro_requer_aprovacao(nova_config_aprovacao)
            st.success("Configuração salva.")
            st.rerun()
        st.divider()

    st.subheader("Cadastrar usuário")
    st.caption("Cada colaborador tem registro próprio: crachá (matrícula), e-mail da empresa e senha pessoal.")
    niveis_disponiveis = list(NIVEIS.keys()) if usuario.pode_gerenciar_masters else [
        p for p in NIVEIS.keys() if p != "master"
    ]
    with st.form("form_novo_usuario", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome completo")
        email = c2.text_input("E-mail da empresa")
        c3, c4 = st.columns(2)
        matricula = c3.text_input("Número do crachá (matrícula)")
        papel = c4.selectbox("Nível de acesso", niveis_disponiveis, format_func=lambda p: NIVEIS[p])
        c5, c6 = st.columns(2)
        senha_inicial = c5.text_input("Senha inicial", type="password")
        turma_nova = c6.selectbox("Turma", ["", *TURMAS_VALIDAS], format_func=lambda t: t or "Não definida")
        if st.form_submit_button("Cadastrar", type="primary"):
            if not all([nome, email, matricula, senha_inicial]):
                st.error("Preencha todos os campos.")
            elif len(senha_inicial) < 6:
                st.error("Senha muito curta (mínimo 6 caracteres).")
            else:
                try:
                    criar_usuario(nome, email, matricula, senha_inicial, papel, usuario.id, quem_cria=usuario, turma=turma_nova or None)
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
                "Turma": u.get("turma") or "-",
                "Ativo": "✅" if u["ativo"] else "⛔",
                "Senha temporária": "⚠️" if u["senha_temporaria"] else "-",
            }
            for u in usuarios
        ],
        use_container_width=True, hide_index=True,
    )

    st.divider()
    mapa_usuarios = {f"{u['nome']} ({u['matricula']})": u["id"] for u in usuarios}
    turma_de_usuario = {u["id"]: u.get("turma") for u in usuarios}

    st.subheader("Turma do colaborador")
    st.caption("Turma fixa (A, B, C ou D). Aparece no histórico, no dashboard e nos PDFs. O próprio colaborador também muda no menu lateral.")
    if usuarios:
        with st.form("form_turma_usuario"):
            alvo_turma = st.selectbox("Colaborador", list(mapa_usuarios.keys()), key="alvo_turma_usuario")
            nova_turma = st.selectbox("Turma", ["", *TURMAS_VALIDAS], format_func=lambda t: t or "Não definida", key="nova_turma_usuario")
            salvar_turma = st.form_submit_button("Salvar turma", type="primary")
        if salvar_turma:
            atualizar_turma_usuario(mapa_usuarios[alvo_turma], nova_turma or None)
            st.success("Turma salva.")
            st.rerun()
    st.divider()
    mapa_usuarios_papel = {f"{u['nome']} ({u['matricula']})": u["papel"] for u in usuarios}

    # Quem não é master nem vê conta master como alvo — evita erro na
    # hora de tentar (a função também bloqueia, isso é só a UI não
    # oferecer o que já sabe que vai falhar).
    if usuario.pode_gerenciar_masters:
        alvos_disponiveis = mapa_usuarios
    else:
        alvos_disponiveis = {k: v for k, v in mapa_usuarios.items() if mapa_usuarios_papel[k] != "master"}

    col_reset, col_status = st.columns(2)
    with col_reset:
        st.subheader("Resetar senha")
        if not alvos_disponiveis:
            st.caption("Nenhum usuário disponível.")
        else:
            with st.form("form_reset_senha"):
                alvo = st.selectbox("Usuário", list(alvos_disponiveis.keys()))
                nova_senha = st.text_input("Nova senha temporária", type="password")
                if st.form_submit_button("Resetar senha"):
                    if len(nova_senha) < 6:
                        st.error("Senha muito curta.")
                    else:
                        try:
                            resetar_senha(alvos_disponiveis[alvo], nova_senha, quem_altera=usuario)
                            st.success(f"Senha de {alvo} resetada. Troca obrigatória no próximo login.")
                        except ValueError as e:
                            st.error(str(e))

    with col_status:
        st.subheader("Ativar / Desativar")
        if not alvos_disponiveis:
            st.caption("Nenhum usuário disponível.")
        else:
            with st.form("form_status_usuario"):
                alvo2 = st.selectbox("Usuário", list(alvos_disponiveis.keys()), key="sel_status")
                acao = st.radio("Ação", ["Ativar", "Desativar"], horizontal=True)
                if st.form_submit_button("Aplicar"):
                    try:
                        alternar_status(alvos_disponiveis[alvo2], acao == "Ativar", quem_altera=usuario)
                        st.success(f"{alvo2}: {acao.lower()} com sucesso.")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

    st.divider()
    st.subheader("Alterar nível de acesso")
    st.caption(
        "Use aqui pra ajustar quem se autocadastrou (entra sempre como "
        "Produção) — ou pra promover/rebaixar qualquer usuário."
    )
    if not alvos_disponiveis:
        st.caption("Nenhum usuário disponível.")
    else:
        niveis_disponiveis_alt = list(NIVEIS.keys()) if usuario.pode_gerenciar_masters else [
            p for p in NIVEIS.keys() if p != "master"
        ]
        with st.form("form_alterar_papel"):
            alvo3 = st.selectbox("Usuário", list(alvos_disponiveis.keys()), key="sel_papel")
            papel_atual = mapa_usuarios_papel.get(alvo3, "producao")
            indice_atual = niveis_disponiveis_alt.index(papel_atual) if papel_atual in niveis_disponiveis_alt else 0
            novo_papel = st.selectbox(
                "Novo nível", niveis_disponiveis_alt,
                index=indice_atual,
                format_func=lambda p: NIVEIS[p],
            )
            if st.form_submit_button("Salvar novo nível", type="primary"):
                if novo_papel == papel_atual:
                    st.info(f"{alvo3} já está como {NIVEIS[novo_papel]}.")
                else:
                    try:
                        atualizar_papel_usuario(alvos_disponiveis[alvo3], novo_papel, quem_altera=usuario)
                        st.success(f"{alvo3} agora é {NIVEIS[novo_papel]}.")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

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

    tipo_area = st.radio(
        "Área", ["interno", "externo"],
        format_func=lambda v: "🏭 Interno" if v == "interno" else "🌳 Externo",
        horizontal=True,
        help="Interno: dentro da planta/equipamento. Externo: pátio, área externa, limpeza externa.",
    )

    revisao = st.text_input("Revisão", value="r01")
    observacao = st.text_area(
        "Observação padrão",
        value="Obs.: toda resposta Não exige comentário sobre a situação, resolução ou pendência.",
    )

    st.subheader("Itens de inspeção")
    st.caption("Uma pergunta por linha.")
    perguntas_texto = st.text_area("Perguntas", height=200)
    criticidade_padrao = st.selectbox("Criticidade padrão dos itens", ["media", "alta", "critica"])
    tipo_resposta_padrao = st.selectbox(
        "Tipo de resposta dos itens acima",
        ["sim_nao", "texto_livre"],
        format_func=lambda v: {"sim_nao": "Sim / Não / N-A", "texto_livre": "Texto livre (pergunta aberta)"}[v],
        help=(
            "Sim/Não/N-A: pergunta fechada de inspeção, ex. \"Correia está com danos?\".\n\n"
            "Texto livre: pergunta aberta que precisa de uma resposta descritiva, "
            "ex. \"Qual produto está sendo produzido?\" ou \"Houve desvio de qualidade? "
            "Qual? O que foi feito para normalizar?\". Use quando a resposta não é um "
            "simples Sim/Não — mistura os dois tipos criando o checklist e depois "
            "ajustando o tipo item a item em \"Checklists cadastrados\" se precisar."
        ),
    )

    st.subheader("Horário de verificação por turno")
    st.caption(f"Um horário inicial por turno — depois de criado, adiciona mais rondas (até {MAX_HORARIOS_POR_TURNO} por turno) em \"Checklists cadastrados\".")
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
                    equipamento_id=equipamento_id, tipo_area=tipo_area,
                )
                perguntas = [p.strip() for p in perguntas_texto.split("\n") if p.strip()]
                adicionar_itens(template["id"], perguntas, criticidade_padrao, tipo_resposta_padrao)
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
    contagem_setor = Counter(t["setor_id"] for t in templates if t.get("setor_id"))
    for t in templates:
        setor_nome = (t.get("setores_processo") or {}).get("nome", "—")
        equipamento_nome = (t.get("equipamentos") or {}).get("nome")
        rotulo_area = f"{setor_nome} · {equipamento_nome}" if equipamento_nome else setor_nome
        with st.expander(f"{'🟢' if t['ativo'] else '⚪'} {t['titulo']} · {rotulo_area}"):
            selo_area = "🏭 Interno" if t.get("tipo_area", "interno") == "interno" else "🌳 Externo"
            st.caption(f"{t['codigo']} · slug: {t['slug']} · {selo_area}")

            # -----------------------------------------------------------
            # Nome de exibição (aparece no QR/etiqueta/cartaz) — editável
            # livremente, sem afetar o setor formal (que continua
            # controlando o agrupamento em todo o resto do sistema).
            # -----------------------------------------------------------
            with st.form(f"form_nome_qr_{t['id']}"):
                novo_nome_qr = st.text_input(
                    "Nome de exibição no QR / etiqueta / cartaz",
                    value=t["area"],
                    help=f"Setor: {setor_nome} (isso aqui não muda — é só o rótulo mostrado no QR, ex: \"{t['titulo']}\").",
                    key=f"nome_qr_{t['id']}",
                )
                if st.form_submit_button("Salvar nome do QR"):
                    if novo_nome_qr.strip():
                        atualizar_nome_exibicao(t["id"], novo_nome_qr)
                        st.success("Nome atualizado.")
                        st.rerun()
                    else:
                        st.error("O nome não pode ficar vazio.")

            # -----------------------------------------------------------
            # Nome do SETOR/processo formal — isso é diferente do campo
            # acima: muda o cabeçalho de agrupamento em TODO o sistema
            # (Gerar QRCodes, Preencher Checklist manual, Dashboard),
            # não só a etiqueta deste checklist.
            # -----------------------------------------------------------
            outros_no_setor = contagem_setor.get(t.get("setor_id"), 1) - 1
            with st.form(f"form_nome_setor_{t['id']}"):
                if outros_no_setor > 0:
                    st.caption(
                        f"⚠️ Esse setor agrupa mais {outros_no_setor} checklist(s) além deste — "
                        "renomear aqui muda o cabeçalho pra todos eles também."
                    )
                novo_nome_setor = st.text_input(
                    "Nome do setor/processo (cabeçalho usado em todo o sistema)",
                    value=setor_nome,
                    key=f"nome_setor_{t['id']}",
                )
                if st.form_submit_button("Salvar nome do setor"):
                    if novo_nome_setor.strip():
                        editar_setor_nome(t["setor_id"], novo_nome_setor)
                        st.success("Setor renomeado.")
                        st.rerun()
                    else:
                        st.error("O nome não pode ficar vazio.")

            # Separar num setor exclusivo — diferente de renomear: cria um
            # setor NOVO só pra esse checklist, sem mudar nada dos outros
            # que ainda dividem o setor atual. Resolve o caso de checklist
            # "perdido" dentro de um setor genérico (ex.: Sifter dentro de
            # Silo de Cavaco) sem bagunçar os demais.
            if outros_no_setor > 0:
                with st.form(f"form_separar_setor_{t['id']}"):
                    st.caption(
                        f"Ou: deixa só ESTE checklist com setor próprio, sem mexer nos outros "
                        f"{outros_no_setor} que continuam em \"{setor_nome}\"."
                    )
                    nome_setor_proprio = st.text_input(
                        "Nome do novo setor exclusivo",
                        value=t["area"],
                        key=f"nome_setor_proprio_{t['id']}",
                    )
                    if st.form_submit_button("📤 Separar em setor próprio"):
                        if nome_setor_proprio.strip():
                            try:
                                mover_para_setor_proprio(t["id"], nome_setor_proprio)
                                st.success(f"Separado em setor próprio: \"{nome_setor_proprio.strip()}\".")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Não deu pra separar — talvez já exista um setor com esse nome. ({e})")
                        else:
                            st.error("O nome não pode ficar vazio.")

            st.divider()

            # -----------------------------------------------------------
            # Horários de checagem por turno — editável, com várias
            # rondas por turno (até MAX_HORARIOS_POR_TURNO).
            # -----------------------------------------------------------
            st.markdown(f"**🕒 Rondas por turno** (até {MAX_HORARIOS_POR_TURNO} por turno)")
            horarios = listar_horarios_todos_turnos(t["id"])
            horarios_por_turno_id = {}
            for h in horarios:
                horarios_por_turno_id.setdefault(h["turno_id"], []).append(h)

            for turno in listar_turnos():
                st.caption(turno["nome"])
                rondas_turno = horarios_por_turno_id.get(turno["id"], [])
                for h in rondas_turno:
                    chave_edit_h = f"editando_horario_{h['id']}"
                    if not st.session_state.get(chave_edit_h, False):
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.write(h["horario"][:5])
                        if c2.button("Editar", key=f"edit_h_{h['id']}"):
                            st.session_state[chave_edit_h] = True
                            st.rerun()
                        if c3.button("Remover", key=f"rm_h_{h['id']}"):
                            remover_horario(h["id"])
                            st.rerun()
                    else:
                        partes = h["horario"].split(":")
                        hora_atual = time(int(partes[0]), int(partes[1]))
                        with st.form(f"form_edit_horario_{h['id']}"):
                            novo_horario = st.time_input("Novo horário", value=hora_atual)
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

                if len(rondas_turno) < MAX_HORARIOS_POR_TURNO:
                    with st.form(f"form_add_horario_{t['id']}_{turno['id']}"):
                        c1, c2 = st.columns([3, 1])
                        novo_h = c1.time_input("Adicionar ronda", key=f"novo_h_{t['id']}_{turno['id']}", label_visibility="collapsed")
                        adicionar_clicado = c2.form_submit_button("➕ Adicionar")
                    if adicionar_clicado:
                        erro_h = adicionar_horario(t["id"], turno["id"], novo_h.strftime("%H:%M"))
                        if erro_h:
                            st.error(erro_h)
                        else:
                            st.success("Ronda adicionada.")
                            st.rerun()
                else:
                    st.caption(f"⚠️ Limite de {MAX_HORARIOS_POR_TURNO} rondas atingido nesse turno.")

            st.divider()

            # -----------------------------------------------------------
            # Itens de inspeção — editável (pergunta + criticidade)
            # -----------------------------------------------------------
            st.markdown("**Itens de inspeção**")
            st.caption(
                "**➕ Sub** cadastra sub-perguntas: elas só aparecem quando a pergunta for respondida "
                "**Sim** (ex.: \"Houve parada programada?\" → perguntas da parada, com foto obrigatória)."
            )
            itens = listar_itens(t["id"])
            topo, filhos_por_pai = separar_itens(itens)

            def _linha_item(item, filho=False):
                chave_edit_i = f"editando_item_{item['id']}"
                if not st.session_state.get(chave_edit_i, False):
                    c1, c2, c3, c4 = st.columns([5, 1, 1, 1])
                    selos = ""
                    if item.get("tipo_resposta") == "texto_livre":
                        selos += " 📝 texto livre"
                    if item.get("exige_foto"):
                        selos += " 📷 foto obrigatória"
                    c1.write(f"{'↳ ' if filho else ''}**[{item['criticidade']}]** {item['pergunta']}{selos}")
                    if c2.button("Editar", key=f"edit_i_{item['id']}"):
                        st.session_state[chave_edit_i] = True
                        st.rerun()
                    if c3.button("Remover", key=f"rm_{item['id']}"):
                        remover_item(item["id"])
                        st.rerun()
                    if not filho and item.get("tipo_resposta", "sim_nao") == "sim_nao":
                        if c4.button("➕ Sub", key=f"sub_{item['id']}"):
                            st.session_state[f"add_sub_{item['id']}"] = not st.session_state.get(f"add_sub_{item['id']}", False)
                            st.rerun()
                else:
                    with st.form(f"form_edit_item_{item['id']}"):
                        nova_pergunta = st.text_area("Pergunta", value=item["pergunta"])
                        nova_criticidade = st.selectbox(
                            "Criticidade", CRITICIDADES,
                            index=CRITICIDADES.index(item["criticidade"]),
                        )
                        TIPOS_RESPOSTA = ["sim_nao", "texto_livre"]
                        novo_tipo = st.selectbox(
                            "Tipo de resposta", TIPOS_RESPOSTA,
                            index=TIPOS_RESPOSTA.index(item.get("tipo_resposta", "sim_nao")),
                            format_func=lambda v: {"sim_nao": "Sim / Não / N-A", "texto_livre": "Texto livre"}[v],
                            help="Ex. texto livre: \"Qual produto está sendo produzido?\"",
                        )
                        nova_exige_foto = st.checkbox(
                            "Exigir foto (não conclui o checklist sem foto desta pergunta)",
                            value=bool(item.get("exige_foto")),
                        )
                        col_salvar, col_cancelar = st.columns(2)
                        salvar_i = col_salvar.form_submit_button("Salvar", type="primary")
                        cancelar_i = col_cancelar.form_submit_button("Cancelar")
                    if salvar_i:
                        if not nova_pergunta.strip():
                            st.error("A pergunta não pode ficar vazia.")
                        else:
                            editar_item(item["id"], nova_pergunta, nova_criticidade, novo_tipo, nova_exige_foto)
                            st.session_state[chave_edit_i] = False
                            st.rerun()
                    if cancelar_i:
                        st.session_state[chave_edit_i] = False
                        st.rerun()

            for item in topo:
                _linha_item(item)
                for filha in filhos_por_pai.get(item["id"], []):
                    _linha_item(filha, filho=True)
                if st.session_state.get(f"add_sub_{item['id']}", False):
                    with st.form(f"form_add_sub_{item['id']}"):
                        st.caption(f"Sub-perguntas de: **{item['pergunta']}**")
                        texto_sub = st.text_area("Uma pergunta por linha", height=140, key=f"txt_sub_{item['id']}")
                        exige_sub = st.checkbox("Exigir foto em cada uma", value=True, key=f"foto_sub_{item['id']}")
                        col_a, col_b = st.columns(2)
                        ok_sub = col_a.form_submit_button("Adicionar sub-perguntas", type="primary")
                        fechar_sub = col_b.form_submit_button("Fechar")
                    if ok_sub:
                        perguntas_sub = [l for l in texto_sub.splitlines() if l.strip()]
                        if not perguntas_sub:
                            st.error("Escreva pelo menos uma pergunta.")
                        else:
                            adicionar_itens(
                                t["id"], perguntas_sub, item["criticidade"], "sim_nao",
                                pai_item_id=item["id"], exige_foto=exige_sub,
                            )
                            st.session_state[f"add_sub_{item['id']}"] = False
                            st.rerun()
                    if fechar_sub:
                        st.session_state[f"add_sub_{item['id']}"] = False
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


# =====================================================================
# TAB 5 — Armazenamento (plano gratuito do Supabase: 500 MB de banco, 1 GB de fotos)
# =====================================================================
with tab_armazenamento:
    LIMITE_BANCO_MB, LIMITE_FOTOS_MB = 500, 1024
    st.subheader("Uso do plano gratuito do Supabase")
    uso = uso_armazenamento()

    def _barra(rotulo: str, valor, limite: int):
        if valor is None:
            st.caption(f"{rotulo}: indisponível (rode o SQL migration_fotos_historico.sql no Supabase).")
            return
        pct = min(valor / limite, 1.0)
        st.progress(pct, text=f"{rotulo}: {valor:.0f} MB de {limite} MB ({pct * 100:.0f}%)")
        if pct >= 0.9:
            st.error(f"{rotulo} quase cheio — apague dados/fotos antigos agora.")
        elif pct >= 0.7:
            st.warning(f"{rotulo} passou de 70% do limite.")

    _barra("Banco de dados", uso["banco_mb"], LIMITE_BANCO_MB)
    _barra("Fotos (Storage)", uso["fotos_mb"], LIMITE_FOTOS_MB)
    if uso["fotos_qtd"] is not None:
        st.caption(f"{uso['fotos_qtd']} foto(s) guardada(s). Cada foto é reduzida pra ~100 KB ao enviar, no máx. 3 por pergunta.")

    st.divider()
    st.subheader("🗑️ Apagar fotos antigas")
    st.caption(
        "Libera espaço do Storage. As respostas, comentários, PDFs já baixados e relatórios continuam — "
        "só as fotos mais velhas que o prazo somem (e deixam de aparecer no histórico e em PDFs novos)."
    )
    dias_apagar = st.number_input("Apagar fotos com mais de (dias)", min_value=30, max_value=3650, value=90, step=15)
    confirma_apagar = st.checkbox("Entendo que as fotos apagadas não podem ser recuperadas.")
    if st.button("Apagar fotos antigas", disabled=not confirma_apagar, type="primary"):
        apagadas = remover_fotos_antigas(int(dias_apagar))
        st.success(f"{apagadas} foto(s) apagada(s).")
        st.rerun()


# =====================================================================
# TAB 6 — Paradas de linha: perguntas de cada um dos 3 checklists
# =====================================================================
with tab_paradas:
    st.subheader("Perguntas dos checklists de parada")
    st.caption(
        "São 3 checklists separados. Cada vez que alguém abre uma parada, ele recebe as perguntas do tipo escolhido. "
        "Com **Exigir foto** marcado, a pergunta não deixa concluir sem foto do local. Remover uma pergunta só a "
        "desativa: paradas antigas continuam mostrando o que foi respondido."
    )
    for tipo_chave, tipo_nome in TIPOS.items():
        with st.expander(tipo_nome, expanded=False):
            itens_tipo = listar_itens_parada(tipo_chave, apenas_ativos=True)
            if not itens_tipo:
                st.info("Nenhuma pergunta cadastrada ainda.")
            for it in itens_tipo:
                chave_edit = f"editando_pi_{it['id']}"
                if not st.session_state.get(chave_edit, False):
                    c1, c2, c3 = st.columns([6, 1, 1])
                    c1.write(f"{it['ordem']}. {it['pergunta']}" + (" 📷 foto obrigatória" if it["exige_foto"] else ""))
                    if c2.button("Editar", key=f"edit_pi_{it['id']}"):
                        st.session_state[chave_edit] = True
                        st.rerun()
                    if c3.button("Remover", key=f"rm_pi_{it['id']}"):
                        desativar_item_parada(it["id"])
                        st.rerun()
                else:
                    with st.form(f"form_edit_pi_{it['id']}"):
                        nova_p = st.text_area("Pergunta", value=it["pergunta"])
                        nova_foto = st.checkbox("Exigir foto", value=it["exige_foto"])
                        ca, cb = st.columns(2)
                        salvar_pi = ca.form_submit_button("Salvar", type="primary")
                        cancelar_pi = cb.form_submit_button("Cancelar")
                    if salvar_pi:
                        if nova_p.strip():
                            editar_item_parada(it["id"], nova_p, nova_foto)
                            st.session_state[chave_edit] = False
                            st.rerun()
                        else:
                            st.error("A pergunta não pode ficar vazia.")
                    if cancelar_pi:
                        st.session_state[chave_edit] = False
                        st.rerun()

            st.markdown("**Adicionar perguntas**")
            with st.form(f"form_add_pi_{tipo_chave}", clear_on_submit=True):
                texto_novas = st.text_area("Uma pergunta por linha", height=140, key=f"txt_pi_{tipo_chave}")
                exige_novas = st.checkbox("Exigir foto em cada uma", value=True, key=f"foto_pi_{tipo_chave}")
                if st.form_submit_button("Adicionar", type="primary"):
                    novas = [l for l in texto_novas.splitlines() if l.strip()]
                    if not novas:
                        st.error("Escreva pelo menos uma pergunta.")
                    else:
                        adicionar_itens_parada(tipo_chave, novas, exige_novas)
                        st.success(f"{len(novas)} pergunta(s) adicionada(s).")
                        st.rerun()
