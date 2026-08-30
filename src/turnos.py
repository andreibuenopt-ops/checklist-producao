"""Detecção do turno atual e data de referência.

Regras: Manhã 07h-15h, Tarde 15h-23h, Noite 23h-07h. O turno Noite
"pertence" à data em que começou (ex.: 02h de 10/03 pertence ao turno
Noite iniciado em 09/03).
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("America/Sao_Paulo")
except Exception:
    _TZ = None

_MANHA_INICIO = time(7, 0)
_TARDE_INICIO = time(15, 0)
_NOITE_INICIO = time(23, 0)


def agora_local() -> datetime:
    return datetime.now(_TZ) if _TZ else datetime.now()


@dataclass
class Turno:
    turno_id: int
    nome: str
    data_referencia: date


def turno_e_data_referencia() -> Turno:
    agora = agora_local()
    hora = agora.time()
    hoje = agora.date()

    if _MANHA_INICIO <= hora < _TARDE_INICIO:
        return Turno(1, "Manhã", hoje)
    if _TARDE_INICIO <= hora < _NOITE_INICIO:
        return Turno(2, "Tarde", hoje)
    if hora >= _NOITE_INICIO:
        return Turno(3, "Noite", hoje)
    return Turno(3, "Noite", hoje - timedelta(days=1))
