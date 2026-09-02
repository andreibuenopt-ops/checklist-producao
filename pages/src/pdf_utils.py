"""Utilitário compartilhado pelos geradores de PDF (pdf_checklist.py,
pdf_dashboard.py): remove emoji/símbolos que a fonte padrão do reportlab
(Helvetica/WinAnsi) não sabe desenhar — apareceriam como quadrado preto
sólido em vez do caractere. Mantém letras acentuadas (ã, ç, é etc.), que
essa fonte já suporta bem — não é um problema de português, é só emoji.
"""
import re

_PADRAO_EMOJI = re.compile(
    "["
    "\U0001F300-\U0001FAFF"  # emojis diversos (símbolos, pictogramas, rostos...)
    "\U00002600-\U000027BF"  # símbolos diversos e dingbats (☀✅❌➖✍️ etc.)
    "\U0001F000-\U0001F0FF"
    "\U0001F900-\U0001F9FF"
    "\uFE0F"                  # variation selector (deixa o emoji "colorido")
    "]+",
    flags=re.UNICODE,
)


def texto_seguro(texto) -> str:
    """Remove emoji e comprime espaços duplicados que sobram da remoção."""
    if not texto:
        return texto
    limpo = _PADRAO_EMOJI.sub("", str(texto))
    return re.sub(r"[ \t]+", " ", limpo).strip()
