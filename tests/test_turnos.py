"""Turnos oficiais: A 05:20–13:40, B 13:40–22:00, C 22:00–05:20.
O dia de produção começa pelo C (sequência C, A, B)."""
from datetime import date, datetime, time

import pytest

import src.turnos as t


def _fixa(monkeypatch, ano, mes, dia, h, m):
    dt = datetime(ano, mes, dia, h, m, tzinfo=t._TZ)
    monkeypatch.setattr(t, "agora_local", lambda: dt)


@pytest.mark.parametrize("h,m,turno,data", [
    (5, 19, "Noite", date(2026, 10, 12)),    # ainda é a Noite que termina 05:20
    (5, 20, "Manhã", date(2026, 10, 12)),
    (13, 39, "Manhã", date(2026, 10, 12)),
    (13, 40, "Tarde", date(2026, 10, 12)),
    (21, 59, "Tarde", date(2026, 10, 12)),
    (22, 0, "Noite", date(2026, 10, 13)),    # Noite das 22h conta no dia SEGUINTE
    (23, 30, "Noite", date(2026, 10, 13)),
    (0, 30, "Noite", date(2026, 10, 12)),    # madrugada: mesma Noite, mesmo dia de produção
])
def test_turno_e_dia_de_producao(monkeypatch, h, m, turno, data):
    # "hoje" calendário = 12/10; para h>=22 o dia de produção é 13/10.
    _fixa(monkeypatch, 2026, 10, 12, h, m)
    r = t.turno_e_data_referencia()
    assert (r.nome, r.data_referencia) == (turno, data)


def test_noite_das_22h_e_madrugada_sao_o_mesmo_dia_de_producao(monkeypatch):
    _fixa(monkeypatch, 2026, 10, 12, 23, 0)     # domingo 23h
    noite_domingo = t.turno_e_data_referencia()
    _fixa(monkeypatch, 2026, 10, 13, 2, 0)      # segunda 02h
    madrugada_segunda = t.turno_e_data_referencia()
    assert noite_domingo == madrugada_segunda


def test_horario_programado_da_noite():
    d = date(2026, 10, 13)  # dia de produção
    # 23:00 é a véspera; 01:30 é no próprio dia de produção
    assert t.horario_programado(d, "23:00:00", "Noite").date() == date(2026, 10, 12)
    assert t.horario_programado(d, "01:30:00", "Noite").date() == date(2026, 10, 13)
    assert t.horario_programado(d, "07:00:00", "Manhã").date() == d


def test_turno_anterior_segue_a_sequencia_c_a_b():
    d = date(2026, 10, 13)
    assert t.turno_anterior(1, d) == (3, d)                       # A <- C (mesmo dia)
    assert t.turno_anterior(2, d) == (1, d)                       # B <- A
    assert t.turno_anterior(3, d) == (2, date(2026, 10, 12))      # C <- B da véspera


def test_chave_ordem_ordena_na_sequencia_c_a_b():
    d = date(2026, 10, 13)
    chaves = sorted([t.chave_ordem(2, d), t.chave_ordem(1, d), t.chave_ordem(3, d)])
    assert chaves == [t.chave_ordem(3, d), t.chave_ordem(1, d), t.chave_ordem(2, d)]
