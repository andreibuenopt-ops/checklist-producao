"""PDF e CSV do relatório mensal de realização dos checklists.
Recebe o dicionário de `aderencia.montar_relatorio()`. Sem gráficos
(evita dependência extra) — só tabelas, no mesmo padrão dos outros PDFs."""
import csv
import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image as RLImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.pdf_utils import texto_seguro

LARGURA = 170 * mm


def _pct(v) -> str:
    return "—" if v is None else f"{v * 100:.0f}%"


def _tabela(dados, larguras, destaque_ultima_coluna=False):
    t = Table(dados, colWidths=larguras, repeatRows=1)
    estilo = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]
    t.setStyle(TableStyle(estilo))
    return t


def gerar_pdf_relatorio_mensal(rel: dict, titulo_periodo: str, logo_bytes: bytes | None = None) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=15 * mm, bottomMargin=15 * mm,
                            leftMargin=20 * mm, rightMargin=20 * mm)
    estilos = getSampleStyleSheet()
    normal = ParagraphStyle("n", parent=estilos["Normal"], fontSize=8)
    titulo = ParagraphStyle("t", parent=estilos["Heading1"], alignment=TA_CENTER, fontSize=15)
    sub = ParagraphStyle("s", parent=normal, fontName="Helvetica-Bold", fontSize=11, spaceBefore=8, spaceAfter=3)

    el = []
    if logo_bytes:
        try:
            el += [RLImage(io.BytesIO(logo_bytes), width=28 * mm, height=19 * mm, kind="proportional"), Spacer(1, 2 * mm)]
        except Exception:
            pass
    el += [Paragraph("Relatório de realização dos checklists", titulo),
           Paragraph(f"Período: {titulo_periodo}", ParagraphStyle("p", parent=normal, alignment=TA_CENTER, fontSize=10)),
           Spacer(1, 4 * mm)]

    g = rel["geral"]
    el.append(Paragraph("Resumo geral", sub))
    el.append(_tabela([
        ["Indicador", "Valor"],
        ["Checklists esperados (turnos já encerrados)", str(g["esperados"])],
        ["Realizados (assinados)", str(g["realizados"])],
        ["Não realizados", str(g["nao_realizados"])],
        ["Aderência geral", _pct(g["aderencia"])],
        ["Assinados incompletos", str(g["incompletos"])],
        ["Respostas \"Não\" registradas", str(rel["total_nao"])],
        ["Rondas com atraso justificado", str(rel["total_atrasos"])],
    ], [110 * mm, 60 * mm]))

    el.append(Paragraph("Aderência por turno", sub))
    linhas = [["Turno", "Esperados", "Realizados", "Não realizados", "Aderência"]]
    linhas += [[t["turno"], t["esperados"], t["realizados"], t["nao_realizados"], _pct(t["aderencia"])] for t in rel["por_turno"]]
    el.append(_tabela(linhas, [50 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm]))

    el.append(Paragraph("Aderência por checklist (do que mais fica sem preencher ao que menos)", sub))
    linhas = [["Checklist", "Esperados", "Realizados", "Não realiz.", "Aderência"]]
    linhas += [[Paragraph(texto_seguro(c["area"]), normal), c["esperados"], c["realizados"],
                c["nao_realizados"], _pct(c["aderencia"])] for c in rel["por_checklist"]]
    el.append(_tabela(linhas, [74 * mm, 24 * mm, 24 * mm, 24 * mm, 24 * mm]))

    el.append(Paragraph("Checklist x turno que mais ficam sem preencher (15 piores)", sub))
    linhas = [["Checklist", "Turno", "Esperados", "Realizados", "Aderência"]]
    linhas += [[Paragraph(texto_seguro(l["area"]), normal), l["turno"], l["esperados"], l["realizados"], _pct(l["aderencia"])]
               for l in rel["ranking"][:15]]
    el.append(_tabela(linhas, [64 * mm, 30 * mm, 24 * mm, 24 * mm, 28 * mm]))

    if rel["itens_mais_nao"]:
        el.append(Paragraph("Itens com mais respostas \"Não\"", sub))
        linhas = [["Checklist", "Pergunta", "Qtd."]]
        linhas += [[Paragraph(texto_seguro(i["area"]), normal), Paragraph(texto_seguro(i["pergunta"]), normal), i["qtd"]]
                   for i in rel["itens_mais_nao"]]
        el.append(_tabela(linhas, [40 * mm, 110 * mm, 20 * mm]))

    doc.build(el)
    return buf.getvalue()


def gerar_csv_relatorio(rel: dict) -> bytes:
    """Uma linha por (checklist, turno) — dá pra filtrar/pivotar no Excel."""
    saida = io.StringIO()
    w = csv.writer(saida, delimiter=";")
    w.writerow(["Checklist", "Codigo", "Turno", "Esperados", "Realizados", "Nao realizados",
                "Assinados incompletos", "Aderencia (%)"])
    for l in sorted(rel["linhas"], key=lambda x: (x["area"], x["turno_id"])):
        taxa = "" if l["aderencia"] is None else f"{l['aderencia'] * 100:.1f}".replace(".", ",")
        w.writerow([l["area"], l["codigo"], l["turno"], l["esperados"], l["realizados"],
                    l["nao_realizados"], l["incompletos"], taxa])
    return ("\ufeff" + saida.getvalue()).encode("utf-8")  # BOM: Excel abre os acentos certo
