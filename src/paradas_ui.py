"""Telas do checklist de PARADA DE LINHA: preenchimento (com foto por
pergunta), visão somente leitura e PDF sob demanda."""
import streamlit as st

from src.fotos import MAX_FOTOS_POR_ITEM, baixar_miniatura, enviar_foto_parada, listar_fotos_parada
from src.paradas import (
    TIPOS,
    atualizar_descricao_parada,
    buscar_parada,
    concluir_parada,
    faltando_fotos,
    faltando_respostas,
    fotos_por_pergunta,
    itens_visiveis,
    listar_itens_parada,
    listar_respostas_parada,
    obter_parada_completa,
    salvar_respostas_parada,
)
from src.turnos import formatar_datahora_local

OPCOES = ["Sim", "Não", "N/A"]
ICONES = {"Sim": "✅ Sim", "Não": "❌ Não", "N/A": "➖ N/A"}


def _data_br(valor) -> str:
    t = str(valor)[:10]
    return f"{t[8:10]}/{t[5:7]}/{t[:4]}"


def renderizar_parada_somente_leitura(dados: dict):
    p = dados["parada"]
    st.caption(
        f"**{dados['tipo_nome']}** · Turno **{dados['turno_nome']}** · dia de produção **{_data_br(p['data'])}** · "
        f"iniciada {formatar_datahora_local(p.get('iniciada_em'))}"
    )
    if p["status"] == "completo":
        st.success("Concluído. ✅")
    else:
        st.info("Ainda **em andamento**.")
    c1, c2, c3 = st.columns(3)
    col_t = dados.get("colaborador_turma")
    c1.metric("Aberta por", dados["colaborador_nome"] + (f" (Turma {col_t})" if col_t else ""))
    c2.metric("Concluída por", dados["supervisor_nome"])
    c3.metric("Concluída em", formatar_datahora_local(p.get("concluido_em")))
    if p.get("descricao"):
        st.info(f"**O que aconteceu:** {p['descricao']}")

    fotos = fotos_por_pergunta(dados.get("fotos", []))
    for item in dados["itens"]:
        reg = dados["respostas"].get(item["id"]) or {}
        resp = reg.get("resposta")
        st.markdown(f"{ICONES.get(resp, '⬜')[:1] if resp else '⬜'} **{item['pergunta']}** — {resp or 'sem resposta'}")
        if reg.get("observacao"):
            st.caption(f"↳ {reg['observacao']}")
        fs = fotos.get(item["id"], [])
        if fs:
            colunas = st.columns(min(len(fs), 3))
            for i, f in enumerate(fs):
                try:
                    colunas[i % len(colunas)].image(baixar_miniatura(f["caminho"]), width=160)
                except Exception:
                    colunas[i % len(colunas)].caption("(foto indisponível)")
    if p.get("comentario"):
        st.info(f"💬 **Comentário:** {p['comentario']}")


def botao_pdf_parada(parada_id: str, logo_bytes, chave: str):
    """PDF sob demanda (só então baixa as fotos inteiras)."""
    from src.pdf_parada import gerar_pdf_parada

    chave_pdf = f"pdfp_{chave}_{parada_id}"
    if st.button("📄 Gerar PDF", key=f"gerar_{chave_pdf}"):
        with st.spinner("Gerando PDF…"):
            st.session_state[chave_pdf] = gerar_pdf_parada(obter_parada_completa(parada_id), logo_bytes)
    if chave_pdf in st.session_state:
        st.download_button("⬇️ Baixar PDF", data=st.session_state[chave_pdf], file_name=f"parada_{parada_id}.pdf",
                           mime="application/pdf", key=f"baixar_{chave_pdf}")


