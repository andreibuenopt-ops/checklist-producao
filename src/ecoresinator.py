"""Formulário dedicado do Ecoresinator (cozinha de cola).

Diferente dos demais checklists: não é Sim/Não por pergunta, é uma
leitura técnica (vazão, eficiência, pressão) por bico injetor, feita
uma vez por turno "logo na primeira hora" — sem horário fixo, o
operador registra a hora real que fez a rotina. Por isso vive fora do
motor genérico de checklist_templates/itens/horarios/respostas.
"""
from datetime import date

from src.db import supabase

NUMERO_BICOS = 14

CAMPOS_GLOBAIS_SIMNAO = (
    "rodizio_ligado", "flush_ligado", "valvula_proporcional_auto",
    "agulhas_force_abertura", "bomba_resina_manutencao",
)
CAMPOS_GLOBAIS_NUMERICOS = (
    "pressao_bomba_resina", "pressao_coletor_resina", "pressao_bomba_agua",
    "pressao_coletor_agua", "pressao_vapor_coletor", "vazao_resina_bomba",
)
CAMPOS_GLOBAIS_TEXTO = (
    "bicos_em_manutencao", "bicos_em_producao", "bomba_resina_em_uso", "bomba_parafina_em_uso",
)


def _leituras_vazias() -> list[dict]:
    return [
        {
            "numero": n, "vazao_lmin": None, "eficiencia_pct": None, "abertura_valvula_pct": None,
            "falha_3_vias": "Não", "falha_agulha": "Não", "falha_vazao": "Não",
        }
        for n in range(1, NUMERO_BICOS + 1)
    ]


def obter_ou_criar_ecoresinator(turno_id: int, data_referencia: date) -> dict:
    res = (
        supabase.table("ecoresinator_checklists")
        .select("*")
        .eq("turno_id", turno_id)
        .eq("data", data_referencia.isoformat())
        .limit(1)
        .execute()
    )
    if res.data:
        return res.data[0]
    novo = supabase.table("ecoresinator_checklists").insert({
        "turno_id": turno_id,
        "data": data_referencia.isoformat(),
        "leituras_bicos": _leituras_vazias(),
    }).execute()
    return novo.data[0]


def buscar_ecoresinator(checklist_id: str) -> dict | None:
    res = supabase.table("ecoresinator_checklists").select("*").eq("id", checklist_id).limit(1).execute()
    return res.data[0] if res.data else None


def definir_colaborador_ecoresinator(checklist_id: str, usuario_id: str):
    atual = buscar_ecoresinator(checklist_id)
    if atual and atual.get("colaborador_id"):
        return
    supabase.table("ecoresinator_checklists").update({"colaborador_id": usuario_id}).eq("id", checklist_id).execute()


def salvar_ecoresinator(checklist_id: str, campos: dict):
    """Grava os campos globais + leituras_bicos numa única chamada
    (mesmo princípio de lote usado no checklist genérico)."""
    supabase.table("ecoresinator_checklists").update(campos).eq("id", checklist_id).execute()


def concluir_ecoresinator(checklist_id: str, assinante_id: str, comentario: str):
    supabase.table("ecoresinator_checklists").update({
        "supervisor_id": assinante_id,
        "comentario": comentario,
        "status": "completo",
        "concluido_em": "now()",
    }).eq("id", checklist_id).execute()


def ecoresinator_do_dia(data_ref: date):
    res = (
        supabase.table("ecoresinator_checklists")
        .select("*, turnos(nome)")
        .eq("data", data_ref.isoformat())
        .execute()
    )
    return res.data
