"""Acesso a dados (Supabase): templates, checklists, respostas, dashboard,
usuários e sugestões de itens.
"""
import re
import unicodedata
from datetime import date

from src.db import supabase


# =====================================================================
# Helpers
# =====================================================================
def _slugify(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^\w\s-]", "", texto).strip().lower()
    return re.sub(r"[\s_]+", "-", texto)


# =====================================================================
# Setores / Turnos
# =====================================================================
def listar_setores():
    return supabase.table("setores_processo").select("*").order("ordem").execute().data


def listar_turnos():
    return supabase.table("turnos").select("*").order("ordem").execute().data


# =====================================================================
# Equipamentos — catálogo de área/equipamento específico por setor,
# mantido pelo master (Administração → Áreas/Equipamentos). Usado como
# campo "área" na criação de um checklist.
# =====================================================================
def listar_equipamentos(setor_id: int | None = None, apenas_ativos: bool = True):
    q = supabase.table("equipamentos").select("*")
    if setor_id is not None:
        q = q.eq("setor_id", setor_id)
    if apenas_ativos:
        q = q.eq("ativo", True)
    return q.order("ordem").execute().data


def criar_equipamento(setor_id: int, nome: str):
    return supabase.table("equipamentos").insert({
        "setor_id": setor_id, "nome": nome.strip(),
    }).execute()


def remover_equipamento(equipamento_id: str):
    supabase.table("equipamentos").delete().eq("id", equipamento_id).execute()


def alternar_equipamento(equipamento_id: str, ativo: bool):
    supabase.table("equipamentos").update({"ativo": ativo}).eq("id", equipamento_id).execute()


# =====================================================================
# Templates (checklists) — CRUD completo, usado pelo master na Administração
# =====================================================================
def listar_templates(apenas_ativos: bool = True):
    q = supabase.table("checklist_templates").select("*, setores_processo(nome, ordem), equipamentos(nome)")
    if apenas_ativos:
        q = q.eq("ativo", True)
    return q.order("ordem_processo").execute().data