def renderizar_parada(usuario, parada_id: str, logo_bytes=None):
    parada = buscar_parada(parada_id)
    if not parada:
        st.error("Parada não encontrada.")
        return

    if parada["status"] == "completo":
        renderizar_parada_somente_leitura(obter_parada_completa(parada_id, com_bytes=False))
        botao_pdf_parada(parada_id, logo_bytes, "parada")
        return

    itens = itens_visiveis(listar_itens_parada(parada["tipo"], apenas_ativos=False), {}, False)
    st.caption(
        f"**{TIPOS[parada['tipo']]}** · Turno **{(parada.get('turnos') or {}).get('nome', '-')}** · "
        f"dia de produção **{_data_br(parada['data'])}** · iniciada {formatar_datahora_local(parada.get('iniciada_em'))}"
    )
    if not itens:
        st.warning("Este tipo de parada ainda não tem perguntas cadastradas. Peça ao administrador: Administração > Paradas.")
        return

    respostas = listar_respostas_parada(parada_id)
    fotos_salvas = fotos_por_pergunta(listar_fotos_parada(parada_id))
    chave_versao = f"pfv_{parada_id}"
    versao = st.session_state.get(chave_versao, 0)

    chave_flash = f"pflash_{parada_id}"
    for tipo_msg, texto_msg in st.session_state.pop(chave_flash, []):
        getattr(st, tipo_msg)(texto_msg)

    chave_estado = f"pestado_{parada_id}"
    if chave_estado not in st.session_state:
        st.session_state[chave_estado] = {
            "faltando": faltando_respostas(itens, respostas),
            "faltando_fotos": faltando_fotos(itens, respostas, fotos_salvas),
        }

    with st.form(f"form_parada_{parada_id}"):
        descricao = st.text_area(
            "O que aconteceu / motivo da parada (opcional)", value=parada.get("descricao") or "",
            key=f"pdesc_{parada_id}", height=80,
        )
        for item in itens:
            chave = f"pr_{parada_id}_{item['id']}"
            chave_obs = f"po_{parada_id}_{item['id']}"
            reg = respostas.get(item["id"]) or {}
            valor_atual = reg.get("resposta")
            fotos_item = fotos_salvas.get(item["id"], [])

            st.markdown(f"**{item['pergunta']}**")
            st.segmented_control(
                "Resposta", OPCOES, format_func=lambda v: ICONES[v],
                default=valor_atual if valor_atual in OPCOES else None, key=chave, label_visibility="collapsed",
            )
            if valor_atual == "Não":
                with st.expander("💬 Justificar esse item (opcional)", expanded=bool(reg.get("observacao"))):
                    st.text_area("O que foi relatado / ação tomada", value=reg.get("observacao", ""), key=chave_obs,
                                 label_visibility="collapsed", height=80)

            if item.get("exige_foto"):
                st.markdown("📷 **Foto do local** " + ("✅" if fotos_item else "— ⚠️ obrigatória"))
            else:
                st.markdown("📷 Foto (opcional)")
            for f in fotos_item:
                try:
                    st.image(baixar_miniatura(f["caminho"]), width=120)
                except Exception:
                    st.caption("(foto salva, miniatura indisponível)")
            if len(fotos_item) < MAX_FOTOS_POR_ITEM:
                st.file_uploader(
                    "Foto", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True,
                    key=f"pf_{parada_id}_{item['id']}_{versao}", label_visibility="collapsed",
                    help=f"No celular, escolha 'Tirar foto'. Enviada ao apertar \"Atualizar respostas\" (até {MAX_FOTOS_POR_ITEM} por pergunta).",
                )
            else:
                st.caption(f"Limite de {MAX_FOTOS_POR_ITEM} fotos atingido nesta pergunta.")
            st.markdown("---")

        atualizar = st.form_submit_button("💾 Atualizar respostas", type="primary", use_container_width=True)

    if atualizar:
        mudancas, faltando = [], 0
        for item in itens:
            resposta = st.session_state.get(f"pr_{parada_id}_{item['id']}")
            atual = respostas.get(item["id"]) or {}
            obs_nova = st.session_state.get(f"po_{parada_id}_{item['id']}", "") if resposta == "Não" else ""
            if (resposta and resposta != atual.get("resposta")) or (resposta == "Não" and obs_nova != atual.get("observacao", "")):
                mudancas.append({"parada_id": parada_id, "item_id": item["id"], "resposta": resposta or atual.get("resposta"),
                                 "observacao": obs_nova, "respondido_por": usuario.id})
            if not resposta:
                faltando += 1
        qtd = salvar_respostas_parada(mudancas)
        for m in mudancas:
            respostas[m["item_id"]] = {"resposta": m["resposta"], "observacao": m["observacao"]}

        descricao_salva = False
        if (descricao or "").strip() != (parada.get("descricao") or ""):
            atualizar_descricao_parada(parada_id, descricao.strip())
            descricao_salva = True

        enviadas, erros, acima, recem = 0, [], 0, set()
        for item in itens:
            arquivos = st.session_state.get(f"pf_{parada_id}_{item['id']}_{versao}") or []
            vaga = max(MAX_FOTOS_POR_ITEM - len(fotos_salvas.get(item["id"], [])), 0)
            acima += max(len(arquivos) - vaga, 0)
            for arq in arquivos[:vaga]:
                try:
                    enviar_foto_parada(parada_id, item["id"], arq.getvalue(), usuario.id)
                    enviadas += 1
                    recem.add(item["id"])
                except Exception as e:
                    erros.append(f"{item['pergunta'][:50]}… ({e})")

        sem_foto = faltando_fotos(itens, respostas, fotos_salvas, recem)
        st.session_state[chave_estado] = {"faltando": faltando, "faltando_fotos": sem_foto}

        mensagens = []
        if not (qtd or descricao_salva or enviadas or erros or acima):
            mensagens.append(("info", "Nenhuma alteração nova para salvar."))
        else:
            if qtd:
                mensagens.append(("success", f"{qtd} resposta(s) salva(s)."))
            if descricao_salva:
                mensagens.append(("success", "Descrição da parada salva."))
            if enviadas:
                mensagens.append(("success", f"📷 {enviadas} foto(s) enviada(s)."))
            mensagens += [("error", f"Não consegui enviar uma foto: {e}") for e in erros]
            if acima:
                mensagens.append(("warning", f"{acima} foto(s) não enviada(s): limite de {MAX_FOTOS_POR_ITEM} por pergunta."))
        if sem_foto:
            mensagens.append(("warning", f"📷 Falta foto em {sem_foto} pergunta(s) — é obrigatória para concluir."))

        if enviadas:
            st.session_state[chave_versao] = versao + 1   # uploaders voltam vazios e as miniaturas novas aparecem
            st.session_state[chave_flash] = mensagens
            st.rerun()
        for tipo_msg, texto_msg in mensagens:
            getattr(st, tipo_msg)(texto_msg)

    estado = st.session_state[chave_estado]
    st.caption(
        (f"{estado['faltando']} pergunta(s) ainda sem resposta." if estado["faltando"] else "Todas as perguntas respondidas. ✅")
        + " (contagem atualizada ao apertar \"Atualizar respostas\")"
    )
    if estado["faltando_fotos"]:
        st.error(f"📷 Faltam fotos obrigatórias em {estado['faltando_fotos']} pergunta(s). Anexe e aperte \"Atualizar respostas\".")

    with st.expander("💬 Comentário geral (opcional)", expanded=bool(parada.get("comentario"))):
        comentario = st.text_area("Comentário", value=parada.get("comentario") or "", key=f"pcom_{parada_id}",
                                  label_visibility="collapsed")

    st.caption(f"Você vai concluir como **{usuario.nome}**. Depois de concluído não dá para editar.")
    with st.form(f"form_concluir_parada_{parada_id}"):
        concluir = st.form_submit_button("✅ Concluir checklist de parada", type="primary", use_container_width=True)
    if concluir:
        if estado["faltando"]:
            st.error(f"Ainda faltam {estado['faltando']} pergunta(s) sem resposta. Confirme com \"Atualizar respostas\" primeiro.")
        elif estado["faltando_fotos"]:
            st.error(f"Faltam fotos obrigatórias em {estado['faltando_fotos']} pergunta(s).")
        else:
            concluir_parada(parada_id, usuario.id, comentario.strip())
            st.success("Checklist de parada concluído. ✅")
            st.balloons()
            st.rerun()
