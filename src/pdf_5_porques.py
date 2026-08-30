"""Geração do PDF do Formulário 5 Porquês — Parada de Linha.

Layout espelha o formulário físico da Guararapes: cabeçalho com logo,
aviso da janela de tempo (30min–1h30min), dados da parada, descrição do
problema, tabela Etapa/Pergunta/Resposta com os 5 porquês, causa raiz,
plano de ação (N linhas), verificação de eficácia e evidências.
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

LARGURA_UTIL = 170 * mm  # A4 (210mm) menos 20mm de margem total


def _formatar_tempo(minutos):
    if minutos is None:
        return "-"
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def _formatar_data(valor):
    if not valor:
        return "-"
    if isinstance(valor, str):
        partes = valor.split("-")
        if len(partes) == 3:
            return f"{partes[2]}/{partes[1]}/{partes[0]}"
        return valor
    return valor.strftime("%d/%m/%Y")


def gerar_pdf_5_porques(analise: dict, acoes: list[dict], logo_bytes: bytes | None = None) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=15 * mm, bottomMargin=15 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
    )

    estilos = getSampleStyleSheet()
    normal = estilos["Normal"]
    titulo_style = ParagraphStyle("Titulo5P", parent=estilos["Heading1"], alignment=TA_CENTER, fontSize=14)
    aviso_style = ParagraphStyle("Aviso5P", parent=normal, alignment=TA_CENTER, fontSize=9)
    rodape_style = ParagraphStyle("Rodape5P", parent=normal, fontName="Helvetica-Oblique", fontSize=8)
    cabecalho_titulo_style = ParagraphStyle("SubTitulo5P", parent=normal, fontName="Helvetica-Bold", fontSize=11)

    elementos = []

    if logo_bytes:
        try:
            elementos.append(RLImage(io.BytesIO(logo_bytes), width=30 * mm, height=20 * mm, kind="proportional"))
            elementos.append(Spacer(1, 2 * mm))
        except Exception:
            pass

    elementos.append(Paragraph("FORMULÁRIO 5 PORQUÊS – PARADA DE LINHA", titulo_style))
    elementos.append(Spacer(1, 3 * mm))

    aviso = Table(
        [[Paragraph("Responder esse formulário para paradas entre 30 minutos e 1h:30min", aviso_style)]],
        colWidths=[LARGURA_UTIL],
    )
    aviso.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF3B0")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elementos.append(aviso)
    elementos.append(Spacer(1, 5 * mm))

    responsavel = analise.get("responsavel") or {}
    cabecalho = [
        [Paragraph(f"<b>Data:</b> {_formatar_data(analise.get('data_parada'))}", normal),
         Paragraph(f"<b>Equipamento:</b> {analise.get('equipamento') or '-'}", normal)],
        [Paragraph(f"<b>Setor:</b> {analise.get('setor') or '-'}", normal),
         Paragraph(f"<b>Tempo de Parada:</b> {_formatar_tempo(analise.get('tempo_parada_minutos'))}", normal)],
        [Paragraph(f"<b>Resp. pela Análise:</b> {responsavel.get('nome', '-')}", normal),
         Paragraph(f"<b>Função:</b> {(responsavel.get('papel') or '-').capitalize()}", normal)],
    ]
    tabela_cabecalho = Table(cabecalho, colWidths=[LARGURA_UTIL / 2, LARGURA_UTIL / 2])
    tabela_cabecalho.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tabela_cabecalho)
    elementos.append(Spacer(1, 4 * mm))

    elementos.append(Paragraph("Descrição do Problema — o que ocorreu:", cabecalho_titulo_style))
    elementos.append(Paragraph((analise.get("descricao_problema") or "-").replace("\n", "<br/>"), normal))
    elementos.append(Spacer(1, 5 * mm))

    perguntas_porque = {
        "problema": "O que aconteceu?",
        "porque_1": "Por que aconteceu?",
        "porque_2": "Por que isso aconteceu?",
        "porque_3": "Por que isso aconteceu?",
        "porque_4": "Por que isso aconteceu?",
        "porque_5": "Por que isso aconteceu?",
    }
    etiquetas_etapa = {
        "problema": "Problema", "porque_1": "1º Porquê", "porque_2": "2º Porquê",
        "porque_3": "3º Porquê", "porque_4": "4º Porquê", "porque_5": "5º Porquê",
    }
    linhas_porque = [["Etapa", "Pergunta", "Resposta"]]
    for chave, pergunta in perguntas_porque.items():
        linhas_porque.append([
            etiquetas_etapa[chave], pergunta, Paragraph(analise.get(chave) or "", normal),
        ])

    tabela_porques = Table(linhas_porque, colWidths=[22 * mm, 43 * mm, LARGURA_UTIL - 65 * mm], repeatRows=1)
    tabela_porques.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elementos.append(tabela_porques)
    elementos.append(Spacer(1, 5 * mm))

    elementos.append(Paragraph("Causa Raiz Identificada", cabecalho_titulo_style))
    elementos.append(Paragraph(analise.get("causa_raiz") or "-", normal))
    elementos.append(Spacer(1, 5 * mm))

    elementos.append(Paragraph("Plano de Ação", cabecalho_titulo_style))
    linhas_acoes = [["Ação Corretiva", "Responsável", "Prazo"]]
    for acao in acoes:
        linhas_acoes.append([
            Paragraph(acao.get("acao_corretiva") or "", normal),
            acao.get("responsavel") or "",
            _formatar_data(acao.get("prazo")) if acao.get("prazo") else "",
        ])
    while len(linhas_acoes) - 1 < 5:  # completa com linhas em branco, igual ao papel
        linhas_acoes.append(["", "", ""])

    tabela_acoes = Table(linhas_acoes, colWidths=[100 * mm, 40 * mm, 30 * mm], repeatRows=1)
    tabela_acoes.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elementos.append(tabela_acoes)
    elementos.append(Spacer(1, 6 * mm))

    eficaz = analise.get("eficaz")
    marca_sim = "[X]" if eficaz is True else "[ ]"
    marca_nao = "[X]" if eficaz is False else "[ ]"
    elementos.append(Paragraph(
        f"<b>Verificação da Eficácia</b> (Coordenador de produção): "
        f"{marca_sim} Sim &nbsp;&nbsp;&nbsp; {marca_nao} Não",
        normal,
    ))
    elementos.append(Spacer(1, 3 * mm))
    elementos.append(Paragraph(f"<b>Evidências:</b> {analise.get('evidencias') or ''}", normal))
    elementos.append(Spacer(1, 6 * mm))

    elementos.append(Paragraph(
        "Se não for eficaz ou se o problema for recorrente, abrir análise de falha no Qualiex.",
        rodape_style,
    ))

    doc.build(elementos)
    buf.seek(0)
    return buf.getvalue()
