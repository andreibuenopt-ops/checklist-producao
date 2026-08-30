"""Geração de QR Code (PNG) e cartaz para impressão (PDF A5)."""
import io

import qrcode
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def url_do_checklist(base_url: str, slug: str) -> str:
    base_url = (base_url or "").rstrip("/")
    return f"{base_url}/?area={slug}"


def _gerar_qr_img(url: str, tamanho_caixa: int = 10) -> Image.Image:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=tamanho_caixa, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def gerar_etiqueta_png(titulo: str, area: str, codigo: str, url: str) -> bytes:
    qr_img = _gerar_qr_img(url, tamanho_caixa=8)
    largura = qr_img.width
    altura_texto = 70
    canvas_img = Image.new("RGB", (largura, qr_img.height + altura_texto), "white")
    canvas_img.paste(qr_img, (0, 0))

    draw = ImageDraw.Draw(canvas_img)
    try:
        fonte = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
    except Exception:
        fonte = ImageFont.load_default()

    draw.text((5, qr_img.height + 5), titulo[:40], fill="black", font=fonte)
    draw.text((5, qr_img.height + 25), f"{area} · {codigo}"[:50], fill="black", font=fonte)

    buf = io.BytesIO()
    canvas_img.save(buf, format="PNG")
    return buf.getvalue()


def gerar_cartaz_pdf(titulo: str, area: str, codigo: str, url: str) -> bytes:
    buf = io.BytesIO()
    largura, altura = A5
    c = canvas.Canvas(buf, pagesize=A5)

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(largura / 2, altura - 25 * mm, "CHECKLIST DE INSPEÇÃO")

    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(largura / 2, altura - 35 * mm, titulo)

    c.setFont("Helvetica", 11)
    c.drawCentredString(largura / 2, altura - 42 * mm, f"{area} · {codigo}")

    qr_img = _gerar_qr_img(url, tamanho_caixa=10)
    qr_buf = io.BytesIO()
    qr_img.save(qr_buf, format="PNG")
    qr_buf.seek(0)
    qr_reader = ImageReader(qr_buf)

    tamanho_qr = 70 * mm
    x = (largura - tamanho_qr) / 2
    y = altura / 2 - tamanho_qr / 2
    c.drawImage(qr_reader, x, y, width=tamanho_qr, height=tamanho_qr)

    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(largura / 2, 15 * mm, "Escaneie para abrir o checklist do turno atual")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()
