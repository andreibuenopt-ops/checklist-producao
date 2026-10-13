"""Acesso a dados (Supabase): templates, checklists, respostas, dashboard,
usuários e sugestões de itens.
"""
import re
import unicodedata
from datetime import date
from pathlib import Path

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


def editar_setor_nome(setor_id: int, nome: str):
    """Renomeia o setor/processo formal — usado como cabeçalho de
    agrupamento em Gerar QRCodes, Preencher Checklist (seleção manual) e
    Dashboard. Diferente de atualizar_nome_exibicao(): isso muda o nome
    em TODO o sistema, não só a etiqueta de um checklist específico.
    Só faz sentido quando o setor tem pouco (ou nenhum) outro checklist
    dividindo o mesmo agrupamento."""
    supabase.table("setores_processo").update({"nome": nome.strip()}).eq("id", setor_id).execute()


def criar_setor(nome: str) -> dict:
    """Cria um setor/processo novo. id e ordem não são automáticos
    (smallint manual na tabela) — pega o próximo disponível."""
    setores = listar_setores()
    novo_id = max((s["id"] for s in setores), default=0) + 1
    novo_ordem = max((s["ordem"] for s in setores), default=0) + 1
    res = supabase.table("setores_processo").insert({
        "id": novo_id, "nome": nome.strip(), "ordem": novo_ordem,
    }).execute()
    return res.data[0]


def mudar_setor_checklist(template_id: str, setor_id: int):
    supabase.table("checklist_templates").update({"setor_id": setor_id}).eq("id", template_id).execute()


def mover_para_setor_proprio(template_id: str, nome_setor: str) -> dict:
    """Separa esse checklist num setor novo, exclusivo pra ele — sem
    afetar o setor antigo nem os outros checklists que ficaram nele.
    Resolve o caso de checklist "perdido" dentro de um setor genérico
    (ex.: Sifter dentro de Silo de Cavaco)."""
    novo_setor = criar_setor(nome_setor)
    mudar_setor_checklist(template_id, novo_setor["id"])
    return novo_setor


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
    equipamento_id: str | None = None, tipo_area: str = "interno",
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
        "tipo_area": tipo_area,
        "ordem_processo": setor["ordem"] * 10,
        "revisao": revisao,
        "observacao": observacao,
    }).execute()
    return res.data[0]


def desativar_template(template_id: str):
    supabase.table("checklist_templates").update({"ativo": False}).eq("id", template_id).execute()


def reativar_template(template_id: str):
    supabase.table("checklist_templates").update({"ativo": True}).eq("id", template_id).execute()


def atualizar_nome_exibicao(template_id: str, area: str):
    """Nome que aparece no QR (etiqueta/cartaz) e na "Área" do checklist —
    independente do setor formal (setor_id), que continua controlando o
    agrupamento por processo em todo o resto do sistema. Editar aqui NÃO
    reclassifica o checklist, só troca o rótulo mostrado."""
    supabase.table("checklist_templates").update({"area": area.strip()}).eq("id", template_id).execute()


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


def adicionar_itens(template_id: str, perguntas: list[str], criticidade: str = "media", tipo_resposta: str = "sim_nao"):
    itens_atuais = listar_itens(template_id)
    proxima_ordem = max((i["ordem"] for i in itens_atuais), default=0)
    payload = [
        {
            "template_id": template_id, "ordem": proxima_ordem + i, "pergunta": p,
            "criticidade": criticidade, "tipo_resposta": tipo_resposta,
        }
        for i, p in enumerate((p.strip() for p in perguntas if p.strip()), start=1)
    ]
    if payload:
        supabase.table("checklist_template_itens").insert(payload).execute()


def remover_item(item_id: str):
    supabase.table("checklist_template_itens").delete().eq("id", item_id).execute()


def editar_item(item_id: str, pergunta: str, criticidade: str, tipo_resposta: str = "sim_nao"):
    supabase.table("checklist_template_itens").update({
        "pergunta": pergunta.strip(),
        "criticidade": criticidade,
        "tipo_resposta": tipo_resposta,
    }).eq("id", item_id).execute()


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


MAX_HORARIOS_POR_TURNO = 6


