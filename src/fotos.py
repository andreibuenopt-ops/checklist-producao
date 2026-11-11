"""Fotos anexadas aos itens do checklist.

O arquivo vai pro bucket privado 'checklist-fotos' do Supabase Storage e
o banco guarda só o caminho (tabela checklist_fotos).

PESO (plano free do Supabase: 1 GB de arquivos, 5 GB de tráfego/mês):
- cada foto é reduzida pra no máx. 1024 px e recomprimida até caber em
  ~110 KB (foto de celular tem 3-8 MB);
- junto vai uma MINIATURA de 240 px (~8 KB), usada nas telas — o arquivo
  grande só é baixado pro PDF. Isso corta o tráfego em ~10x;
- no máximo 3 fotos por item/ronda;
- dá pra apagar fotos antigas em Administração → Armazenamento.
Resultado: ~110 KB x 3 fotos x algumas dezenas por dia ainda cabe em meses.
"""
import io
import uuid
from collections import defaultdict
from datetime import timedelta

import streamlit as st
from PIL import Image, ImageOps

from src.db import supabase
from src.turnos import agora_local

BUCKET = "checklist-fotos"
MAX_LADO = 1024
LIMITE_BYTES = 110_000
QUALIDADES = (62, 54, 46, 38)
MAX_LADO_MINIATURA = 240
QUALIDADE_MINIATURA = 55
MAX_FOTOS_POR_ITEM = 3      # por item, por ronda (somando as já salvas)


def _abrir(conteudo: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(conteudo))
        img = ImageOps.exif_transpose(img)  # corrige rotação do celular
    except Exception as e:  # arquivo corrompido / não é imagem
        raise ValueError("Arquivo não é uma imagem válida.") from e
    if img.mode in ("RGBA", "LA", "P"):
        rgba = img.convert("RGBA")
        fundo = Image.new("RGB", rgba.size, (255, 255, 255))  # senão transparência vira preto
        fundo.paste(rgba, mask=rgba.split()[-1])
        return fundo
    return img.convert("RGB")


def _jpeg(img: Image.Image, qualidade: int) -> bytes:
    saida = io.BytesIO()
    img.save(saida, format="JPEG", quality=qualidade, optimize=True)
    return saida.getvalue()


def comprimir_imagem(conteudo: bytes, limite_bytes: int = LIMITE_BYTES) -> bytes:
    """Reduz pro MAX_LADO e baixa a qualidade (e, se preciso, a resolução)
    até caber em `limite_bytes`. Levanta ValueError se não for imagem."""
    img = _abrir(conteudo)
    img.thumbnail((MAX_LADO, MAX_LADO))
    dados = b""
    for _ in range(4):
        for qualidade in QUALIDADES:
            dados = _jpeg(img, qualidade)
            if len(dados) <= limite_bytes:
                return dados
        img = img.resize((max(int(img.width * 0.8), 64), max(int(img.height * 0.8), 64)))
    return dados


def criar_miniatura(jpeg: bytes) -> bytes:
    img = _abrir(jpeg)
    img.thumbnail((MAX_LADO_MINIATURA, MAX_LADO_MINIATURA))
    return _jpeg(img, QUALIDADE_MINIATURA)


def caminho_miniatura(caminho: str) -> str:
    return caminho[:-4] + "_t.jpg"


def enviar_foto(checklist_id: str, item_id: str, horario_id: str, conteudo: bytes, usuario_id: str) -> dict:
    """Comprime, sobe a foto + miniatura e registra no banco."""
    jpeg = comprimir_imagem(conteudo)
    mini = criar_miniatura(jpeg)
    caminho = f"{checklist_id}/{item_id}_{horario_id}_{uuid.uuid4().hex[:12]}.jpg"
    opcoes = {"content-type": "image/jpeg"}
    bucket = supabase.storage.from_(BUCKET)
    bucket.upload(caminho, jpeg, opcoes)
    try:
        bucket.upload(caminho_miniatura(caminho), mini, opcoes)
        res = supabase.table("checklist_fotos").insert({
            "checklist_id": checklist_id, "item_id": item_id, "horario_id": horario_id,
            "caminho": caminho, "enviado_por": usuario_id,
        }).execute()
    except Exception:
        # não deixa arquivo órfão ocupando espaço
        try:
            bucket.remove([caminho, caminho_miniatura(caminho)])
        except Exception:
            pass
        raise
    return res.data[0]


