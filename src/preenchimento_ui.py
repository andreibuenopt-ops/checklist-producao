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
from datetime import date

import streamlit as st

from src.auth import autenticar
from src.fotos import (
    MAX_FOTOS_POR_ITEM, agrupar_por_item, baixar_miniatura, enviar_foto, listar_fotos, remover_fotos_de_itens,
)
from src.itens import faltando_fotos, faltando_respostas, ids_filhos_inativos, itens_da_ronda, separar_itens
from src.historico_ui import botao_pdf_checklist, renderizar_checklist_somente_leitura
from src.models import (
    buscar_checklist,
    checklist_anterior,
    concluir_checklist,
    definir_colaborador,
    listar_horarios,
    listar_itens,
    listar_justificativas_atraso,
    listar_respostas,
    nomes_usuarios,
    obter_checklist_completo,
    obter_logo_bytes_com_fallback,
    obter_ou_criar_checklist,
    remover_respostas,
    salvar_justificativa_atraso,
    salvar_respostas_em_lote,
)
from src.turnos import (
    LETRA_TURNO, NOME_TURNO, esta_atrasado, ronda_vigente, turno_anterior, turno_e_data_referencia,
)


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

        botao_pdf_checklist(checklist["id"], obter_logo_bytes_com_fallback(), obter_checklist_completo, "preench")
        return

    itens = listar_itens(template["id"])
    horarios = listar_horarios(template["id"], turno.turno_id)
    respostas_salvas = listar_respostas(checklist["id"])
    justificativas_salvas = listar_justificativas_atraso(checklist["id"])
    data_ref = date.fromisoformat(str(checklist["data"])[:10])

    if not itens or not horarios:
        st.error("Este modelo de checklist ainda não tem perguntas/horário cadastrados.")
        return

    st.divider()

    ICONE_CRITICIDADE = {"critica": "🔴", "alta": "🟠", "media": "⚪"}
    ICONES_RESPOSTA = {"Sim": "✅ Sim", "Não": "❌ Não", "N/A": "➖ N/A"}
    OPCOES = ["Sim", "Não", "N/A"]

    # A ronda VIGENTE é a mais recente que já deveria ter acontecido — só
    # ela pode pedir justificativa de atraso (não todas as rondas passadas
    # de uma vez, senão quem chega atrasado pra preencher tudo junto teria
    # que justificar 2-3 vezes seguidas). Ver turnos.ronda_vigente().
    vigente = ronda_vigente(horarios, data_ref, turno.nome)
    vigente_atrasada = bool(vigente) and esta_atrasado(data_ref, vigente["horario"], turno.nome)

    # Fotos já salvas deste checklist, por (item, ronda). `versao_fotos`
    # entra na chave dos uploaders: ao salvar fotos ela sobe e os
    # uploaders voltam vazios (senão o mesmo arquivo seria reenviado).
    fotos_salvas = agrupar_por_item(listar_fotos(checklist["id"]))
    chave_versao_fotos = f"fotos_v_{checklist['id']}"
    versao_fotos = st.session_state.get(chave_versao_fotos, 0)

    # Mensagens que precisam sobreviver a um st.rerun() (ex.: depois de
    # enviar fotos, a página reroda pra mostrar as miniaturas novas).
    chave_flash = f"flash_{checklist['id']}"
    for tipo_msg, texto_msg in st.session_state.pop(chave_flash, []):
        getattr(st, tipo_msg)(texto_msg)

    # Passagem de turno: o que aconteceu nos 2 turnos anteriores desta área
    # (mais recente primeiro). toggle (e não expander) pra só buscar no
    # banco quando abrir.
    if st.toggle("📜 Ver o que aconteceu nos 2 turnos anteriores", key=f"ver_ant_{checklist['id']}"):
        cursor_turno, cursor_data = turno.turno_id, turno.data_referencia
        for _ in range(2):
            anterior = checklist_anterior(template["id"], cursor_turno, cursor_data)
            cursor_turno, cursor_data = turno_anterior(cursor_turno, cursor_data)   # o turno que acabou de ser consultado
            st.markdown(
                f"**Turno {LETRA_TURNO[cursor_turno]} {NOME_TURNO[cursor_turno]} · "
                f"{cursor_data.strftime('%d/%m/%Y')}**"
            )
            if anterior:
                renderizar_checklist_somente_leitura(obter_checklist_completo(anterior["id"], com_bytes=False), resumido=True)
            else:
                st.caption("Sem registro desse turno para esta área.")

    # Perguntas com SUB-perguntas (ex.: "Houve parada programada?"): o "Sim"
    # abre as filhas naquela ronda. Ver src/itens.py.
    _, filhos_por_pai = separar_itens(itens)
    ids_pais = set(filhos_por_pai)

    # Estado de tem_nao/faltando/faltando_justificativa/faltando_fotos só é
    # recalculado quando "Atualizar respostas" é confirmado — por isso fica
    # em session_state, não numa variável local (a página não reroda a
    # cada clique dentro do form).
    chave_estado = f"estado_preenchimento_{checklist['id']}"
    if chave_estado not in st.session_state:
        st.session_state[chave_estado] = {
            "tem_nao": any(v.get("resposta") == "Não" for v in respostas_salvas.values()),
            "faltando": faltando_respostas(itens, respostas_salvas, horarios),
            "faltando_justificativa": int(
                vigente_atrasada and not justificativas_salvas.get(vigente["id"])
            ),
            "faltando_fotos": faltando_fotos(itens, respostas_salvas, fotos_salvas, horarios),
        }

    def _bloco_foto(item, horario):
        """Fotos do item/ronda. Opcional (expander) ou, se o item exige
        foto, sempre visível e marcada como obrigatória."""
        chave_item = (item["id"], horario["id"])
        fotos_item = fotos_salvas.get(chave_item, [])
        restante = MAX_FOTOS_POR_ITEM - len(fotos_item)

        def _conteudo():
            for f in fotos_item:
                try:
                    st.image(baixar_miniatura(f["caminho"]), width=120)
                except Exception:
                    st.caption("(foto salva, miniatura indisponível)")
            if restante > 0:
                st.file_uploader(
                    "Foto", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True,
                    key=f"foto_{checklist['id']}_{item['id']}_{horario['id']}_{versao_fotos}",
                    label_visibility="collapsed",
                    help=f"No celular, escolha 'Tirar foto'. Enviada ao apertar \"Atualizar respostas\" "
                         f"(até {MAX_FOTOS_POR_ITEM} por pergunta).",
                )
            else:
                st.caption(f"Limite de {MAX_FOTOS_POR_ITEM} fotos atingido nesta pergunta.")

        if item.get("exige_foto"):
            st.markdown("📷 **Foto do local** " + ("✅" if fotos_item else "— ⚠️ obrigatória"))
            _conteudo()
        else:
            rotulo = f"📷 Fotos ({len(fotos_item)}) — adicionar mais" if fotos_item else "📷 Adicionar foto (opcional)"
            with st.expander(rotulo):
                _conteudo()

    def _desenhar_item(item, horario):
        chave = f"resp_{checklist['id']}_{item['id']}_{horario['id']}"
        chave_obs = f"obs_{checklist['id']}_{item['id']}_{horario['id']}"
        registro_atual = respostas_salvas.get((item["id"], horario["id"])) or {}
        valor_atual = registro_atual.get("resposta")

        icone = ICONE_CRITICIDADE.get(item.get("criticidade", "media"), "⚪")
        st.markdown(f"{icone} **{item['pergunta']}**")

        if item.get("tipo_resposta") == "texto_livre":
            st.text_area(
                "Resposta", value=registro_atual.get("observacao", ""), key=chave_obs,
                label_visibility="collapsed", height=80,
            )
        else:
            st.segmented_control(
                "Resposta", OPCOES, format_func=lambda v: ICONES_RESPOSTA[v],
                default=valor_atual if valor_atual in OPCOES else None,
                key=chave, label_visibility="collapsed",
            )
            if item["id"] in ids_pais and valor_atual != "Sim":
                st.caption("Marque **Sim** e aperte \"Atualizar respostas\" para abrir as perguntas desta parada.")
            if valor_atual == "Não":
                with st.expander("💬 Justificar esse item (opcional)", expanded=bool(registro_atual.get("observacao"))):
                    st.text_area(
                        "O que foi relatado / ação tomada nesse item",
                        value=registro_atual.get("observacao", ""), key=chave_obs,
                        label_visibility="collapsed", height=80,
                    )
        _bloco_foto(item, horario)

    # -------------------------------------------------------------
    # Perguntas x horário de checagem do turno, dentro de um único
    # formulário — ver explicação no topo do arquivo.
    #
    # O campo de observação por item só aparece quando a ÚLTIMA resposta
    # SALVA daquele item é "Não" (e as sub-perguntas, quando o pai está
    # salvo como "Sim") — como o form não reroda a cada clique (proposital,
    # ver topo do arquivo), isso surge depois de "Atualizar respostas".
    #
    # Justificativa de atraso: só na ronda VIGENTE (a mais recente que já
    # deveria ter acontecido), não em todas as rondas passadas.
    # -------------------------------------------------------------
    with st.form(f"form_respostas_{checklist['id']}"):
        for horario in horarios:
            eh_vigente_atrasada = vigente_atrasada and horario["id"] == vigente["id"]
            titulo_ronda = f"🕒 Ronda das {horario['horario'][:5]}"
            if eh_vigente_atrasada:
                titulo_ronda += " — ⏰ preenchendo com atraso"
            st.subheader(titulo_ronda)

            quadro_filhos = None
            for item, eh_filho in itens_da_ronda(itens, respostas_salvas, horario["id"]):
                if eh_filho:
                    if quadro_filhos is None:
                        quadro_filhos = st.container(border=True)
                        quadro_filhos.caption("↳ Perguntas desta parada — a foto do local é obrigatória")
                    with quadro_filhos:
                        _desenhar_item(item, horario)
                else:
                    quadro_filhos = None
                    _desenhar_item(item, horario)

            if eh_vigente_atrasada:
                chave_just = f"just_{checklist['id']}_{horario['id']}"
                st.caption(f"⏰ Essa ronda passou de 1h do horário programado ({horario['horario'][:5]}).")
                with st.expander("💬 Explicar o atraso (opcional)", expanded=bool(justificativas_salvas.get(horario["id"]))):
                    st.text_area(
                        "Por que está preenchendo agora?",
                        value=justificativas_salvas.get(horario["id"], ""), key=chave_just,
                        label_visibility="collapsed", height=80,
                    )
            st.markdown("---")

        atualizar_clicado = st.form_submit_button(
            "💾 Atualizar respostas", type="primary", use_container_width=True,
        )

    if atualizar_clicado:
        mudancas = []
        tem_nao = False
        faltando = 0
        gate_mudou = False
        for horario in horarios:
            def resposta_atual(item_id, _h=horario):
                chave_r = f"resp_{checklist['id']}_{item_id}_{_h['id']}"
                if chave_r in st.session_state:
                    return st.session_state[chave_r]
                return (respostas_salvas.get((item_id, _h["id"])) or {}).get("resposta")

            for item, _eh_filho in itens_da_ronda(itens, respostas_salvas, horario["id"], resposta_de=resposta_atual):
                chave = f"resp_{checklist['id']}_{item['id']}_{horario['id']}"
                chave_obs = f"obs_{checklist['id']}_{item['id']}_{horario['id']}"
                registro_atual = respostas_salvas.get((item["id"], horario["id"])) or {}
                valor_atual = registro_atual.get("resposta")
                observacao_atual = registro_atual.get("observacao", "")

                if item.get("tipo_resposta") == "texto_livre":
                    texto_novo = st.session_state.get(chave_obs, "").strip()
                    if texto_novo and texto_novo != observacao_atual:
                        mudancas.append({
                            "checklist_id": checklist["id"], "item_id": item["id"],
                            "horario_id": horario["id"], "resposta": "Texto",
                            "observacao": texto_novo,
                            "respondido_por": usuario.id,
                        })
                    if not texto_novo:
                        faltando += 1
                    continue

                resposta = st.session_state.get(chave)
                observacao_nova = st.session_state.get(chave_obs, "") if resposta == "Não" else ""

                houve_mudanca_resposta = resposta and resposta != valor_atual
                houve_mudanca_obs = resposta == "Não" and observacao_nova != observacao_atual

                if houve_mudanca_resposta or houve_mudanca_obs:
                    mudancas.append({
                        "checklist_id": checklist["id"], "item_id": item["id"],
                        "horario_id": horario["id"], "resposta": resposta or valor_atual,
                        "observacao": observacao_nova,
                        "respondido_por": usuario.id,
                    })
                if item["id"] in ids_pais and resposta != valor_atual:
                    gate_mudou = True   # abre/fecha as sub-perguntas: página precisa redesenhar
                if resposta == "Não":
                    tem_nao = True
                if not resposta:
                    faltando += 1

        qtd_salva = salvar_respostas_em_lote(mudancas)
        for m in mudancas:
            respostas_salvas[(m["item_id"], m["horario_id"])] = {
                "resposta": m["resposta"], "observacao": m["observacao"],
            }

        # Pai que voltou de "Sim" pra "Não": apaga respostas e fotos das
        # sub-perguntas (senão ficam ocupando espaço e aparecendo nos
        # relatórios sem fazer sentido).
        for horario in horarios:
            def resposta_pos(item_id, _h=horario):
                return (respostas_salvas.get((item_id, _h["id"])) or {}).get("resposta")
            orfas = ids_filhos_inativos(itens, respostas_salvas, horario["id"], resposta_de=resposta_pos)
            if orfas:
                remover_respostas(checklist["id"], horario["id"], orfas)
                remover_fotos_de_itens(checklist["id"], horario["id"], orfas)
                for item_id in orfas:
                    respostas_salvas.pop((item_id, horario["id"]), None)
                    fotos_salvas.pop((item_id, horario["id"]), None)
                gate_mudou = True

        # Justificativa de atraso: só a ronda vigente (a mais recente que
        # já deveria ter acontecido) pode ter justificativa pendente.
        faltando_justificativa = 0
        justificativas_novas = 0
        if vigente_atrasada:
            chave_just = f"just_{checklist['id']}_{vigente['id']}"
            texto_just = st.session_state.get(chave_just, "").strip()
            if texto_just and texto_just != justificativas_salvas.get(vigente["id"], ""):
                salvar_justificativa_atraso(checklist["id"], vigente["id"], texto_just, usuario.id)
                justificativas_salvas[vigente["id"]] = texto_just
                justificativas_novas += 1
            if not justificativas_salvas.get(vigente["id"]):
                faltando_justificativa = 1

        # Fotos: sobe as escolhidas nos uploaders (já reduzidas em
        # fotos.enviar_foto), respeitando o limite por pergunta. Falha numa
        # foto não derruba o resto.
        fotos_enviadas, erros_fotos, acima_do_limite = 0, [], 0
        recem_enviadas = set()
        for horario in horarios:
            def resposta_final(item_id, _h=horario):
                return (respostas_salvas.get((item_id, _h["id"])) or {}).get("resposta")
            for item, _eh_filho in itens_da_ronda(itens, respostas_salvas, horario["id"], resposta_de=resposta_final):
                chave_item = (item["id"], horario["id"])
                arquivos = st.session_state.get(f"foto_{checklist['id']}_{item['id']}_{horario['id']}_{versao_fotos}") or []
                vaga = max(MAX_FOTOS_POR_ITEM - len(fotos_salvas.get(chave_item, [])), 0)
                acima_do_limite += max(len(arquivos) - vaga, 0)
                for arquivo in arquivos[:vaga]:
                    try:
                        enviar_foto(checklist["id"], item["id"], horario["id"], arquivo.getvalue(), usuario.id)
                        fotos_enviadas += 1
                        recem_enviadas.add(chave_item)
                    except Exception as e:
                        erros_fotos.append(f"{item['pergunta'][:50]}… ({e})")

        sem_foto = faltando_fotos(itens, respostas_salvas, fotos_salvas, horarios, recem_enviadas)
        st.session_state[chave_estado] = {
            "tem_nao": tem_nao, "faltando": faltando, "faltando_justificativa": faltando_justificativa,
            "faltando_fotos": sem_foto,
        }

        mensagens = []
        if (qtd_salva == 0 and justificativas_novas == 0 and fotos_enviadas == 0 and not erros_fotos
                and not gate_mudou and not acima_do_limite):
            mensagens.append(("info", "Nenhuma alteração nova para salvar."))
        else:
            if qtd_salva:
                contagem = Counter(m["resposta"] for m in mudancas)
                resumo = f"{qtd_salva} resposta(s) salva(s): "
                resumo += ", ".join(f"{v} {k}" for k, v in contagem.items())
                mensagens.append(("success", resumo))
                if contagem.get("Não"):
                    mensagens.append((
                        "warning",
                        f"⚠️ {contagem['Não']} item(ns) marcado(s) como **Não** (não conforme). "
                        "Se quiser, registre o que foi feito em \"Justificar esse item\" ou no comentário geral.",
                    ))
            if justificativas_novas:
                mensagens.append(("success", f"{justificativas_novas} justificativa(s) de atraso salva(s)."))
            if fotos_enviadas:
                mensagens.append(("success", f"📷 {fotos_enviadas} foto(s) enviada(s)."))
            for erro in erros_fotos:
                mensagens.append(("error", f"Não consegui enviar uma foto: {erro}"))
            if acima_do_limite:
                mensagens.append(("warning", f"{acima_do_limite} foto(s) não enviada(s): limite de {MAX_FOTOS_POR_ITEM} por pergunta."))
        if sem_foto:
            mensagens.append(("warning", f"📷 Falta foto em {sem_foto} pergunta(s) da parada — é obrigatória para concluir."))

        if fotos_enviadas or gate_mudou:
            # Reroda pra mostrar as miniaturas novas / abrir ou fechar as
            # sub-perguntas, e esvaziar os uploaders.
            if fotos_enviadas:
                st.session_state[chave_versao_fotos] = versao_fotos + 1
            st.session_state[chave_flash] = mensagens
            st.rerun()
        for tipo_msg, texto_msg in mensagens:
            getattr(st, tipo_msg)(texto_msg)

    estado = st.session_state[chave_estado]
    tem_nao = estado["tem_nao"]
    faltando = estado["faltando"]
    faltando_justificativa = estado["faltando_justificativa"]
    sem_foto_obrigatoria = estado["faltando_fotos"]

    st.caption(
        (f"{faltando} pergunta(s) ainda sem resposta." if faltando else "Todas as perguntas respondidas. ✅")
        + " (contagem atualizada só depois de apertar \"Atualizar respostas\" acima)"
    )
    if sem_foto_obrigatoria:
        st.error(f"📷 Faltam fotos obrigatórias em {sem_foto_obrigatoria} pergunta(s) da parada. Anexe e aperte \"Atualizar respostas\".")

    # -------------------------------------------------------------
    # Comentários — sempre opcional. Justificar fica a critério de quem
    # preenche: só quando achar que realmente importa, não em toda
    # resposta "Não" ou toda ronda atrasada.
    # -------------------------------------------------------------
    with st.expander("💬 Comentário geral (opcional)", expanded=bool(checklist.get("comentario"))):
        comentario = st.text_area(
            "Comentários",
            value=checklist.get("comentario", "") or "",
            help="Use quando achar importante explicar a situação: se foi resolvido, como, ou se ficará pendente.",
            key=f"comentario_{checklist['id']}",
            label_visibility="collapsed",
        )

    # -------------------------------------------------------------
    # Assinatura e conclusão.
    # Qualquer usuário logado conclui sozinho, com a própria sessão —
    # sem depender do papel. Quem quiser dupla checagem pode, opcionalmente,
    # assinar com o login de um supervisor/coordenador/master (expander).
    # -------------------------------------------------------------
    st.divider()
    st.subheader("✍️ Conclusão")
    st.warning(
        "⚠️ **Depois de concluído, este checklist não pode mais ser editado.** "
        "Aperte \"Atualizar respostas\" antes de concluir, pra garantir que tudo "
        "que você marcou foi confirmado."
    )

    st.caption(f"Você vai concluir e assinar como **{usuario.nome}**.")
    with st.form(f"form_concluir_{checklist['id']}"):
        concluir = st.form_submit_button(
            "✅ Concluir checklist", type="primary", use_container_width=True,
        )
    if concluir:
        if faltando:
            st.error(f"Ainda faltam {faltando} pergunta(s) sem resposta. Confirme com \"Atualizar respostas\" primeiro.")
        elif sem_foto_obrigatoria:
            st.error(f"Faltam fotos obrigatórias em {sem_foto_obrigatoria} pergunta(s) da parada.")
        else:
            concluir_checklist(checklist["id"], usuario.id, comentario.strip())
            if "area" in st.query_params:
                del st.query_params["area"]
            st.success(f"Checklist concluído e assinado por {usuario.nome}. ✅")
            st.balloons()
            st.rerun()

    with st.expander("🔏 Assinar com outro usuário (supervisor) — opcional"):
        with st.form(f"form_concluir_outro_{checklist['id']}"):
            identificador_sup = st.text_input("E-mail ou matrícula de quem assina")
            senha_sup = st.text_input("Senha", type="password")
            concluir_outro = st.form_submit_button("Assinar e concluir com outro usuário", use_container_width=True)

        if concluir_outro:
            if faltando:
                st.error(f"Ainda faltam {faltando} pergunta(s) sem resposta. Confirme com \"Atualizar respostas\" primeiro.")
            elif sem_foto_obrigatoria:
                st.error(f"Faltam fotos obrigatórias em {sem_foto_obrigatoria} pergunta(s) da parada.")
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
