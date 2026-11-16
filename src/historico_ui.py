"""Visualização somente leitura de um checklist já registrado — usada no
"turno anterior" (dentro do preenchimento) e na página de Histórico.

Recebe o pacote de `models.obter_checklist_completo()`.
"""
import base64
import html

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
    turma_col = dados.get("colaborador_turma")
    c1.metric("Colaborador", dados.get("colaborador_nome", "-") + (f" (Turma {turma_col})" if turma_col else ""))
    turma_sup = dados.get("supervisor_turma")
    c2.metric("Assinado por", dados.get("supervisor_nome", "-") + (f" (Turma {turma_sup})" if turma_sup else ""))
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


_CSS_FOLHA = (
    "<style>.folha{background:#fff;color:#111;border:1px solid #cfcfcf;border-radius:6px;padding:18px 20px;"
    "box-shadow:0 1px 4px rgba(0,0,0,.15);font-size:14px;line-height:1.35}"
    ".folha h3{margin:0 0 2px 0;font-size:18px;color:#111}"
    ".folha .meta{color:#444;font-size:13px;margin-bottom:10px}"
    ".folha table{width:100%;border-collapse:collapse;margin:6px 0 12px 0}"
    ".folha th{background:#e9eee2;color:#111;text-align:left;padding:5px 7px;border:1px solid #bbb;font-size:13px}"
    ".folha td{padding:5px 7px;border:1px solid #ccc;vertical-align:top;color:#111}"
    ".folha td.r{width:70px;text-align:center;font-weight:700}"
    ".folha .sim{color:#1b7a2f}.folha .nao{color:#c0281c}.folha .na{color:#666}"
    ".folha .filho td:first-child{padding-left:22px}"
    ".folha .ronda{font-weight:700;margin-top:8px}"
    ".folha img{height:70px;margin:3px 4px 0 0;border:1px solid #bbb;border-radius:3px}"
    ".folha .ass{display:flex;gap:30px;margin-top:14px}.folha .ass div{flex:1;border-top:1px solid #555;padding-top:3px;font-size:12px}"
    "</style>"
)


def _miniatura_html(caminho: str) -> str:
    try:
        b64 = base64.b64encode(baixar_miniatura(caminho)).decode()
        return f'<img src="data:image/jpeg;base64,{b64}">'
    except Exception:
        return "<i>(foto indisponível)</i>"


def renderizar_checklist_folha(dados: dict):
    """Mostra o checklist na tela como uma 'folha' (igual ao PDF, em HTML) —
    dá pra ler direto sem baixar nada. O PDF fica só como opção."""
    if not dados:
        st.caption("Sem dados.")
        return
    esc = html.escape
    ck = dados["checklist"]
    template = dados.get("template", {})
    itens, horarios = dados["itens"], dados["horarios"]
    respostas = dados["respostas"]
    justificativas = dados.get("justificativas_atraso", {})
    fotos_por_item = agrupar_por_item(dados.get("fotos", []))
    letra = LETRA_TURNO.get(ck.get("turno_id"), "")

    def _pessoa(nome_chave, turma_chave):
        t = dados.get(turma_chave)
        return esc(str(dados.get(nome_chave, "-"))) + (f" (Turma {esc(str(t))})" if t else "")

    if ck["status"] == "completo":
        situacao = "⚠️ Assinado incompleto" if ck.get("incompleto") else "✅ Concluído e assinado"
    else:
        situacao = "🟡 Em andamento (não assinado)"

    partes = [_CSS_FOLHA, '<div class="folha">',
              f"<h3>{esc(str(template.get('titulo') or template.get('area', '-')))}</h3>",
              f'<div class="meta">{esc(str(template.get("codigo", "-")))} · {esc(str(template.get("area", "-")))} · '
              f'Turno {esc(str(dados.get("turno_nome", "-")))} ({letra}) · Dia de produção {_data_br(ck["data"])} · {situacao}</div>',
              f'<div class="meta">Colaborador: <b>{_pessoa("colaborador_nome", "colaborador_turma")}</b></div>']

    for horario in horarios:
        linhas = []
        for item, eh_filho in itens_da_ronda(itens, respostas, horario["id"]):
            reg = respostas.get((item["id"], horario["id"])) or {}
            linhas.append((item, reg, eh_filho))
        if not linhas:
            continue
        partes.append(f'<div class="ronda">🕒 Ronda das {esc(horario["horario"][:5])}</div>')
        just = justificativas.get(horario["id"])
        if just:
            partes.append(f'<div class="meta">⏰ Justificativa do atraso: {esc(str(just))}</div>')
        partes.append("<table><tr><th>Item</th><th>Resposta</th></tr>")
        for item, reg, eh_filho in linhas:
            resp, obs = reg.get("resposta"), reg.get("observacao") or ""
            fotos = fotos_por_item.get((item["id"], horario["id"]), [])
            classe = {"Sim": "sim", "Não": "nao", "N/A": "na"}.get(resp, "")
            if resp == "Texto":
                celula = esc(obs) or "—"
            else:
                celula = esc(resp or "—")
            detalhe = ""
            if obs and resp != "Texto":
                detalhe += f'<br><i>{esc(obs)}</i>'
            if fotos:
                detalhe += "<br>" + "".join(_miniatura_html(f["caminho"]) for f in fotos)
            marca = "&gt; " if eh_filho else ""
            partes.append(
                f'<tr class="{"filho" if eh_filho else ""}"><td>{marca}{esc(item["pergunta"])}{detalhe}</td>'
                f'<td class="r {classe}">{celula}</td></tr>'
            )
        partes.append("</table>")

    if ck.get("comentario"):
        partes.append(f'<div><b>💬 Comentário geral:</b> {esc(ck["comentario"])}</div>')
    partes.append(
        '<div class="ass">'
        f'<div>Colaborador<br><b>{_pessoa("colaborador_nome", "colaborador_turma")}</b></div>'
        f'<div>Assinado por<br><b>{_pessoa("supervisor_nome", "supervisor_turma")}</b><br>'
        f'{esc(formatar_datahora_local(ck.get("concluido_em")))}</div></div></div>'
    )
    # sem linhas em branco/indentação: o markdown não pode virar bloco de código
    st.markdown("".join(partes), unsafe_allow_html=True)


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
