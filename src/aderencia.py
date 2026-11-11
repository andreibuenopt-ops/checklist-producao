"""Índice de aderência: dos checklists que ERAM ESPERADOS no período, quantos
foram realmente concluídos. Alimenta o ranking de "quais o pessoal mais
esquece" e o relatório mensal.

Regras:
- Esperado = cada checklist ativo x cada turno x cada dia de produção do
  período (o Ecoresinator entra como um checklist a mais).
- Só conta turno que JÁ TERMINOU (o turno atual ainda está em andamento).
- Realizado = status "concluído" (assinado). Assinado incompleto conta como
  realizado, mas é contado à parte.
- Um checklist só passa a ser esperado a partir do dia em que foi criado.
"""
from collections import Counter
from datetime import date, timedelta

from src.turnos import LETRA_TURNO, NOME_TURNO, chave_ordem

TURNOS_NA_ORDEM = (3, 1, 2)  # sequência do dia de produção: C, A, B
ID_ECORESINATOR = "ecoresinator"


def _data(valor) -> date:
    return valor if isinstance(valor, date) else date.fromisoformat(str(valor)[:10])


def _dias(inicio: date, fim: date):
    d = inicio
    while d <= fim:
        yield d
        d += timedelta(days=1)


def _taxa(realizados: int, esperados: int):
    return None if esperados == 0 else min(realizados / esperados, 1.0)


def calcular_aderencia(templates: list, checklists: list, inicio: date, fim: date, limite: tuple) -> list:
    """Uma linha por (checklist, turno). `limite` = chave_ordem do turno
    atual: só entram turnos anteriores a ele."""
    realizados, incompletos = Counter(), Counter()
    for c in checklists:
        if c["status"] != "completo":
            continue
        d = _data(c["data"])
        if not (inicio <= d <= fim) or chave_ordem(c["turno_id"], d) >= limite:
            continue
        chave = (c["template_id"], c["turno_id"])
        realizados[chave] += 1
        if c.get("incompleto"):
            incompletos[chave] += 1

    linhas = []
    for t in templates:
        criado = _data(t["criado_em"]) if t.get("criado_em") else inicio
        for turno_id in TURNOS_NA_ORDEM:
            esperados = sum(
                1 for d in _dias(max(inicio, criado), fim)
                if chave_ordem(turno_id, d) < limite
            )
            feitos = realizados[(t["id"], turno_id)]
            linhas.append({
                "template_id": t["id"], "area": t["area"], "titulo": t.get("titulo", t["area"]),
                "codigo": t.get("codigo", ""), "tipo_area": t.get("tipo_area", "interno"),
                "turno_id": turno_id, "turno": f"{LETRA_TURNO[turno_id]} {NOME_TURNO[turno_id]}",
                "esperados": esperados, "realizados": min(feitos, esperados) if esperados else feitos,
                "incompletos": incompletos[(t["id"], turno_id)],
                "nao_realizados": max(esperados - feitos, 0),
                "aderencia": _taxa(feitos, esperados),
            })
    return linhas


def somar(linhas: list) -> dict:
    esperados = sum(l["esperados"] for l in linhas)
    realizados = sum(l["realizados"] for l in linhas)
    return {
        "esperados": esperados, "realizados": realizados,
        "incompletos": sum(l["incompletos"] for l in linhas),
        "nao_realizados": sum(l["nao_realizados"] for l in linhas),
        "aderencia": _taxa(realizados, esperados),
    }


def por_turno(linhas: list) -> list:
    saida = []
    for turno_id in TURNOS_NA_ORDEM:
        sel = [l for l in linhas if l["turno_id"] == turno_id]
        saida.append({"turno": f"{LETRA_TURNO[turno_id]} {NOME_TURNO[turno_id]}", **somar(sel)})
    return saida


def por_checklist(linhas: list) -> list:
    """Um item por checklist, do que MAIS é esquecido pro que menos."""
    grupos = {}
    for l in linhas:
        grupos.setdefault(l["template_id"], []).append(l)
    saida = [
        {"template_id": tid, "area": g[0]["area"], "codigo": g[0]["codigo"], **somar(g)}
        for tid, g in grupos.items()
    ]
    saida = [s for s in saida if s["esperados"] > 0]
    return sorted(saida, key=lambda s: (s["aderencia"], -s["nao_realizados"]))


def ranking_esquecimentos(linhas: list, limite: int | None = None) -> list:
    """Pares (checklist, turno) com pior aderência primeiro."""
    com_esperado = [l for l in linhas if l["esperados"] > 0]
    ordenado = sorted(com_esperado, key=lambda l: (l["aderencia"], -l["nao_realizados"]))
    return ordenado[:limite] if limite else ordenado


def montar_relatorio(inicio: date, fim: date) -> dict:
    """Busca tudo no banco e devolve o relatório pronto (índice + totais)."""
    from src.ecoresinator import ecoresinator_periodo, ecoresinator_primeiro_dia
    from src.models import (
        justificativas_periodo, listar_checklists_periodo, listar_templates, respostas_nao_periodo,
    )
    from src.turnos import turno_e_data_referencia

    atual = turno_e_data_referencia()
    limite = chave_ordem(atual.turno_id, atual.data_referencia)

    templates = listar_templates()  # só os ativos
    checklists = listar_checklists_periodo(inicio, fim)

    eco_inicio = ecoresinator_primeiro_dia()
    if eco_inicio:
        templates = templates + [{
            "id": ID_ECORESINATOR, "area": "Ecoresinator (Cozinha de Cola)",
            "titulo": "Rotina de Inspeção — Ecoresinator", "codigo": "FR-CD-M2-016",
            "tipo_area": "interno", "criado_em": eco_inicio.isoformat(),
        }]
        checklists = checklists + [
            {"template_id": ID_ECORESINATOR, "turno_id": e["turno_id"], "data": e["data"],
             "status": "completo" if e["status"] == "completo" else "em_andamento", "incompleto": False}
            for e in ecoresinator_periodo(inicio, fim)
        ]

    linhas = calcular_aderencia(templates, checklists, inicio, fim, limite)

    nao = respostas_nao_periodo(inicio, fim)
    itens_nao = Counter(
        ((r["checklists"]["checklist_templates"] or {}).get("area", "-"),
         (r["checklist_template_itens"] or {}).get("pergunta", "-"))
        for r in nao
    )
    atrasos = justificativas_periodo(inicio, fim)

    return {
        "inicio": inicio, "fim": fim, "linhas": linhas,
        "geral": somar(linhas), "por_turno": por_turno(linhas),
        "por_checklist": por_checklist(linhas),
        "ranking": ranking_esquecimentos(linhas),
        "total_nao": len(nao), "total_atrasos": len(atrasos),
        "itens_mais_nao": [
            {"area": a, "pergunta": p, "qtd": q} for (a, p), q in itens_nao.most_common(10)
        ],
    }
