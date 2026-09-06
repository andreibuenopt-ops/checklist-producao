"""PDF do checklist do Ecoresinator — grade de leituras por bico +
parâmetros globais da cozinha de cola. Mesmo padrão visual dos outros
PDFs do sistema."""
import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
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
from src.turnos import formatar_datahora_local

LARGURA_UTIL = 257 * mm  # A4 paisagem, margens de 20mm

RES_GLOBAIS_LABELS = {
    "rodizio_ligado": "Rodízio ligado?",
    "flush_ligado": "Flush ligado?",
    "pressao_bomba_resina": "Pressão bomba resina",
    "pressao_coletor_resina": "Pressão coletor resina",
    "pressao_bomba_agua": "Pressão bomba água",
    "pressao_coletor_agua": "Pressão coletor água",
    "pressao_vapor_coletor": "Pressão vapor coletor",
    "vazao_resina_bomba": "Vazão resina na bomba (L/min)",
    "valvula_proporcional_auto": "Válvula proporcional em automático?",
    "agulhas_force_abertura": "Agulhas com \"force\" de abertura?",
    "bomba_resina_manutencao": "Alguma bomba de resina em manutenção?",
    "bomba_resina_em_uso": "Bomba de resina em uso",
    "bomba_parafina_em_uso": "Bomba de parafina em uso",
    "bicos_em_manutencao": "Bicos em manutenção",
    "bicos_em_producao": "Bicos em produção",
}


def _fmt(v) -> str:
    return "-" if v in (None, "") else str(v)


def gerar_pdf_ecoresinator(dados: dict, logo_bytes: bytes | None = None) -> bytes:
    checklist = dados["checklist"]

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        topMargin=12 * mm, bottomMargin=12 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
    )
    estilos = getSampleStyleSheet()
    normal = estilos["Normal"]
    titulo_style = ParagraphStyle("Titulo", parent=estilos["Heading1"], alignment=TA_CENTER, fontSize=14)
    subtitulo_style = ParagraphStyle("Sub", parent=normal, fontName="Helvetica-Bold", fontSize=11)

    elementos = []
    if logo_bytes:
        try:
            elementos.append(RLImage(io.BytesIO(logo_bytes), width=28 * mm, height=19 * mm, kind="proportional"))
            elementos.append(Spacer(1, 2 * mm))
        except Exception:
            pass

    elementos.append(Paragraph("Rotina de Inspeção — Ecoresinator (Cozinha de Cola)", titulo_style))
    elementos.append(Spacer(1, 3 * mm))

    cabecalho = [
        [Paragraph(f"<b>Data:</b> {_fmt(checklist.get('data'))}", normal),
         Paragraph(f"<b>Turno:</b> {dados.get('turno_nome', '-')}", normal),
         Paragraph(f"<b>Horário real:</b> {_fmt(checklist.get('horario_real'))}", normal)],
        [Paragraph(f"<b>Status:</b> {checklist.get('status', '-')}", normal),
         Paragraph(f"<b>Concluído em:</b> {formatar_datahora_local(checklist.get('concluido_em'))}", normal),
         Paragraph("", normal)],
        [Paragraph(f"<b>Colaborador:</b> {dados.get('colaborador_nome', '-')}", normal),
         Paragraph(f"<b>Assinado por:</b> {dados.get('supervisor_nome', '-')}", normal),
         Paragraph("", normal)],
    ]
    tabela_cab = Table(cabecalho, colWidths=[LARGURA_UTIL / 3] * 3)
    tabela_cab.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    elementos.append(tabela_cab)
    elementos.append(Spacer(1, 4 * mm))

    # Grade por bico
    elementos.append(Paragraph("Leituras por bico", subtitulo_style))
    elementos.append(Spacer(1, 1 * mm))
    cabecalho_bicos = ["Bico", "Vazão\n(L/min)", "Eficiência\n(%)", "Abertura\nválvula (%)", "Falha\n3 vias?", "Falha\nagulha?", "Falha\nvazão?"]
    linhas_bicos = [cabecalho_bicos]
    cores_fundo = []
    for idx, b in enumerate(dados.get("leituras_bicos", []), start=1):
        tem_falha = "Sim" in (b.get("falha_3_vias"), b.get("falha_agulha"), b.get("falha_vazao"))
        linhas_bicos.append([
            str(b.get("numero", idx)),
            _fmt(b.get("vazao_lmin")), _fmt(b.get("eficiencia_pct")), _fmt(b.get("abertura_valvula_pct")),
            _fmt(b.get("falha_3_vias")), _fmt(b.get("falha_agulha")), _fmt(b.get("falha_vazao")),
        ])
        if tem_falha:
            cores_fundo.append(idx)

    largura_bico = LARGURA_UTIL / 7
    tabela_bicos = Table(linhas_bicos, colWidths=[largura_bico] * 7, repeatRows=1)
    estilo_bicos = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    for idx in cores_fundo:
        estilo_bicos.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#f2dede")))
    tabela_bicos.setStyle(TableStyle(estilo_bicos))
    elementos.append(tabela_bicos)
    elementos.append(Spacer(1, 4 * mm))

    # Parâmetros globais
    elementos.append(Paragraph("Parâmetros gerais", subtitulo_style))
    elementos.append(Spacer(1, 1 * mm))
    linhas_globais = []
    par = []
    for campo, rotulo in RES_GLOBAIS_LABELS.items():
        par.append(Paragraph(f"<b>{rotulo}:</b> {_fmt(checklist.get(campo))}", normal))
        if len(par) == 2:
            linhas_globais.append(par)
            par = []
    if par:
        linhas_globais.append(par + [Paragraph("", normal)])
    tabela_globais = Table(linhas_globais, colWidths=[LARGURA_UTIL / 2] * 2)
    tabela_globais.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    elementos.append(tabela_globais)
    elementos.append(Spacer(1, 4 * mm))

    elementos.append(Paragraph("Comentários", subtitulo_style))
    elementos.append(Paragraph(texto_seguro(checklist.get("comentario")) or "—", normal))

    doc.build(elementos)
    buf.seek(0)
    return buf.getvalue()