def buscar_template_por_slug(slug: str):
    res = (
        supabase.table("checklist_templates")
        .select("*, setores_processo(nome, ordem), equipamentos(nome)")
        .eq("slug", slug)
        .eq("ativo", True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def criar_template(
    codigo: str, titulo: str, setor_id: int, revisao: str = "", observacao: str = "",
    equipamento_id: str | None = None,
):
    setor = next(s for s in listar_setores() if s["id"] == setor_id)
    area = setor["nome"]
    if equipamento_id:
        equipamento = next(e for e in listar_equipamentos(setor_id, apenas_ativos=False) if e["id"] == equipamento_id)
        area = equipamento["nome"]

    res = supabase.table("checklist_templates").insert({
        "codigo": codigo,
        "titulo": titulo,
        "area": area,
        "slug": _slugify(titulo),
        "setor_id": setor_id,
        "equipamento_id": equipamento_id,
        "ordem_processo": setor["ordem"] * 10,
        "revisao": revisao,
        "observacao": observacao,
    }).execute()
    return res.data[0]


def desativar_template(template_id: str):
    supabase.table("checklist_templates").update({"ativo": False}).eq("id", template_id).execute()


def reativar_template(template_id: str):
    supabase.table("checklist_templates").update({"ativo": True}).eq("id", template_id).execute()


# =====================================================================
# Itens de inspeção
# =====================================================================
def listar_itens(template_id: str):
    return (
        supabase.table("checklist_template_itens")
        .select("*")
        .eq("template_id", template_id)
        .order("ordem")
        .execute()
        .data
    )


def adicionar_itens(template_id: str, perguntas: list[str], criticidade: str = "media"):
    itens_atuais = listar_itens(template_id)
    proxima_ordem = max((i["ordem"] for i in itens_atuais), default=0)
    payload = [
        {"template_id": template_id, "ordem": proxima_ordem + i, "pergunta": p, "criticidade": criticidade}
        for i, p in enumerate((p.strip() for p in perguntas if p.strip()), start=1)
    ]
    if payload:
        supabase.table("checklist_template_itens").insert(payload).execute()


def remover_item(item_id: str):
    supabase.table("checklist_template_itens").delete().eq("id", item_id).execute()


# =====================================================================
# Horários de verificação por turno — definidos pelo master, um por turno
# =====================================================================
def listar_horarios(template_id: str, turno_id: int):
    return (
        supabase.table("checklist_template_horarios")
        .select("*")
        .eq("template_id", template_id)
        .eq("turno_id", turno_id)
        .order("ordem")
        .execute()
        .data
    )


def listar_horarios_todos_turnos(template_id: str):
    return (
        supabase.table("checklist_template_horarios")
        .select("*, turnos(nome, ordem)")
        .eq("template_id", template_id)
        .order("turno_id")
        .execute()
        .data
    )


def definir_horarios_turnos(template_id: str, horarios_por_turno: dict):
    """horarios_por_turno: {turno_id: 'HH:MM'} — um horário de checagem por turno."""
    payload = [
        {"template_id": template_id, "turno_id": turno_id, "horario": horario, "ordem": 1}
        for turno_id, horario in horarios_por_turno.items() if horario
    ]
    if payload:
        supabase.table("checklist_template_horarios").upsert(
            payload, on_conflict="template_id,turno_id,horario"
        ).execute()


def remover_horario(horario_id: str):
    supabase.table("checklist_template_horarios").delete().eq("id", horario_id).execute()


# =====================================================================
# Checklists (instâncias diárias por turno)
# =====================================================================
def obter_ou_criar_checklist(template_id: str, turno_id: int, data_referencia: date):
    existente = (
        supabase.table("checklists")
        .select("*")
        .eq("template_id", template_id)
        .eq("turno_id", turno_id)
        .eq("data", data_referencia.isoformat())
        .limit(1)
        .execute()
    )
    if existente.data:
        return existente.data[0]

    novo = supabase.table("checklists").insert({
        "template_id": template_id,
        "turno_id": turno_id,
        "data": data_referencia.isoformat(),
    }).execute()
    return novo.data[0]


def buscar_checklist(checklist_id: str):
    res = supabase.table("checklists").select("*").eq("id", checklist_id).limit(1).execute()
    return res.data[0] if res.data else None


def definir_colaborador(checklist_id: str, usuario_id: str):
    checklist = buscar_checklist(checklist_id)
    if checklist and checklist.get("colaborador_id"):
        return
    supabase.table("checklists").update({
        "colaborador_id": usuario_id,
        "status": "em_andamento",
    }).eq("id", checklist_id).execute()


def concluir_checklist(checklist_id: str, supervisor_id: str, comentario: str):
    supabase.table("checklists").update({
        "supervisor_id": supervisor_id,
        "comentario": comentario,
        "status": "completo",
        "concluido_em": "now()",
    }).eq("id", checklist_id).execute()


# =====================================================================
# Respostas
# =====================================================================
def listar_respostas(checklist_id: str) -> dict:
    res = (
        supabase.table("checklist_respostas")
        .select("item_id, horario_id, resposta")
        .eq("checklist_id", checklist_id)
        .execute()
    )
    return {(r["item_id"], r["horario_id"]): r["resposta"] for r in res.data}


def salvar_resposta(checklist_id: str, item_id: str, horario_id: str, resposta: str, usuario_id: str):
    supabase.table("checklist_respostas").upsert({
        "checklist_id": checklist_id,
        "item_id": item_id,
        "horario_id": horario_id,
        "resposta": resposta,
        "respondido_por": usuario_id,
        "respondido_em": "now()",
    }, on_conflict="checklist_id,item_id,horario_id").execute()


# =====================================================================
# Dashboard
# =====================================================================
def checklists_do_dia(data_ref: date):
    res = (
        supabase.table("checklists")
        .select("*, checklist_templates(titulo, area, codigo), turnos(nome)")
        .eq("data", data_ref.isoformat())
        .execute()
    )
    return res.data


def respostas_por_data(data_ref: date):
    res = (
        supabase.table("checklist_respostas")
        .select(
            "*, checklist_template_itens(pergunta, criticidade), "
            "checklists!inner(id, data, checklist_templates(titulo, area))"
        )
        .eq("checklists.data", data_ref.isoformat())
        .execute()
    )
    return res.data


# =====================================================================
# Usuários
# =====================================================================
def listar_usuarios():
    return (
        supabase.table("usuarios")
        .select("id,nome,email,matricula,papel,ativo,senha_temporaria")
        .order("nome")
        .execute()
        .data
    )


def nomes_usuarios(ids: tuple):
    ids_validos = [i for i in ids if i]
    if not ids_validos:
        return {}
    res = supabase.table("usuarios").select("id, nome").in_("id", ids_validos).execute()
    return {u["id"]: u["nome"] for u in res.data}


# =====================================================================
# Sugestões de novos itens — qualquer usuário sugere, master aprova/rejeita
# =====================================================================
def criar_sugestao(template_id: str, usuario_id: str, pergunta: str, justificativa: str, criticidade: str):
    return supabase.table("checklist_sugestoes").insert({
        "template_id": template_id,
        "sugerido_por": usuario_id,
        "pergunta_sugerida": pergunta.strip(),
        "justificativa": justificativa.strip(),
        "criticidade_sugerida": criticidade,
    }).execute()


def listar_sugestoes(status: str | None = None):
    q = (
        supabase.table("checklist_sugestoes")
        .select("*, checklist_templates(titulo, area), usuarios!checklist_sugestoes_sugerido_por_fkey(nome)")
        .order("criado_em", desc=True)
    )
    if status:
        q = q.eq("status", status)
    return q.execute().data


def aprovar_sugestao(sugestao_id: str, template_id: str, master_id: str, pergunta: str, criticidade: str):
    itens_atuais = listar_itens(template_id)
    proxima_ordem = max((i["ordem"] for i in itens_atuais), default=0) + 1
    novo_item = supabase.table("checklist_template_itens").insert({
        "template_id": template_id,
        "ordem": proxima_ordem,
        "pergunta": pergunta,
        "criticidade": criticidade,
    }).execute().data[0]

    supabase.table("checklist_sugestoes").update({
        "status": "aprovada",
        "analisado_por": master_id,
        "analisado_em": "now()",
        "item_id": novo_item["id"],
    }).eq("id", sugestao_id).execute()
    return novo_item


def rejeitar_sugestao(sugestao_id: str, master_id: str, motivo: str):
    supabase.table("checklist_sugestoes").update({
        "status": "rejeitada",
        "analisado_por": master_id,
        "analisado_em": "now()",
        "motivo_rejeicao": motivo.strip(),
    }).eq("id", sugestao_id).execute()


# =====================================================================
# Análise 5 Porquês (RCA) — ESTRUTURA PROVISÓRIA, aguardando spec final
# =====================================================================
def respostas_nao_criticas_sem_analise(dias: int = 30):
    """Respostas 'Não' em itens críticos, nos últimos N dias, sem RCA aberta ainda."""
    from datetime import date, timedelta
    desde = (date.today() - timedelta(days=dias)).isoformat()

    respostas = (
        supabase.table("checklist_respostas")
        .select(
            "id, resposta, respondido_em, "
            "checklist_template_itens!inner(pergunta, criticidade), "
            "checklists!inner(id, data, template_id, checklist_templates(titulo, area))"
        )
        .eq("resposta", "Não")
        .eq("checklist_template_itens.criticidade", "critica")
        .gte("checklists.data", desde)
        .execute()
    )
    ja_analisadas = {
        a["checklist_resposta_id"]
        for a in supabase.table("analises_5_porques").select("checklist_resposta_id").execute().data
        if a["checklist_resposta_id"]
    }
    return [r for r in respostas.data if r["id"] not in ja_analisadas]


def criar_analise_5_porques(checklist_resposta_id: str, template_id: str, problema: str, criado_por_id: str):
    return supabase.table("analises_5_porques").insert({
        "checklist_resposta_id": checklist_resposta_id,
        "template_id": template_id,
        "problema": problema.strip(),
        "criado_por": criado_por_id,
    }).execute().data[0]


def listar_analises_5_porques(status: str | None = None):
    q = (
        supabase.table("analises_5_porques")
        .select("*, checklist_templates(titulo, area)")
        .order("criado_em", desc=True)
    )
    if status:
        q = q.eq("status", status)
    return q.execute().data


def atualizar_analise_5_porques(analise_id: str, campos: dict):
    supabase.table("analises_5_porques").update(campos).eq("id", analise_id).execute()
