"""PARADA DE LINHA — 3 tipos de checklist (programada, saída de finos,
corretiva). Cada parada é um EVENTO: abre um checklist novo (pode haver
várias no mesmo turno), com foto por pergunta.

Fica fora do motor de checklists por ronda (checklist_templates/horarios)
porque não tem horário fixo nem entra na conta de "esperados" da aderência.
As perguntas de cada tipo são cadastradas em Administração > Paradas.
"""
from datetime import date

from src.db import supabase

TIPOS = {
    "programada": "Parada programada",
    "saida_finos": "Parada para limpeza de saída de finos",
    "corretiva": "Parada corretiva",
}
TIPOS_CURTOS = {"programada": "Programada", "saida_finos": "Saída de finos", "corretiva": "Corretiva"}


# ---------------------------------------------------------------------
# Perguntas de cada tipo
# ---------------------------------------------------------------------
def listar_itens_parada(tipo: str, apenas_ativos: bool = True) -> list:
    q = supabase.table("paradas_itens").select("*").eq("tipo", tipo)
    if apenas_ativos:
        q = q.eq("ativo", True)
    return q.order("ordem").execute().data


def adicionar_itens_parada(tipo: str, perguntas: list[str], exige_foto: bool = True):
    atuais = listar_itens_parada(tipo, apenas_ativos=False)
    proxima = max((i["ordem"] for i in atuais), default=0)
    payload = [
        {"tipo": tipo, "ordem": proxima + n, "pergunta": p, "exige_foto": exige_foto}
        for n, p in enumerate((p.strip() for p in perguntas if p.strip()), start=1)
    ]
    if payload:
        supabase.table("paradas_itens").insert(payload).execute()


def editar_item_parada(item_id: str, pergunta: str, exige_foto: bool):
    supabase.table("paradas_itens").update({"pergunta": pergunta.strip(), "exige_foto": exige_foto}).eq("id", item_id).execute()


def desativar_item_parada(item_id: str):
    """Não apaga: paradas já feitas continuam referenciando a pergunta."""
    supabase.table("paradas_itens").update({"ativo": False}).eq("id", item_id).execute()


# ---------------------------------------------------------------------
# Paradas (ocorrências)
# ---------------------------------------------------------------------
SELECT_PARADA = "*, turnos(nome)"


def criar_parada(tipo: str, turno_id: int, data_ref: date, colaborador_id: str, descricao: str = "") -> dict:
    res = supabase.table("paradas").insert({
        "tipo": tipo, "turno_id": turno_id, "data": data_ref.isoformat(),
        "colaborador_id": colaborador_id, "descricao": descricao,
    }).execute()
    return res.data[0]


def buscar_parada(parada_id: str) -> dict | None:
    res = supabase.table("paradas").select(SELECT_PARADA).eq("id", parada_id).limit(1).execute()
    return res.data[0] if res.data else None


def listar_paradas_do_turno(turno_id: int, data_ref: date) -> list:
    return (
        supabase.table("paradas").select(SELECT_PARADA)
        .eq("turno_id", turno_id).eq("data", data_ref.isoformat())
        .order("iniciada_em").execute().data
    )


def listar_paradas_periodo(inicio: date, fim: date, tipo: str | None = None, apenas_concluidas: bool = False) -> list:
    q = (
        supabase.table("paradas").select(SELECT_PARADA)
        .gte("data", inicio.isoformat()).lte("data", fim.isoformat())
    )
    if tipo:
        q = q.eq("tipo", tipo)
    if apenas_concluidas:
        q = q.eq("status", "completo")
    return q.order("data", desc=True).order("iniciada_em", desc=True).execute().data


def atualizar_descricao_parada(parada_id: str, descricao: str):
    supabase.table("paradas").update({"descricao": descricao}).eq("id", parada_id).execute()


def concluir_parada(parada_id: str, usuario_id: str, comentario: str):
    supabase.table("paradas").update({
        "supervisor_id": usuario_id, "comentario": comentario,
        "status": "completo", "concluido_em": "now()",
    }).eq("id", parada_id).execute()


# ---------------------------------------------------------------------
# Respostas
# ---------------------------------------------------------------------
def listar_respostas_parada(parada_id: str) -> dict:
    """{item_id: {"resposta": ..., "observacao": ...}}"""
    res = supabase.table("paradas_respostas").select("item_id, resposta, observacao").eq("parada_id", parada_id).execute()
    return {r["item_id"]: {"resposta": r["resposta"], "observacao": r.get("observacao") or ""} for r in res.data}


def salvar_respostas_parada(respostas: list[dict]) -> int:
    """Lote único (upsert) — mesmo princípio do checklist por ronda."""
    if not respostas:
        return 0
    payload = [{**r, "respondido_em": "now()"} for r in respostas]
    supabase.table("paradas_respostas").upsert(payload, on_conflict="parada_id,item_id").execute()
    return len(payload)


# ---------------------------------------------------------------------
# Regras (funções puras)
# ---------------------------------------------------------------------
def itens_visiveis(itens: list, respostas: dict, concluida: bool) -> list:
    """Parada em andamento: só as perguntas ativas. Concluída: também as
    desativadas depois, se já tinham resposta (o histórico não perde nada)."""
    if concluida:
        return [i for i in itens if i.get("ativo", True) or i["id"] in respostas]
    return [i for i in itens if i.get("ativo", True)]


def faltando_respostas(itens: list, respostas: dict) -> int:
    return sum(1 for i in itens if not (respostas.get(i["id"]) or {}).get("resposta"))


def faltando_fotos(itens: list, respostas: dict, fotos_por_pergunta: dict, recem_enviadas=frozenset()) -> int:
    """Perguntas que exigem foto, já respondidas, ainda sem nenhuma foto."""
    return sum(
        1 for i in itens
        if i.get("exige_foto") and (respostas.get(i["id"]) or {}).get("resposta")
        and not fotos_por_pergunta.get(i["id"]) and i["id"] not in recem_enviadas
    )


def fotos_por_pergunta(fotos: list) -> dict:
    grupos = {}
    for f in fotos:
        grupos.setdefault(f["item_id"], []).append(f)
    return grupos


def obter_parada_completa(parada_id: str, com_bytes: bool = True) -> dict | None:
    """Pacote pra PDF/histórico: parada + perguntas + respostas + fotos + nomes."""
    from src.fotos import carregar_bytes
    from src.models import dados_usuarios

    parada = buscar_parada(parada_id)
    if not parada:
        return None
    respostas = listar_respostas_parada(parada_id)
    itens = itens_visiveis(listar_itens_parada(parada["tipo"], apenas_ativos=False), respostas, parada["status"] == "completo")
    from src.fotos import listar_fotos_parada
    fotos = listar_fotos_parada(parada_id)
    pessoas = dados_usuarios((parada.get("colaborador_id"), parada.get("supervisor_id")))
    col = pessoas.get(parada.get("colaborador_id")) or {}
    sup = pessoas.get(parada.get("supervisor_id")) or {}
    return {
        "parada": parada,
        "tipo_nome": TIPOS.get(parada["tipo"], parada["tipo"]),
        "turno_nome": (parada.get("turnos") or {}).get("nome", "-"),
        "itens": itens, "respostas": respostas,
        "fotos": carregar_bytes(fotos) if com_bytes else fotos,
        "colaborador_nome": col.get("nome", "-"), "colaborador_turma": col.get("turma"),
        "supervisor_nome": sup.get("nome", "-"), "supervisor_turma": sup.get("turma"),
    }
