"""Visualização somente leitura de um checklist já registrado — usada no
"turno anterior" (dentro do preenchimento) e na página de Histórico.

Recebe o pacote de `models.obter_checklist_completo()`.
"""
import streamlit as st

from src.fotos import agrupar_por_item, baixar_miniatura
from src.itens import itens_da_ronda
from src.pdf_checklist import gerar_pdf_checklist
from src.turnos import LETRA_TURNO, formatar_datahora_local

ICONE_RESPOSTA = {"Sim": "✅", "Não": "❌", "N/A": "➖", "Texto": "📝"}


def _data_br(valor) -> str:
    texto = str(valor)[:10]
    try:
        ano, mes, dia = texto.split("-")
        return f"{dia}/{mes}/{ano}"
    except ValueError:
        return texto


def renderizar_checklist_somente_leitura(dados: dict, resumido: bool = False):
    """resumido=True: só o que importa pra passagem de turno — itens "Não"
    (com o que foi relatado), respostas de texto livre, itens com foto,
    atrasos justificados e comentário. resumido=False: todas as respostas."""
    if not dados:
        st.caption("Sem dados.")
        return

    ck = dados["checklist"]
    template = dados.get("template", {})
    itens = dados["itens"]
    horarios = dados["horarios"]
    respostas = dados["respostas"]
    justificativas = dados.get("justificativas_atraso", {})
    fotos_por_item = agrupar_por_item(dados.get("fotos", []))

    letra = LETRA_TURNO.get(ck.get("turno_id"), "")
    st.caption(
        f"**{template.get('area', '-')}** · {template.get('codigo', '-')} · "
        f"Turno **{dados.get('turno_nome', '-')}** ({letra}) · dia de produção **{_data_br(ck['data'])}**"
    )

    if ck["status"] == "completo":
        if ck.get("incompleto"):
            st.warning("Assinado **incompleto** — havia perguntas sem resposta quando foi assinado.")
        else:
            st.success("Concluído e assinado. ✅")
    else:
        st.info("Ainda **não assinado** (em andamento).")

    c1, c2, c3 = st.columns(3)
    c1.metric("Colaborador", dados.get("colaborador_nome", "-"))
    c2.metric("Assinado por", dados.get("supervisor_nome", "-"))
    c3.metric("Assinado em", formatar_datahora_local(ck.get("concluido_em")))

    contagem = {"Sim": 0, "Não": 0, "N/A": 0}
    for reg in respostas.values():
        if reg.get("resposta") in contagem:
            contagem[reg["resposta"]] += 1
    st.caption(f"✅ {contagem['Sim']} Sim · ❌ {contagem['Não']} Não · ➖ {contagem['N/A']} N/A")

    if ck.get("comentario"):
        st.info(f"💬 **Comentário geral:** {ck['comentario']}")

    algo_mostrado = False
    for horario in horarios:
        linhas = []
        for item, eh_filho in itens_da_ronda(itens, respostas, horario["id"]):
            reg = respostas.get((item["id"], horario["id"])) or {}
            resp = reg.get("resposta")
            obs = reg.get("observacao") or ""
            fotos = fotos_por_item.get((item["id"], horario["id"]), [])
            if resumido and not (resp in ("Não", "Texto") or fotos):
                continue
            linhas.append((item, resp, obs, fotos, eh_filho))

        just = justificativas.get(horario["id"])
        if not linhas and not just:
            continue

        algo_mostrado = True
        st.markdown(f"**🕒 Ronda das {horario['horario'][:5]}**")
        if just:
            st.caption(f"⏰ Justificativa do atraso: {just}")
        for item, resp, obs, fotos, eh_filho in linhas:
            icone = ICONE_RESPOSTA.get(resp, "⬜")
            recuo = "↳ " if eh_filho else ""
            if resp == "Texto":
                st.markdown(f"{recuo}{icone} **{item['pergunta']}**")
                st.write(obs or "—")
            else:
                st.markdown(f"{recuo}{icone} **{item['pergunta']}** — {resp or 'sem resposta'}")
                if obs:
                    st.caption(f"↳ {obs}")
            if fotos:
                colunas = st.columns(min(len(fotos), 3))
                for i, f in enumerate(fotos):
                    try:
                        # miniatura (~8 KB): a foto inteira só é baixada pro PDF
                        colunas[i % len(colunas)].image(baixar_miniatura(f["caminho"]), width=160)
                    except Exception:
                        colunas[i % len(colunas)].caption("(foto indisponível)")

    if resumido and not algo_mostrado and not ck.get("comentario"):
        st.caption("Sem ocorrências registradas nesse turno (nenhum 'Não', texto ou foto).")


def botao_pdf_checklist(checklist_id: str, logo_bytes, obter_dados, chave: str):
    """PDF sob demanda: só baixa as fotos inteiras e gera o arquivo quando
    a pessoa pede (antes gerava a cada vez que a tela abria — pesado e com
    muito tráfego do Storage). `obter_dados(checklist_id)` devolve o pacote
    completo (com fotos)."""
    chave_pdf = f"pdf_{chave}_{checklist_id}"
    if st.button("📄 Gerar PDF", key=f"gerar_{chave_pdf}"):
        with st.spinner("Gerando PDF…"):
            st.session_state[chave_pdf] = gerar_pdf_checklist(obter_dados(checklist_id), logo_bytes)
    if chave_pdf in st.session_state:
        st.download_button(
            "⬇️ Baixar PDF", data=st.session_state[chave_pdf],
            file_name=f"checklist_{checklist_id}.pdf", mime="application/pdf", key=f"baixar_{chave_pdf}",
        )