def adicionar_horario(template_id: str, turno_id: int, horario: str) -> str | None:
    """Adiciona mais uma ronda (horário) num turno já existente do
    checklist. Devolve uma mensagem de erro (string) se não der — None
    se deu certo. Limite de MAX_HORARIOS_POR_TURNO por turno."""
    existentes = (
        supabase.table("checklist_template_horarios")
        .select("id, ordem")
        .eq("template_id", template_id)
        .eq("turno_id", turno_id)
        .execute()
        .data
    )
    if len(existentes) >= MAX_HORARIOS_POR_TURNO:
        return f"Esse turno já tem o máximo de {MAX_HORARIOS_POR_TURNO} horários."
    proxima_ordem = max((e["ordem"] for e in existentes), default=0) + 1
    try:
        supabase.table("checklist_template_horarios").insert({
            "template_id": template_id, "turno_id": turno_id,
            "horario": horario, "ordem": proxima_ordem,
        }).execute()
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            return "Esse turno já tem uma ronda nesse mesmo horário."
        raise
    return None


def editar_horario(horario_id: str, novo_horario: str):
    supabase.table("checklist_template_horarios").update({
        "horario": novo_horario,
    }).eq("id", horario_id).execute()


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
    """Retorna {(item_id, horario_id): {"resposta": ..., "observacao": ...}}.

    "observacao" é o relato específico daquele item (preenchido quando a
    resposta é "Não") — diferente do campo "comentario" geral do checklist.
    """
    res = (
        supabase.table("checklist_respostas")
        .select("item_id, horario_id, resposta, observacao")
        .eq("checklist_id", checklist_id)
        .execute()
    )
    return {
        (r["item_id"], r["horario_id"]): {
            "resposta": r["resposta"],
            "observacao": r.get("observacao") or "",
        }
        for r in res.data
    }


def salvar_resposta(checklist_id: str, item_id: str, horario_id: str, resposta: str, usuario_id: str, observacao: str = ""):
    supabase.table("checklist_respostas").upsert({
        "checklist_id": checklist_id,
        "item_id": item_id,
        "horario_id": horario_id,
        "resposta": resposta,
        "observacao": observacao or "",
        "respondido_por": usuario_id,
        "respondido_em": "now()",
    }, on_conflict="checklist_id,item_id,horario_id").execute()


def salvar_respostas_em_lote(respostas: list[dict]) -> int:
    """Grava várias respostas numa ÚNICA chamada ao Supabase (1 upsert com
    N linhas), em vez de 1 chamada por clique. Usada pelo botão 'Atualizar'
    do preenchimento — evita travar a tela a cada resposta marcada.

    respostas: lista de dicts com checklist_id, item_id, horario_id,
    resposta, respondido_por. Retorna quantas linhas foram gravadas.
    """
    if not respostas:
        return 0
    payload = [{**r, "respondido_em": "now()"} for r in respostas]
    supabase.table("checklist_respostas").upsert(
        payload, on_conflict="checklist_id,item_id,horario_id"
    ).execute()
    return len(payload)


# =====================================================================
# Justificativa de atraso (ronda concluída com >1h de atraso)
# =====================================================================
def listar_justificativas_atraso(checklist_id: str) -> dict:
    """Retorna {horario_id: justificativa} das rondas atrasadas já
    justificadas nesse checklist."""
    res = (
        supabase.table("checklist_justificativas_atraso")
        .select("horario_id, justificativa")
        .eq("checklist_id", checklist_id)
        .execute()
    )
    return {r["horario_id"]: r["justificativa"] for r in res.data}


def salvar_justificativa_atraso(checklist_id: str, horario_id: str, justificativa: str, usuario_id: str):
    supabase.table("checklist_justificativas_atraso").upsert({
        "checklist_id": checklist_id,
        "horario_id": horario_id,
        "justificativa": justificativa,
        "registrado_por": usuario_id,
        "registrado_em": "now()",
    }, on_conflict="checklist_id,horario_id").execute()


# =====================================================================
# Dashboard
# =====================================================================
def checklists_do_dia(data_ref: date):
    res = (
        supabase.table("checklists")
        .select("*, checklist_templates(titulo, area, codigo, tipo_area), turnos(nome)")
        .eq("data", data_ref.isoformat())
        .execute()
    )
    return res.data


