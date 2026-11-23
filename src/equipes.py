"""Equipes — acesso ao banco. A lógica de pertencimento fica em src/equipes_logica.py."""
from datetime import date, timedelta

from src.db import supabase
from src.equipes_logica import _d, indice_membros  # noqa: F401


# ---------------------------------------------------------------------
# Banco (cada função tolera a migration ainda não rodada)
# ---------------------------------------------------------------------
def listar_equipes(apenas_ativas: bool = True) -> list:
    try:
        q = supabase.table("equipes").select("*").order("nome")
        if apenas_ativas:
            q = q.eq("ativa", True)
        return q.execute().data
    except Exception:
        return []


def criar_equipe(nome: str, lider_id: str | None):
    nova = supabase.table("equipes").insert({"nome": nome.strip(), "lider_id": lider_id}).execute().data[0]
    if lider_id:   # o líder também é da equipe (assina/preenche em nome dela)
        supabase.table("equipe_membros").insert({
            "equipe_id": nova["id"], "usuario_id": lider_id, "inicio": date.today().isoformat(),
        }).execute()
    return nova


def definir_equipe_ativa(equipe_id: str, ativa: bool):
    supabase.table("equipes").update({"ativa": ativa}).eq("id", equipe_id).execute()


def listar_membros(equipe_id: str) -> list:
    try:
        return (
            supabase.table("equipe_membros").select("*").eq("equipe_id", equipe_id)
            .order("inicio", desc=True).execute().data
        )
    except Exception:
        return []


def adicionar_membros(equipe_id: str, usuario_ids: list, inicio: date):
    """Ignora quem já está ativo na equipe (evita vigência duplicada)."""
    ja = {m["usuario_id"] for m in listar_membros(equipe_id) if not m.get("fim")}
    novos = [{"equipe_id": equipe_id, "usuario_id": u, "inicio": inicio.isoformat()} for u in usuario_ids if u not in ja]
    if novos:
        supabase.table("equipe_membros").insert(novos).execute()
    return len(novos)


def encerrar_membro(membro_id: str, fim: date):
    supabase.table("equipe_membros").update({"fim": fim.isoformat()}).eq("id", membro_id).execute()


def transferir(membro_id: str, usuario_id: str, para_equipe_id: str, data_troca: date):
    """Sai da equipe atual no DIA ANTERIOR à troca e entra na nova na data da troca."""
    atual = supabase.table("equipe_membros").select("inicio").eq("id", membro_id).limit(1).execute().data
    fim = data_troca - timedelta(days=1)
    if atual and _d(atual[0]["inicio"]) > fim:
        fim = _d(atual[0]["inicio"])
    encerrar_membro(membro_id, fim)
    adicionar_membros(para_equipe_id, [usuario_id], data_troca)


def indice_da_equipe(equipe_id: str) -> dict:
    return indice_membros(listar_membros(equipe_id))
