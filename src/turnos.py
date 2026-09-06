"""Detecção do turno atual e data de referência.

Regras (horário oficial da fábrica): Manhã 05h-14h, Tarde 14h-22h,
Noite 22h-05h. O turno Noite "pertence" à data em que começou (ex.: 02h
de 10/03 pertence ao turno Noite iniciado em 09/03).
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("America/Sao_Paulo")
except Exception:
    _TZ = None

_MANHA_INICIO = time(5, 0)
_TARDE_INICIO = time(14, 0)
_NOITE_INICIO = time(22, 0)


def agora_local() -> datetime:
    return datetime.now(_TZ) if _TZ else datetime.now()


def formatar_datahora_local(valor) -> str:
    """Converte um timestamp vindo do Supabase (armazenado em UTC) para
    horário de Brasília e formata como 'AAAA-MM-DD HH:MM'.

    Usar SEMPRE que exibir concluido_em/criado_em/respondido_em etc. —
    o valor cru do banco vem em UTC e não deve ser mostrado direto,
    senão o horário aparece ~3h adiantado (bug já visto em produção).
    """
    if not valor:
        return "-"
    texto = str(valor)
    try:
        # Supabase retorna ISO 8601, às vezes com 'Z', às vezes com offset.
        dt = datetime.fromisoformat(texto.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if _TZ:
            dt = dt.astimezone(_TZ)
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return texto[:16].replace("T", " ")


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


MARGEM_ATRASO_MINUTOS = 60


def horario_programado(data_referencia: date, horario_str: str, turno_nome: str) -> datetime:
    """Combina a data de referência do turno com o horário (hora) de uma
    ronda específica do template, devolvendo o datetime completo (com
    timezone) em que aquela ronda deveria ter sido feita.

    O turno Noite cruza a virada do dia (ex.: começa 22h de um dia, tem
    rondas de madrugada no dia seguinte) — igual à regra de
    data_referencia acima: horários de madrugada (antes do meio-dia)
    dentro do turno Noite pertencem ao dia SEGUINTE à data_referencia.
    """
    hora = horario_str if isinstance(horario_str, time) else time.fromisoformat(str(horario_str)[:8])
    dia = data_referencia
    if turno_nome == "Noite" and hora < time(12, 0):
        dia = data_referencia + timedelta(days=1)
    dt = datetime.combine(dia, hora)
    return dt.replace(tzinfo=_TZ) if _TZ else dt


def esta_atrasado(data_referencia: date, horario_str: str, turno_nome: str, referencia_agora: datetime | None = None) -> bool:
    """True se já passou mais de MARGEM_ATRASO_MINUTOS do horário programado
    daquela ronda, em relação a agora (ou a um instante de referência)."""
    programado = horario_programado(data_referencia, horario_str, turno_nome)
    agora = referencia_agora or agora_local()
    return agora > programado + timedelta(minutes=MARGEM_ATRASO_MINUTOS)
