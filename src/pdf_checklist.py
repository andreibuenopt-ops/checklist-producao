"""Geração do PDF de um checklist já preenchido — todas as respostas por
horário, comentário e quem assinou. Mesmo padrão visual dos outros PDFs
do sistema (src/pdf_5_porques.py).
"""
import io

from src.itens import itens_da_ronda
from src.turnos import formatar_datahora_local
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as RLImage,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.pdf_utils import texto_seguro

LARGURA_UTIL = 170 * mm

COR_FUNDO_RESPOSTA = {
    "Sim": colors.HexColor("#dff0d8"),
    "Não": colors.HexColor("#f2dede"),
    "N/A": colors.HexColor("#eeeeee"),
}
STATUS_LABEL = {"completo": "Completo", "em_andamento": "Em andamento", "pendente": "Pendente"}


def _formatar_data(valor) -> str:
    if not valor:
        return "-"
    if isinstance(valor, str):
        partes = valor.split("-")
        if len(partes) == 3:
            return f"{partes[2]}/{partes[1]}/{partes[0]}"
        return valor
    return valor.strftime("%d/%m/%Y")


def _formatar_datahora(valor) -> str:
    return formatar_datahora_local(valor)


def gerar_pdf_checklist(dados: dict, logo_bytes: bytes | None = None) -> bytes:
    checklist = dados["checklist"]
    template = dados["template"]
    itens = dados["itens"]
    horarios = dados["horarios"]
    respostas = dados["respostas"]
    justificativas_atraso = dados.get("justificativas_atraso", {})

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=15 * mm, bottomMargin=15 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
    )

    estilos = getSampleStyleSheet()
    normal = estilos["Normal"]
    titulo_style = ParagraphStyle("TituloChecklist", parent=estilos["Heading1"], alignment=TA_CENTER, fontSize=14)
    subtitulo_style = ParagraphStyle("SubChecklist", parent=normal, fontName="Helvetica-Bold", fontSize=11)

    elementos = []

    if logo_bytes:
        try:
            elementos.append(RLImage(io.BytesIO(logo_bytes), width=28 * mm, height=19 * mm, kind="proportional"))
            elementos.append(Spacer(1, 2 * mm))
        except Exception:
            pass

    elementos.append(Paragraph(template.get("titulo", "Checklist"), titulo_style))
    elementos.append(Spacer(1, 3 * mm))

    status = checklist.get("status", "pendente")
    cabecalho = [
        [Paragraph(f"<b>Área:</b> {template.get('area', '-')}", normal),
         Paragraph(f"<b>Código:</b> {template.get('codigo', '-')}", normal)],
        [Paragraph(f"<b>Data:</b> {_formatar_data(checklist.get('data'))}", normal),
         Paragraph(f"<b>Turno:</b> {dados.get('turno_nome', '-')}", normal)],
        [Paragraph(
            f"<b>Status:</b> {STATUS_LABEL.get(status, status)}"
            + (' <font color="#aa3333"><b>(assinado INCOMPLETO)</b></font>' if checklist.get("incompleto") else ""),
            normal),
         Paragraph(f"<b>Concluído em:</b> {_formatar_datahora(checklist.get('concluido_em'))}", normal)],
        [Paragraph(f"<b>Colaborador:</b> {dados.get('colaborador_nome', '-')}"
                   + (f" (Turma {dados['colaborador_turma']})" if dados.get("colaborador_turma") else ""), normal),
         Paragraph(f"<b>Assinado por:</b> {dados.get('supervisor_nome', '-')}"
                   + (f" (Turma {dados['supervisor_turma']})" if dados.get("supervisor_turma") else ""), normal)],
    ]
    tabela_cabecalho = Table(cabecalho, colWidths=[LARGURA_UTIL / 2, LARGURA_UTIL / 2])
    tabela_cabecalho.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tabela_cabecalho)
    elementos.append(Spacer(1, 5 * mm))

    for horario in horarios:
        titulo_ronda = f"Ronda das {horario['horario'][:5]}"
        justificativa_ronda = texto_seguro(justificativas_atraso.get(horario["id"], ""))
        if justificativa_ronda:
            titulo_ronda += " — ATRASADA"
        elementos.append(Paragraph(titulo_ronda, subtitulo_style))
        if justificativa_ronda:
            elementos.append(Paragraph(
                f'<font size=9 color="#aa3333">'
                f"<b>Justificativa do atraso:</b> {justificativa_ronda}</font>",
                normal,
            ))
        elementos.append(Spacer(1, 2 * mm))

        linhas = [["Item", "Resposta"]]
        cores_fundo = []  # (linha, cor) — linha 0 é o cabeçalho, respostas começam em 1
        for idx, (item, eh_filho) in enumerate(itens_da_ronda(itens, respostas, horario["id"]), start=1):
            registro = respostas.get((item["id"], horario["id"])) or {}
            resposta = registro.get("resposta") or "-"
            observacao = texto_seguro(registro.get("observacao") or "")

            texto_item = ("&nbsp;&nbsp;&nbsp;&gt; " if eh_filho else "") + texto_seguro(item["pergunta"])
            if item.get("tipo_resposta") == "texto_livre":
                resposta_exibida = observacao or "-"
                linhas.append([Paragraph(texto_item, normal), Paragraph(resposta_exibida, normal)])
                continue

            if resposta == "Não" and observacao:
                texto_item += (
                    f'<br/><font size=8 color="#555555">'
                    f"<b>Observação:</b> {observacao}</font>"
                )

            linhas.append([
                Paragraph(texto_item, normal),
                resposta,
            ])
            if resposta in COR_FUNDO_RESPOSTA:
                cores_fundo.append((idx, COR_FUNDO_RESPOSTA[resposta]))

        tabela = Table(linhas, colWidths=[LARGURA_UTIL - 30 * mm, 30 * mm], repeatRows=1)
        estilo_tabela = [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        for linha_idx, cor in cores_fundo:
            estilo_tabela.append(("BACKGROUND", (1, linha_idx), (1, linha_idx), cor))
        tabela.setStyle(TableStyle(estilo_tabela))
        elementos.append(tabela)
        elementos.append(Spacer(1, 5 * mm))

    # Fotos anexadas (qualquer item/ronda) — vêm com os bytes já baixados.
    fotos = dados.get("fotos") or []
    if fotos:
        elementos.append(Spacer(1, 4 * mm))
        elementos.append(Paragraph("Fotos anexadas", subtitulo_style))
        elementos.append(Spacer(1, 2 * mm))
        perguntas = {i["id"]: i["pergunta"] for i in itens}
        rondas = {h["id"]: h["horario"][:5] for h in horarios}
        for f in fotos:
            if not f.get("bytes"):
                continue
            legenda = (
                f"Ronda {rondas.get(f['horario_id'], '-')} — "
                f"{texto_seguro(perguntas.get(f['item_id'], ''))[:110]}"
            )
            try:
                img = RLImage(io.BytesIO(f["bytes"]))
                escala = min(80 * mm / img.imageWidth, 60 * mm / img.imageHeight, 1.0)
                img.drawWidth, img.drawHeight = img.imageWidth * escala, img.imageHeight * escala
            except Exception:
                continue
            bloco = Table([[img], [Paragraph(legenda, normal)]], colWidths=[85 * mm])
            bloco.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
            elementos.append(KeepTogether(bloco))
            elementos.append(Spacer(1, 3 * mm))

    elementos.append(Paragraph("Comentários", subtitulo_style))
    comentario_limpo = texto_seguro(checklist.get("comentario")) or "—"
    elementos.append(Paragraph(comentario_limpo.replace("\n", "<br/>"), normal))

    doc.build(elementos)
    buf.seek(0)
    return buf.getvalue()
