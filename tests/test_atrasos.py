from datetime import date, datetime
from zoneinfo import ZoneInfo

from src.atrasos import formatar_atraso, rondas_pendentes

TZ = ZoneInfo("America/Sao_Paulo")
HOJE = date(2026, 11, 16)
T = [{"id": "t1", "titulo": "Prensa", "area": "Prensa"}, {"id": "t2", "titulo": "Lixa", "area": "Lixa"}]
H = [
    {"id": "h1", "template_id": "t1", "horario": "06:00:00"},
    {"id": "h2", "template_id": "t1", "horario": "08:00:00"},
    {"id": "h3", "template_id": "t2", "horario": "06:00:00"},
]


def _agora(h, m=0):
    return datetime(2026, 11, 16, h, m, tzinfo=TZ)


def test_atrasada_e_na_hora():
    r = rondas_pendentes(T, H, [], set(), HOJE, 1, "Manhã", _agora(8, 30))
    por = {(l["titulo"], l["horario"]): l for l in r}
    assert por[("Prensa", "06:00")]["atrasada"] and por[("Lixa", "06:00")]["atrasada"]
    assert not por[("Prensa", "08:00")]["atrasada"]  # dentro da margem de 60 min
    assert r[0]["atraso_min"] >= r[-1]["atraso_min"]


def test_ronda_futura_nao_aparece():
    r = rondas_pendentes(T, H, [], set(), HOJE, 1, "Manhã", _agora(5, 30))
    assert r == []


def test_respondida_e_assinada_somem():
    cks = [{"id": "c1", "template_id": "t1", "turno_id": 1, "status": "em_andamento"},
           {"id": "c2", "template_id": "t2", "turno_id": 1, "status": "completo"}]
    r = rondas_pendentes(T, H, cks, {("c1", "h1")}, HOJE, 1, "Manhã", _agora(9))
    assert [(l["titulo"], l["horario"]) for l in r] == [("Prensa", "08:00")]
    assert r[0]["iniciado"]


def test_formatar():
    assert formatar_atraso(135) == "2h15min" and formatar_atraso(40) == "40min"
