"""Equipes — LÓGICA PURA (sem banco): grupo fechado de um líder (ex.: Equipe do Eduardo), independente de
turno/turma. Cada pessoa tem uma ou mais vigências (entrou em / saiu em), então
uma transferência não reescreve o passado: o checklist feito antes da troca
continua contando pra equipe antiga.

Uma pessoa 'pertence' à equipe num dia D se alguma vigência cobre D. Um
checklist é da equipe se QUEM PREENCHEU ou QUEM ASSINOU pertencia à equipe no
dia de produção do checklist.
"""
from datetime import date, timedelta


# ---------------------------------------------------------------------
# Lógica pura
# ---------------------------------------------------------------------
def _d(v) -> date | None:
    return date.fromisoformat(str(v)[:10]) if v else None


def indice_membros(membros: list) -> dict:
    """{usuario_id: [(inicio, fim|None), ...]} a partir de linhas de equipe_membros."""
    idx: dict = {}
    for m in membros:
        idx.setdefault(m["usuario_id"], []).append((_d(m["inicio"]), _d(m.get("fim"))))
    return idx


def pertence(indice: dict, usuario_id, dia) -> bool:
    if not usuario_id or usuario_id not in indice:
        return False
    dia = _d(dia)
    return any(ini <= dia and (fim is None or dia <= fim) for ini, fim in indice[usuario_id])


def checklist_e_da_equipe(ck: dict, indice: dict) -> bool:
    return pertence(indice, ck.get("colaborador_id"), ck["data"]) or pertence(indice, ck.get("supervisor_id"), ck["data"])


def filtrar_checklists(checklists: list, indice: dict) -> list:
    return [c for c in checklists if checklist_e_da_equipe(c, indice)]


def membros_do_dia(indice: dict, dia) -> list:
    return [u for u in indice if pertence(indice, u, dia)]


def resumo_membros(indice: dict, checklists: list, inicio: date, fim: date, hoje: date | None = None) -> list:
    """Uma linha por pessoa que passou pela equipe no período:
    preencheu / assinou (checklists do período) e dias SEM nenhum preenchimento
    (dias em que era da equipe e não preencheu nem assinou nada — inclui folgas)."""
    limite = min(fim, hoje) if hoje else fim
    por_pessoa: dict = {}
    for c in checklists:
        dia = _d(c["data"])
        if c.get("colaborador_id") in indice:
            por_pessoa.setdefault(c["colaborador_id"], {"preencheu": 0, "assinou": 0, "dias": set()})
            p = por_pessoa[c["colaborador_id"]]
            p["preencheu"] += 1
            p["dias"].add(dia)
        if c.get("supervisor_id") in indice:
            por_pessoa.setdefault(c["supervisor_id"], {"preencheu": 0, "assinou": 0, "dias": set()})
            p = por_pessoa[c["supervisor_id"]]
            p["assinou"] += 1
            p["dias"].add(dia)

    linhas = []
    for uid in indice:
        dias_ativos = []
        dia = inicio
        while dia <= limite:
            if pertence(indice, uid, dia):
                dias_ativos.append(dia)
            dia += timedelta(days=1)
        if not dias_ativos:
            continue   # não era da equipe nesse período
        p = por_pessoa.get(uid, {"preencheu": 0, "assinou": 0, "dias": set()})
        sem = [d for d in dias_ativos if d not in p["dias"]]
        linhas.append({
            "usuario_id": uid, "preencheu": p["preencheu"], "assinou": p["assinou"],
            "dias_ativos": len(dias_ativos), "dias_com_atividade": len(dias_ativos) - len(sem),
            "dias_sem": len(sem), "ultimo_dia_sem": max(sem) if sem else None,
        })
    return sorted(linhas, key=lambda l: (-l["dias_sem"], l["preencheu"] + l["assinou"]))
