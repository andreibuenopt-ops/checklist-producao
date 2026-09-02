"""Geração do PDF de um checklist já preenchido — todas as respostas por
horário, comentário e quem assinou. Mesmo padrão visual dos outros PDFs
do sistema (src/pdf_5_porques.py).
"""
import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as RLImage,
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
    if not valor:
        return "-"
    return str(valor)[:16].replace("T", " ")


def gerar_pdf_checklist(dados: dict, logo_bytes: bytes | None = None) -> bytes:
    checklist = dados["checklist"]
    template = dados["template"]
    itens = dados["itens"]
    horarios = dados["horarios"]
    respostas = dados["respostas"]

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
        [Paragraph(f"<b>Status:</b> {STATUS_LABEL.get(status, status)}", normal),
         Paragraph(f"<b>Concluído em:</b> {_formatar_datahora(checklist.get('concluido_em'))}", normal)],
        [Paragraph(f"<b>Colaborador:</b> {dados.get('colaborador_nome', '-')}", normal),
         Paragraph(f"<b>Assinado por:</b> {dados.get('supervisor_nome', '-')}", normal)],
    ]
    tabela_cabecalho = Table(cabecalho, colWidths=[LARGURA_UTIL / 2, LARGURA_UTIL / 2])
    tabela_cabecalho.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tabela_cabecalho)
    elementos.append(Spacer(1, 5 * mm))

    for horario in horarios:
        elementos.append(Paragraph(f"Ronda das {horario['horario'][:5]}", subtitulo_style))
        elementos.append(Spacer(1, 2 * mm))

        linhas = [["Item", "Resposta"]]
        cores_fundo = []  # (linha, cor) — linha 0 é o cabeçalho, respostas começam em 1
        for idx, item in enumerate(itens, start=1):
            resposta = respostas.get((item["id"], horario["id"])) or "-"
            linhas.append([
                Paragraph(texto_seguro(item["pergunta"]), normal),
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

    elementos.append(Paragraph("Comentários", subtitulo_style))
    comentario_limpo = texto_seguro(checklist.get("comentario")) or "—"
    elementos.append(Paragraph(comentario_limpo.replace("\n", "<br/>"), normal))

    doc.build(elementos)
    buf.seek(0)
    return buf.getvalue()
