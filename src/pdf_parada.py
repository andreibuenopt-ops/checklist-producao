"""PDF de um checklist de PARADA DE LINHA: perguntas, respostas, o que foi
relatado e as fotos de cada pergunta. Mesmo padrão visual dos outros PDFs."""
import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image as RLImage, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.paradas import fotos_por_pergunta
from src.pdf_checklist import COR_FUNDO_RESPOSTA, LARGURA_UTIL
from src.pdf_utils import texto_seguro
from src.turnos import formatar_datahora_local


def _data(valor) -> str:
    t = str(valor)[:10]
    return f"{t[8:10]}/{t[5:7]}/{t[:4]}"


def _com_turma(nome: str, turma) -> str:
    return f"{texto_seguro(nome)}" + (f" (Turma {turma})" if turma else "")


def gerar_pdf_parada(dados: dict, logo_bytes: bytes | None = None) -> bytes:
    p = dados["parada"]
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=15 * mm, bottomMargin=15 * mm, leftMargin=20 * mm, rightMargin=20 * mm)
    estilos = getSampleStyleSheet()
    normal = estilos["Normal"]
    titulo = ParagraphStyle("t", parent=estilos["Heading1"], alignment=TA_CENTER, fontSize=15)
    sub = ParagraphStyle("s", parent=normal, fontName="Helvetica-Bold", fontSize=11, spaceBefore=6)

    el = []
    if logo_bytes:
        try:
            el += [RLImage(io.BytesIO(logo_bytes), width=28 * mm, height=19 * mm, kind="proportional"), Spacer(1, 2 * mm)]
        except Exception:
            pass
    el += [Paragraph(f"Checklist de {texto_seguro(dados['tipo_nome'])}", titulo), Spacer(1, 3 * mm)]

    status = "Concluído" if p["status"] == "completo" else "Em andamento"
    cab = [
        [Paragraph(f"<b>Turno:</b> {dados['turno_nome']}", normal), Paragraph(f"<b>Dia de produção:</b> {_data(p['data'])}", normal)],
        [Paragraph(f"<b>Iniciada em:</b> {formatar_datahora_local(p.get('iniciada_em'))}", normal),
         Paragraph(f"<b>Status:</b> {status}", normal)],
        [Paragraph(f"<b>Aberta por:</b> {_com_turma(dados['colaborador_nome'], dados.get('colaborador_turma'))}", normal),
         Paragraph(f"<b>Concluída por:</b> {_com_turma(dados['supervisor_nome'], dados.get('supervisor_turma'))}", normal)],
        [Paragraph(f"<b>Concluída em:</b> {formatar_datahora_local(p.get('concluido_em'))}", normal), Paragraph("", normal)],
    ]
    tabela_cab = Table(cab, colWidths=[LARGURA_UTIL / 2] * 2)
    tabela_cab.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    el += [tabela_cab]

    if p.get("descricao"):
        el += [Paragraph("O que aconteceu", sub), Paragraph(texto_seguro(p["descricao"]).replace("\n", "<br/>"), normal)]

    el += [Paragraph("Perguntas", sub), Spacer(1, 2 * mm)]
    fotos = fotos_por_pergunta(dados.get("fotos", []))
    linhas, fundos = [["Pergunta", "Resposta"]], []
    for idx, item in enumerate(dados["itens"], start=1):
        reg = dados["respostas"].get(item["id"]) or {}
        resp = reg.get("resposta") or "-"
        texto = texto_seguro(item["pergunta"])
        if reg.get("observacao"):
            texto += f'<br/><font size=8 color="#555555"><b>Relato:</b> {texto_seguro(reg["observacao"])}</font>'
        n = len(fotos.get(item["id"], []))
        if n:
            texto += f'<br/><font size=8 color="#555555">{n} foto(s) anexada(s)</font>'
        linhas.append([Paragraph(texto, normal), resp])
        if resp in COR_FUNDO_RESPOSTA:
            fundos.append((idx, COR_FUNDO_RESPOSTA[resp]))
    t = Table(linhas, colWidths=[LARGURA_UTIL - 28 * mm, 28 * mm], repeatRows=1)
    estilo = [("GRID", (0, 0), (-1, -1), 0.5, colors.black), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
              ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("ALIGN", (1, 0), (1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
    estilo += [("BACKGROUND", (1, i), (1, i), cor) for i, cor in fundos]
    t.setStyle(TableStyle(estilo))
    el.append(t)

    com_foto = [(i, fotos[i["id"]]) for i in dados["itens"] if fotos.get(i["id"])]
    if com_foto:
        el += [Spacer(1, 4 * mm), Paragraph("Fotos", sub), Spacer(1, 2 * mm)]
        for item, lista in com_foto:
            for f in lista:
                if not f.get("bytes"):
                    continue
                try:
                    img = RLImage(io.BytesIO(f["bytes"]))
                    escala = min(80 * mm / img.imageWidth, 60 * mm / img.imageHeight, 1.0)
                    img.drawWidth, img.drawHeight = img.imageWidth * escala, img.imageHeight * escala
                except Exception:
                    continue
                bloco = Table([[img], [Paragraph(texto_seguro(item["pergunta"])[:120], normal)]], colWidths=[85 * mm])
                bloco.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
                el += [KeepTogether(bloco), Spacer(1, 3 * mm)]

    el += [Paragraph("Comentários", sub), Paragraph(texto_seguro(p.get("comentario")) or "—", normal)]
    doc.build(el)
    return buf.getvalue()
