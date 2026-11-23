from datetime import date

from src.equipes_logica import (
    checklist_e_da_equipe, filtrar_checklists, indice_membros, membros_do_dia, pertence, resumo_membros,
)

# Zezinho: equipe do Eduardo até 14/11, depois foi transferido (esta é a equipe do Eduardo)
MEMB = [
    {"usuario_id": "edu", "inicio": "2026-01-01", "fim": None},
    {"usuario_id": "zeze", "inicio": "2026-01-01", "fim": "2026-11-14"},
    {"usuario_id": "ana", "inicio": "2026-11-10", "fim": None},
]
IDX = indice_membros(MEMB)


def test_pertence_respeita_datas_da_transferencia():
    assert pertence(IDX, "zeze", "2026-11-14") and not pertence(IDX, "zeze", "2026-11-15")
    assert not pertence(IDX, "ana", "2026-11-09") and pertence(IDX, "ana", "2026-11-10")
    assert not pertence(IDX, "ninguem", "2026-11-12") and not pertence(IDX, None, "2026-11-12")
    assert set(membros_do_dia(IDX, date(2026, 11, 20))) == {"edu", "ana"}


def test_checklist_da_equipe_preencheu_ou_assinou_na_data():
    antes = {"data": "2026-11-12", "colaborador_id": "zeze", "supervisor_id": "outro"}
    depois = {"data": "2026-11-16", "colaborador_id": "zeze", "supervisor_id": "outro"}
    assinado_pelo_lider = {"data": "2026-11-16", "colaborador_id": "x", "supervisor_id": "edu"}
    assert checklist_e_da_equipe(antes, IDX)            # ainda era da equipe
    assert not checklist_e_da_equipe(depois, IDX)       # já transferido
    assert checklist_e_da_equipe(assinado_pelo_lider, IDX)
    assert filtrar_checklists([antes, depois, assinado_pelo_lider], IDX) == [antes, assinado_pelo_lider]


def test_resumo_membros_dias_sem_preenchimento():
    cks = [
        {"data": "2026-11-16", "colaborador_id": "ana", "supervisor_id": "edu"},
        {"data": "2026-11-17", "colaborador_id": "ana", "supervisor_id": None},
        {"data": "2026-11-17", "colaborador_id": "fora", "supervisor_id": "fora2"},
    ]
    r = {l["usuario_id"]: l for l in resumo_membros(IDX, cks, date(2026, 11, 16), date(2026, 11, 18), hoje=date(2026, 11, 17))}
    assert set(r) == {"edu", "ana"}                      # zeze já saiu; "fora" nunca foi da equipe
    assert r["ana"]["preencheu"] == 2 and r["ana"]["dias_sem"] == 0
    assert r["edu"]["assinou"] == 1 and r["edu"]["dias_sem"] == 1      # 17/11 sem nada (18/11 ainda não chegou)
