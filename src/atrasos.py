"""Rondas em atraso do turno em andamento — pra quem acompanha cobrar na hora.

Regra (a mesma do preenchimento): a ronda está ATRASADA quando já passou
MARGEM_ATRASO_MINUTOS do horário programado e ainda não tem nenhuma resposta
registrada. Antes disso, se o horário já chegou, fica "na hora" (aguardando).
"""
from datetime import datetime, timedelta

from src.turnos import MARGEM_ATRASO_MINUTOS, horario_programado


def rondas_pendentes(templates: list, horarios: list, checklists: list, feitos: set,
                     data_ref, turno_id: int, turno_nome: str, agora: datetime) -> list:
    """Uma linha por ronda cujo horário já chegou e ainda sem respostas.

    templates: checklists ativos (já filtrados); horarios: linhas de
    checklist_template_horarios do turno; checklists: checklists do dia
    (qualquer status); feitos: {(checklist_id, horario_id)} com resposta.
    Ordem: mais atrasadas primeiro."""
    ck_por_template = {c["template_id"]: c for c in checklists if c["turno_id"] == turno_id}
    linhas = []
    for t in templates:
        ck = ck_por_template.get(t["id"])
        if ck and ck["status"] == "completo":
            continue  # assinado: nada a cobrar
        for h in (x for x in horarios if x["template_id"] == t["id"]):
            programado = horario_programado(data_ref, h["horario"], turno_nome)
            if programado > agora:
                continue  # ainda não chegou a hora
            if ck and (ck["id"], h["id"]) in feitos:
                continue
            atraso_min = int((agora - programado).total_seconds() // 60)
            linhas.append({
                "titulo": t["titulo"], "area": t.get("area", ""), "horario": str(h["horario"])[:5],
                "atraso_min": atraso_min,
                "atrasada": agora > programado + timedelta(minutes=MARGEM_ATRASO_MINUTOS),
                "iniciado": bool(ck), "colaborador_id": ck.get("colaborador_id") if ck else None,
                "data": str(data_ref)[:10],
            })
    return sorted(linhas, key=lambda l: -l["atraso_min"])


def formatar_atraso(minutos: int) -> str:
    h, m = divmod(max(minutos, 0), 60)
    return f"{h}h{m:02d}min" if h else f"{m}min"