def listar_fotos(checklist_id: str) -> list[dict]:
    res = (
        supabase.table("checklist_fotos")
        .select("id, item_id, horario_id, caminho, enviado_em")
        .eq("checklist_id", checklist_id)
        .order("enviado_em")
        .execute()
    )
    return res.data


def agrupar_por_item(fotos: list[dict]) -> dict:
    """{(item_id, horario_id): [fotos...]}"""
    grupos = defaultdict(list)
    for f in fotos:
        grupos[(f["item_id"], f["horario_id"])].append(f)
    return grupos


@st.cache_data(show_spinner=False, max_entries=300)
def baixar_miniatura(caminho: str) -> bytes:
    """Miniatura (~8 KB) — é o que as telas mostram."""
    return supabase.storage.from_(BUCKET).download(caminho_miniatura(caminho))


@st.cache_data(show_spinner=False, max_entries=30)
def baixar_foto(caminho: str) -> bytes:
    """Foto inteira — só pra PDF (cache pequeno de propósito: memória)."""
    return supabase.storage.from_(BUCKET).download(caminho)


def carregar_bytes(fotos: list[dict]) -> list[dict]:
    """Mesmas fotos com a chave 'bytes' (foto inteira), pro PDF. Foto que
    não baixar é pulada — PDF não deve quebrar por causa disso."""
    saida = []
    for f in fotos:
        try:
            saida.append({**f, "bytes": baixar_foto(f["caminho"])})
        except Exception:
            continue
    return saida


# ---------------------------------------------------------------------
# Limpeza e uso de espaço
# ---------------------------------------------------------------------
def remover_fotos(fotos: list[dict]) -> int:
    """Apaga do Storage (foto + miniatura) e do banco. `fotos` = linhas
    com 'id' e 'caminho'."""
    if not fotos:
        return 0
    caminhos = []
    for f in fotos:
        caminhos += [f["caminho"], caminho_miniatura(f["caminho"])]
    for i in range(0, len(caminhos), 100):
        supabase.storage.from_(BUCKET).remove(caminhos[i:i + 100])
    ids = [f["id"] for f in fotos]
    for i in range(0, len(ids), 100):
        supabase.table("checklist_fotos").delete().in_("id", ids[i:i + 100]).execute()
    return len(fotos)


def remover_fotos_antigas(dias: int) -> int:
    """Apaga fotos enviadas há mais de `dias` dias. Devolve quantas."""
    corte = (agora_local() - timedelta(days=dias)).isoformat()
    total = 0
    while True:
        lote = supabase.table("checklist_fotos").select("id, caminho").lt("enviado_em", corte).limit(200).execute().data
        if not lote:
            return total
        total += remover_fotos(lote)


def remover_fotos_de_itens(checklist_id: str, horario_id: str, item_ids: list[str]) -> int:
    """Apaga as fotos de certos itens numa ronda (ex.: perguntas de uma
    parada que foi desmarcada)."""
    if not item_ids:
        return 0
    lote = (
        supabase.table("checklist_fotos").select("id, caminho")
        .eq("checklist_id", checklist_id).eq("horario_id", horario_id).in_("item_id", item_ids)
        .execute().data
    )
    return remover_fotos(lote)


def uso_armazenamento() -> dict:
    """Banco (MB) e fotos (MB), lidos de funções do banco. None = não deu
    pra ler (função ainda não criada, por exemplo)."""
    uso = {"banco_mb": None, "fotos_mb": None, "fotos_qtd": None}
    for chave, funcao in (("banco_mb", "tamanho_banco_mb"), ("fotos_mb", "tamanho_fotos_mb")):
        try:
            uso[chave] = float(supabase.rpc(funcao).execute().data)
        except Exception:
            pass
    try:
        uso["fotos_qtd"] = supabase.table("checklist_fotos").select("id", count="exact").limit(1).execute().count
    except Exception:
        pass
    return uso
