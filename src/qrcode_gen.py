"""Geração de QR Code (PNG) e cartaz para impressão (PDF A5)."""
import io
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

# Fonte embutida no projeto — carregar "DejaVuSans-Bold.ttf" pelo nome
# solto depende do servidor já ter ela instalada no sistema (não tinha
# no Streamlit Cloud: caía no load_default(), uma fonte bitmap que
# desenha acento errado — "inspeções" saía com traço sobreposto/feio).
_FONTE_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "DejaVuSans-Bold.ttf"


def _carregar_fonte(tamanho: int) -> ImageFont.FreeTypeFont:
    if _FONTE_PATH.exists():
        return ImageFont.truetype(str(_FONTE_PATH), tamanho)
    return ImageFont.load_default()


def url_do_checklist(base_url: str, slug: str) -> str:
    base_url = (base_url or "").rstrip("/")
    return f"{base_url}/?area={slug}"


def url_do_ecoresinator(base_url: str) -> str:
    base_url = (base_url or "").rstrip("/")
    return f"{base_url}/?form=ecoresinator"


def validar_url_base(base_url: str) -> tuple[bool, str]:
    """Detecta os erros de URL mais comuns antes de gerar um QR Code — evita
    imprimir e colar na parede um QR que abre a URL errada.
    Retorna (valida, mensagem_de_erro)."""
    url = (base_url or "").strip()

    if not url:
        return False, "URL vazia. Cole a URL pública do app (ex: https://seu-app.streamlit.app)."

    if "share.streamlit.io" in url:
        return False, (
            "Essa é a URL de **gerenciamento** do Streamlit Cloud (só abre pra "
            "quem tem login lá) — não é a URL pública do app que o operador "
            "deve escanear. Use o formato `https://seu-app.streamlit.app`. "
            "Confira em Settings → General do seu app no Streamlit Cloud."
        )

    if "localhost" in url or "127.0.0.1" in url:
        return False, "Essa é uma URL local — só funciona no seu computador. Use a URL pública, depois do deploy."

    if not (url.startswith("http://") or url.startswith("https://")):
        return False, "A URL precisa começar com `https://`."

    return True, ""


def _gerar_qr_img(url: str, tamanho_caixa: int = 10) -> Image.Image:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=tamanho_caixa, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def _quebrar_linhas(draw: ImageDraw.ImageDraw, texto: str, fonte, largura_max: int) -> list[str]:
    """Quebra o texto em várias linhas pra caber em largura_max, sem cortar palavra no meio."""
    palavras = texto.split()
    linhas, linha_atual = [], ""
    for palavra in palavras:
        tentativa = f"{linha_atual} {palavra}".strip()
        if draw.textlength(tentativa, font=fonte) <= largura_max:
            linha_atual = tentativa
        else:
            if linha_atual:
                linhas.append(linha_atual)
            linha_atual = palavra
    if linha_atual:
        linhas.append(linha_atual)
    return linhas or [""]


def gerar_etiqueta_png(titulo: str, area: str, codigo: str, url: str, logo_bytes: bytes | None = None) -> bytes:
    qr_img = _gerar_qr_img(url, tamanho_caixa=8)
    largura = qr_img.width

    fonte = _carregar_fonte(14)

    # Prepara a faixa da logo antes de saber o tamanho final do canvas
    faixa_logo, altura_logo = None, 50
    if logo_bytes:
        try:
            logo_img = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
            logo_img.thumbnail((largura - 10, altura_logo - 6))
            faixa_logo = Image.new("RGB", (largura, altura_logo), "white")
            x_logo = (largura - logo_img.width) // 2
            y_logo = (altura_logo - logo_img.height) // 2
            faixa_logo.paste(logo_img, (x_logo, y_logo), logo_img)
        except Exception:
            faixa_logo = None
    if faixa_logo is None:
        altura_logo = 0

    # Quebra de linha (em vez do corte fixo em N caracteres, que cortava palavra no meio)
    medidor = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    largura_texto_max = largura - 10
    linhas = _quebrar_linhas(medidor, "Checklist", fonte, largura_texto_max)
    linhas += _quebrar_linhas(medidor, f"{area} · {codigo}", fonte, largura_texto_max)
    altura_linha = 20
    altura_texto = 10 + altura_linha * len(linhas)

    canvas_img = Image.new("RGB", (largura, altura_logo + qr_img.height + altura_texto), "white")
    if faixa_logo is not None:
        canvas_img.paste(faixa_logo, (0, 0))
    canvas_img.paste(qr_img, (0, altura_logo))

    draw = ImageDraw.Draw(canvas_img)
    y = altura_logo + qr_img.height + 5
    for linha in linhas:
        draw.text((5, y), linha, fill="black", font=fonte)
        y += altura_linha

    buf = io.BytesIO()
    canvas_img.save(buf, format="PNG")
    return buf.getvalue()


def _tamanho_fonte_que_cabe(texto: str, fonte_nome: str, tamanho_base: float, largura_max: float) -> float:
    """Reduz o tamanho da fonte até o texto caber em largura_max (nunca abaixo de 7pt)."""
    tamanho = tamanho_base
    while tamanho > 7 and stringWidth(texto, fonte_nome, tamanho) > largura_max:
        tamanho -= 0.5
    return tamanho


def gerar_cartaz_pdf(titulo: str, area: str, codigo: str, url: str, logo_bytes: bytes | None = None) -> bytes:
    buf = io.BytesIO()
    largura, altura = A5
    c = canvas.Canvas(buf, pagesize=A5)
    largura_disponivel = largura - 16 * mm  # margem de 8mm de cada lado

    y_titulo = altura - 25 * mm
    if logo_bytes:
        try:
            logo_reader = ImageReader(io.BytesIO(logo_bytes))
            logo_w, logo_h = logo_reader.getSize()
            largura_logo = 35 * mm
            altura_logo = largura_logo * logo_h / logo_w
            x_logo = (largura - largura_logo) / 2
            y_logo = altura - 10 * mm - altura_logo
            c.drawImage(logo_reader, x_logo, y_logo, width=largura_logo, height=altura_logo, mask="auto")
            y_titulo = y_logo - 8 * mm
        except Exception:
            pass

    tam_titulo = _tamanho_fonte_que_cabe(titulo, "Helvetica-Bold", 13, largura_disponivel)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(largura / 2, y_titulo, "CHECKLIST DE INSPEÇÃO")

    c.setFont("Helvetica-Bold", tam_titulo)
    c.drawCentredString(largura / 2, y_titulo - 10 * mm, titulo)

    texto_area = f"{area} · {codigo}"
    tam_area = _tamanho_fonte_que_cabe(texto_area, "Helvetica", 11, largura_disponivel)
    c.setFont("Helvetica", tam_area)
    c.drawCentredString(largura / 2, y_titulo - 17 * mm, texto_area)

    qr_img = _gerar_qr_img(url, tamanho_caixa=10)
    qr_buf = io.BytesIO()
    qr_img.save(qr_buf, format="PNG")
    qr_buf.seek(0)
    qr_reader = ImageReader(qr_buf)

    tamanho_qr = 70 * mm
    x = (largura - tamanho_qr) / 2
    y = altura / 2 - tamanho_qr / 2 - 8 * mm
    c.drawImage(qr_reader, x, y, width=tamanho_qr, height=tamanho_qr)

    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(largura / 2, 15 * mm, "Escaneie para abrir o checklist do turno atual")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()