def obter_checklist_completo(checklist_id: str) -> dict | None:
    """Monta o pacote inteiro de um checklist (dados + itens + horários +
    respostas + nomes de quem preencheu/assinou) pronto pra exportação
    em PDF — evita a página de relatório ter que orquestrar 6 chamadas
    separadas."""
    checklist = buscar_checklist(checklist_id)
    if not checklist:
        return None

    res_template = (
        supabase.table("checklist_templates")
        .select("titulo, area, codigo, id")
        .eq("id", checklist["template_id"])
        .limit(1)
        .execute()
    )
    template = res_template.data[0] if res_template.data else {}

    res_turno = supabase.table("turnos").select("nome").eq("id", checklist["turno_id"]).limit(1).execute()
    turno_nome = res_turno.data[0]["nome"] if res_turno.data else "-"

    itens = listar_itens(checklist["template_id"])
    horarios = listar_horarios(checklist["template_id"], checklist["turno_id"])
    respostas = listar_respostas(checklist_id)
    justificativas_atraso = listar_justificativas_atraso(checklist_id)
    nomes = nomes_usuarios((checklist.get("colaborador_id"), checklist.get("supervisor_id")))

    return {
        "checklist": checklist,
        "template": template,
        "turno_nome": turno_nome,
        "itens": itens,
        "horarios": horarios,
        "respostas": respostas,
        "justificativas_atraso": justificativas_atraso,
        "colaborador_nome": nomes.get(checklist.get("colaborador_id"), "-"),
        "supervisor_nome": nomes.get(checklist.get("supervisor_id"), "-"),
    }


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
# Análise 5 Porquês (RCA) — "Formulário 5 Porquês – Parada de Linha"
# =====================================================================
JANELA_MINUTOS_MIN = 30
JANELA_MINUTOS_MAX = 90  # 1h30min — regra impressa no formulário


def respostas_nao_criticas_sem_analise(dias: int = 30):
    """Respostas 'Não' em itens críticos, nos últimos N dias, sem RCA aberta ainda.

    Usada só como atalho opcional (pré-preencher a partir de um checklist);
    o formulário também pode ser aberto avulso, sem essa origem.
    """
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


def criar_analise_5_porques(dados: dict, criado_por_id: str) -> dict:
    """dados: data_parada, equipamento, setor, responsavel_id, tempo_parada_minutos,
    descricao_problema, problema, porque_1..5, causa_raiz, e opcionalmente
    checklist_resposta_id/template_id se originada de um checklist."""
    payload = {**dados, "criado_por": criado_por_id}
    return supabase.table("analises_5_porques").insert(payload).execute().data[0]


def listar_analises_5_porques(status: str | None = None):
    q = (
        supabase.table("analises_5_porques")
        .select("*, responsavel:usuarios!analises_5_porques_responsavel_id_fkey(nome, papel)")
        .order("data_parada", desc=True)
    )
    if status:
        q = q.eq("status", status)
    return q.execute().data


