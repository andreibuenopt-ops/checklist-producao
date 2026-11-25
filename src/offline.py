"""Modo offline — parte que fala com o banco.

`pacote_do_usuario`: monta o que o celular guarda antes de sair da rede.
`gravar_ronda` / `gravar_foto`: recebem o que foi preenchido sem internet.
Sempre usam o usuário LOGADO (nunca o que o celular diz) e podem ser repetidas
sem duplicar nada (resposta = upsert; foto = id do celular no nome do arquivo).
"""
import base64
from datetime import date

from src.db import supabase
from src.fotos import MAX_FOTOS_POR_ITEM, enviar_foto, listar_fotos
from src.models import (
    buscar_checklist, definir_colaborador, listar_horarios, listar_itens, listar_templates,
    obter_ou_criar_checklist, salvar_justificativa_atraso,
)
from src.offline_logica import (
    MAX_FOTO_BYTES, id_cliente_valido, montar_pacote, sem_conflito, validar_registro,
)
from src.turnos import agora_local


def pacote_do_usuario(usuario, incluir_internos: bool = False) -> dict:
    templates = listar_templates()
    if not incluir_internos:
        templates = [t for t in templates if t.get("tipo_area", "interno") == "externo"]
    itens = {t["id"]: listar_itens(t["id"]) for t in templates}
    horarios = {
        t["id"]: {turno: listar_horarios(t["id"], turno) for turno in (1, 2, 3)} for t in templates
    }
    return montar_pacote({"id": usuario.id, "nome": usuario.nome}, templates, itens, horarios, agora_local())


def _resolver(item: dict, usuario):
    """Valida a chave do registro e devolve (erro, template_id, turno_id, data_ref)."""
    try:
        turno_id = int(item["turno_id"])
        data_ref = date.fromisoformat(str(item["data_ref"])[:10])
        template_id = str(item["template_id"])
    except (KeyError, ValueError, TypeError):
        return "Registro inválido.", None, None, None
    if turno_id not in (1, 2, 3):
        return "Turno inválido.", None, None, None
    if str(item.get("user_id")) != str(usuario.id):
        return "Preenchido por outra pessoa neste aparelho — entre com o login dela para enviar.", None, None, None
    return None, template_id, turno_id, data_ref


def _checklist(template_id, turno_id, data_ref, usuario):
    ids = {t["id"] for t in listar_templates()}
    if template_id not in ids:
        return None, "Checklist não existe mais (ou foi desativado)."
    ck = obter_ou_criar_checklist(template_id, turno_id, data_ref)
    if ck["status"] == "completo":
        return None, "Esse checklist já foi assinado — não dá mais para acrescentar respostas."
    definir_colaborador(ck["id"], usuario.id)
    return ck, None


def gravar_ronda(item: dict, usuario) -> dict:
    """Grava respostas + justificativas de um checklist/turno/dia vindos do celular."""
    erro, template_id, turno_id, data_ref = _resolver(item, usuario)
    if erro:
        return {"estado": "bloqueado", "msg": erro}
    ck, erro = _checklist(template_id, turno_id, data_ref, usuario)
    if erro:
        return {"estado": "bloqueado", "msg": erro}

    itens = listar_itens(template_id)
    horarios_ids = {h["id"] for h in listar_horarios(template_id, turno_id)}
    respostas, justificativas, avisos = validar_registro(item, itens, horarios_ids, agora_local())

    existentes = {
        (r["item_id"], r["horario_id"]): r["respondido_em"]
        for r in supabase.table("checklist_respostas").select("item_id, horario_id, respondido_em")
        .eq("checklist_id", ck["id"]).execute().data
    }
    respostas, puladas = sem_conflito(respostas, existentes)
    if respostas:
        supabase.table("checklist_respostas").upsert(
            [{**r, "checklist_id": ck["id"], "respondido_por": usuario.id} for r in respostas],
            on_conflict="checklist_id,item_id,horario_id",
        ).execute()
    for horario_id, texto in justificativas.items():
        salvar_justificativa_atraso(ck["id"], horario_id, texto, usuario.id)
    if puladas:
        avisos.append(f"{puladas} resposta(s) não gravada(s): já havia uma mais nova no sistema.")
    return {"estado": "ok", "msg": f"{len(respostas)} resposta(s) gravada(s)", "avisos": avisos}


def gravar_foto(item: dict, usuario) -> dict:
    erro, template_id, turno_id, data_ref = _resolver(item, usuario)
    if erro:
        return {"estado": "bloqueado", "msg": erro}
    id_cliente = id_cliente_valido(item.get("id"))
    if not id_cliente:
        return {"estado": "bloqueado", "msg": "Foto com identificação inválida."}
    try:
        conteudo = base64.b64decode(str(item.get("b64") or "").split(",")[-1], validate=True)
    except Exception:
        return {"estado": "bloqueado", "msg": "Foto corrompida."}
    if not conteudo or len(conteudo) > MAX_FOTO_BYTES:
        return {"estado": "bloqueado", "msg": "Foto vazia ou grande demais."}

    ck, erro = _checklist(template_id, turno_id, data_ref, usuario)
    if erro:
        return {"estado": "bloqueado", "msg": erro}
    item_id, horario_id = str(item.get("item_id")), str(item.get("horario_id"))
    if item_id not in {i["id"] for i in listar_itens(template_id)} \
            or horario_id not in {h["id"] for h in listar_horarios(template_id, turno_id)}:
        return {"estado": "bloqueado", "msg": "Foto de uma pergunta que não existe mais."}

    salvas = listar_fotos(ck["id"])
    if any(id_cliente[:12] in f["caminho"] for f in salvas):
        return {"estado": "ok", "msg": "Foto já estava enviada."}
    do_item = [f for f in salvas if f["item_id"] == item_id and f["horario_id"] == horario_id]
    if len(do_item) >= MAX_FOTOS_POR_ITEM:
        return {"estado": "ok", "msg": f"Foto não enviada: limite de {MAX_FOTOS_POR_ITEM} por pergunta."}
    enviar_foto(ck["id"], item_id, horario_id, conteudo, usuario.id, id_cliente=id_cliente)
    return {"estado": "ok", "msg": "Foto enviada."}
