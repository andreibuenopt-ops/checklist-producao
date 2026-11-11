from datetime import date

from src.aderencia import calcular_aderencia, por_checklist, por_turno, ranking_esquecimentos, somar
from src.turnos import chave_ordem

D1, D2, D3 = date(2026, 10, 1), date(2026, 10, 2), date(2026, 10, 3)
# "agora" = turno A do dia 3: C do dia 3 já acabou? NÃO — C do dia 3 acabou às 05:20,
# e A do dia 3 é o turno em andamento. Turnos esperados: tudo antes de (D3, A).
LIMITE = chave_ordem(1, D3)

T_SERRAS = {"id": "t1", "area": "Área das Serras", "codigo": "001", "criado_em": "2026-10-01T10:00:00+00:00"}
T_SIFTER = {"id": "t2", "area": "Sifter", "codigo": "011", "criado_em": "2026-10-01T10:00:00+00:00"}


def _ck(tid, turno, data, status="completo", incompleto=False):
    return {"template_id": tid, "turno_id": turno, "data": data.isoformat(), "status": status, "incompleto": incompleto}


def test_esperados_so_contam_turnos_que_ja_terminaram():
    linhas = calcular_aderencia([T_SERRAS], [], D1, D3, LIMITE)
    esperados = {l["turno_id"]: l["esperados"] for l in linhas}
    # C: dias 1,2,3 ; A: dias 1,2 ; B: dias 1,2
    assert esperados == {3: 3, 1: 2, 2: 2}


def test_realizados_incompletos_e_turno_atual_ignorado():
    cks = [
        _ck("t1", 3, D1), _ck("t1", 3, D3), _ck("t1", 1, D1, incompleto=True),
        _ck("t1", 1, D3),                          # turno ATUAL: não conta
        _ck("t1", 2, D1, status="em_andamento"),   # não assinado: não conta
    ]
    linhas = {l["turno_id"]: l for l in calcular_aderencia([T_SERRAS], cks, D1, D3, LIMITE)}
    assert linhas[3]["realizados"] == 2 and linhas[3]["nao_realizados"] == 1
    assert linhas[1]["realizados"] == 1 and linhas[1]["incompletos"] == 1
    assert linhas[2]["realizados"] == 0 and linhas[2]["nao_realizados"] == 2
    assert linhas[2]["aderencia"] == 0


def test_checklist_so_e_esperado_a_partir_da_criacao():
    t_novo = {**T_SIFTER, "criado_em": "2026-10-03T08:00:00+00:00"}
    linhas = calcular_aderencia([t_novo], [], D1, D3, LIMITE)
    assert sum(l["esperados"] for l in linhas) == 1  # só a Noite C do dia 3


def test_resumos_e_ranking_do_que_mais_esquece():
    cks = [_ck("t1", t, d) for d in (D1, D2) for t in (3, 1, 2)]   # Serras: tudo feito
    cks += [_ck("t2", 3, D1)]                                      # Sifter: quase nada
    linhas = calcular_aderencia([T_SERRAS, T_SIFTER], cks, D1, D2, LIMITE)

    por_ck = por_checklist(linhas)
    assert [c["area"] for c in por_ck] == ["Sifter", "Área das Serras"]   # pior primeiro
    assert por_ck[1]["aderencia"] == 1.0

    rank = ranking_esquecimentos(linhas)
    assert rank[0]["area"] == "Sifter" and rank[0]["aderencia"] == 0   # Sifter turnos A/B: 0%
    assert somar(linhas)["esperados"] == 12
    assert [t["turno"] for t in por_turno(linhas)] == ["C Noite", "A Manhã", "B Tarde"]
