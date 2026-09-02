"""Geração do PDF de resumo do Dashboard (cards + tabela do dia + top
perguntas com mais "Não"). Sem os gráficos (pizza/barras) — reproduzi-los
em PDF exigiria a lib kaleido só pra isso; os mesmos números aparecem em
tabela, que é mais fácil de ler impresso mesmo.
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


def _formatar_data(data_ref) -> str:
    if isinstance(data_ref, str):
        return data_ref
    return data_ref.strftime("%d/%m/%Y")


def gerar_pdf_dashboard(
    data_ref, area_escolhida: str, cards: dict, linhas: list[dict],
    contagem_resp: dict, top_perguntas_nao: list[tuple[str, int]],
    logo_bytes: bytes | None = None,
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=15 * mm, bottomMargin=15 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
    )

    estilos = getSampleStyleSheet()
    normal = estilos["Normal"]
    titulo_style = ParagraphStyle("TituloDash", parent=estilos["Heading1"], alignment=TA_CENTER, fontSize=14)
    subtitulo_style = ParagraphStyle("SubDash", parent=normal, fontName="Helvetica-Bold", fontSize=11)

    elementos = []

    if logo_bytes:
        try:
            elementos.append(RLImage(io.BytesIO(logo_bytes), width=28 * mm, height=19 * mm, kind="proportional"))
            elementos.append(Spacer(1, 2 * mm))
        except Exception:
            pass

    elementos.append(Paragraph("Dashboard de Checklists", titulo_style))
    elementos.append(Paragraph(
        f"Data: {_formatar_data(data_ref)} · Área: {area_escolhida}",
        ParagraphStyle("Filtro", parent=normal, alignment=TA_CENTER),
    ))
    elementos.append(Spacer(1, 5 * mm))

    # ---- Cards ----
    linhas_cards = [
        ["Checklists esperados", str(cards["esperados"])],
        ["Concluídos", str(cards["completos"])],
        ["Não iniciados", str(cards["nao_iniciados"])],
        ["Conformidade (Sim)", f"{cards['conformidade']:.0f}%" if cards["conformidade"] is not None else "—"],
        ["Pendências sem comentário", str(cards["pendencias_sem_comentario"])],
        ["'Não' em itens críticos", str(cards["criticas_nao"])],
    ]
    tabela_cards = Table(linhas_cards, colWidths=[LARGURA_UTIL * 0.6, LARGURA_UTIL * 0.4])
    tabela_cards.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elementos.append(tabela_cards)
    elementos.append(Spacer(1, 6 * mm))

    # ---- Distribuição das respostas ----
    sim = contagem_resp.get("Sim", 0)
    nao = contagem_resp.get("Não", 0)
    na = contagem_resp.get("N/A", 0)
    if sim + nao + na > 0:
        elementos.append(Paragraph("Distribuição das respostas", subtitulo_style))
        tabela_dist = Table(
            [["Sim", "Não", "N/A"], [str(sim), str(nao), str(na)]],
            colWidths=[LARGURA_UTIL / 3] * 3,
        )
        tabela_dist.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elementos.append(tabela_dist)
        elementos.append(Spacer(1, 6 * mm))

    # ---- Checklists do dia ----
    elementos.append(Paragraph("Checklists do dia", subtitulo_style))
    if not linhas:
        elementos.append(Paragraph("Nenhum checklist iniciado para essa data/área.", normal))
    else:
        cabecalho_linhas = list(linhas[0].keys())
        tabela_linhas = [cabecalho_linhas] + [
            [Paragraph(texto_seguro(linha[c]), normal) for c in cabecalho_linhas] for linha in linhas
        ]
        tabela_checklists = Table(tabela_linhas, repeatRows=1)
        tabela_checklists.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elementos.append(tabela_checklists)
    elementos.append(Spacer(1, 6 * mm))

    # ---- Top perguntas com mais "Não" ----
    elementos.append(Paragraph("Perguntas com mais 'Não'", subtitulo_style))
    if not top_perguntas_nao:
        elementos.append(Paragraph("Nenhuma resposta 'Não' registrada — ótimo sinal.", normal))
    else:
        linhas_top = [["Pergunta", "Ocorrências"]] + [
            [Paragraph(texto_seguro(pergunta), normal), str(qtd)]
            for pergunta, qtd in sorted(top_perguntas_nao, key=lambda x: -x[1])
        ]
        tabela_top = Table(linhas_top, colWidths=[LARGURA_UTIL - 30 * mm, 30 * mm])
        tabela_top.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elementos.append(tabela_top)

    doc.build(elementos)
    buf.seek(0)
    return buf.getvalue()