def buscar_analise_5_porques(analise_id: str) -> dict | None:
    res = (
        supabase.table("analises_5_porques")
        .select("*, responsavel:usuarios!analises_5_porques_responsavel_id_fkey(nome, papel)")
        .eq("id", analise_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def atualizar_analise_5_porques(analise_id: str, campos: dict):
    supabase.table("analises_5_porques").update(campos).eq("id", analise_id).execute()


def registrar_verificacao_eficacia(analise_id: str, eficaz: bool, evidencias: str, verificado_por_id: str):
    supabase.table("analises_5_porques").update({
        "eficaz": eficaz,
        "evidencias": evidencias.strip(),
        "verificado_por": verificado_por_id,
        "verificado_em": "now()",
        "status": "concluida" if eficaz else "em_andamento",
    }).eq("id", analise_id).execute()


# ---------------------------------------------------------------------
# Plano de Ação (tabela "Ação Corretiva | Responsável | Prazo", N linhas)
# ---------------------------------------------------------------------
def listar_acoes_5_porques(analise_id: str):
    return (
        supabase.table("analise_5_porques_acoes")
        .select("*")
        .eq("analise_id", analise_id)
        .order("ordem")
        .execute()
        .data
    )


def adicionar_acao_5_porques(analise_id: str, acao_corretiva: str, responsavel: str, prazo: str | None):
    atuais = listar_acoes_5_porques(analise_id)
    proxima_ordem = max((a["ordem"] for a in atuais), default=0) + 1
    return supabase.table("analise_5_porques_acoes").insert({
        "analise_id": analise_id,
        "ordem": proxima_ordem,
        "acao_corretiva": acao_corretiva.strip(),
        "responsavel": (responsavel or "").strip(),
        "prazo": prazo,
    }).execute().data[0]


def alternar_conclusao_acao(acao_id: str, concluida: bool):
    supabase.table("analise_5_porques_acoes").update({"concluida": concluida}).eq("id", acao_id).execute()


def remover_acao_5_porques(acao_id: str):
    supabase.table("analise_5_porques_acoes").delete().eq("id", acao_id).execute()


# =====================================================================
# Configurações do sistema — logo da empresa (Supabase Storage)
# =====================================================================
LOGO_BUCKET = "logos"


def obter_configuracoes():
    res = supabase.table("configuracoes_sistema").select("*").eq("id", 1).limit(1).execute()
    return res.data[0] if res.data else None


def atualizar_logo(conteudo: bytes, nome_arquivo: str) -> str:
    extensao = nome_arquivo.rsplit(".", 1)[-1].lower()
    caminho = f"logo.{extensao}"
    content_type = f"image/{'jpeg' if extensao in ('jpg', 'jpeg') else extensao}"
    opcoes = {"content-type": content_type, "upsert": "true"}

    try:
        supabase.storage.from_(LOGO_BUCKET).upload(caminho, conteudo, opcoes)
    except Exception:
        supabase.storage.from_(LOGO_BUCKET).update(caminho, conteudo, opcoes)

    url_publica = supabase.storage.from_(LOGO_BUCKET).get_public_url(caminho)
    supabase.table("configuracoes_sistema").update({
        "logo_path": caminho,
        "logo_url": url_publica,
    }).eq("id", 1).execute()
    return url_publica


def remover_logo():
    config = obter_configuracoes()
    if config and config.get("logo_path"):
        try:
            supabase.storage.from_(LOGO_BUCKET).remove([config["logo_path"]])
        except Exception:
            pass
    supabase.table("configuracoes_sistema").update({
        "logo_path": None,
        "logo_url": None,
    }).eq("id", 1).execute()


def obter_logo_bytes():
    """Usada na geração do cartaz/etiqueta de QR Code (precisa dos bytes, não só da URL)."""
    config = obter_configuracoes()
    if not config or not config.get("logo_path"):
        return None
    try:
        return supabase.storage.from_(LOGO_BUCKET).download(config["logo_path"])
    except Exception:
        return None


# Logo padrão embutida no projeto (assets/), usada só até o master subir
# uma pela Administração pela primeira vez. Depois disso, a do Storage
# sempre tem prioridade — esse arquivo local nunca é sobrescrito.
LOGO_LOCAL_FALLBACK = Path(__file__).resolve().parent.parent / "assets" / "logo_guararapes.png"


def obter_logo_bytes_com_fallback():
    """Para uso em geração de imagem/PDF (qrcode_gen), que precisa de bytes."""
    conteudo = obter_logo_bytes()
    if conteudo:
        return conteudo
    if LOGO_LOCAL_FALLBACK.exists():
        return LOGO_LOCAL_FALLBACK.read_bytes()
    return None


def obter_logo_url_com_fallback():
    """Para uso em st.image() (aceita tanto URL quanto caminho local)."""
    config = obter_configuracoes()
    if config and config.get("logo_url"):
        return config["logo_url"]
    if LOGO_LOCAL_FALLBACK.exists():
        return str(LOGO_LOCAL_FALLBACK)
    return None


# Verde extraído por pixel da logo Guararapes (folha) — é o padrão de
# fábrica. Editável em Administração → Identidade Visual sem redeploy
# (best-effort via CSS, ver src/tema.py); o método garantido pra qualquer
# widget é editar .streamlit/config.toml e fazer redeploy.
COR_PADRAO_GUARARAPES = "#667f38"


def obter_cor_primaria() -> str:
    config = obter_configuracoes()
    if config and config.get("cor_primaria"):
        return config["cor_primaria"]
    return COR_PADRAO_GUARARAPES


def atualizar_cor_primaria(cor_hex: str):
    supabase.table("configuracoes_sistema").update({"cor_primaria": cor_hex}).eq("id", 1).execute()


def restaurar_cor_padrao():
    atualizar_cor_primaria(COR_PADRAO_GUARARAPES)


def obter_autocadastro_requer_aprovacao() -> bool:
    config = obter_configuracoes()
    return bool(config and config.get("autocadastro_requer_aprovacao"))


def atualizar_autocadastro_requer_aprovacao(valor: bool):
    supabase.table("configuracoes_sistema").update({
        "autocadastro_requer_aprovacao": valor,
    }).eq("id", 1).execute()
