"""Detecção do turno atual e data de referência.

Regras (horário oficial da fábrica):
  A / Manhã  05:20 – 13:40
  B / Tarde  13:40 – 22:00
  C / Noite  22:00 – 05:20

O DIA DE PRODUÇÃO começa pelo turno C: a sequência do dia é C, A, B. Por
isso a Noite que começa às 22h de domingo pertence a SEGUNDA-FEIRA (é o
primeiro turno de segunda). Ex.: 23h de 09/03 e 02h de 10/03 pertencem,
os dois, ao dia de produção 10/03.
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("America/Sao_Paulo")
except Exception:
    _TZ = None

_MANHA_INICIO = time(5, 20)
_TARDE_INICIO = time(13, 40)
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


# Ordem dos turnos DENTRO do dia de produção: C (Noite), A (Manhã), B (Tarde).
ORDEM_NO_DIA = {3: 0, 1: 1, 2: 2}
NOME_TURNO = {1: "Manhã", 2: "Tarde", 3: "Noite"}
LETRA_TURNO = {1: "A", 2: "B", 3: "C"}


def turno_e_data_referencia() -> Turno:
    agora = agora_local()
    hora = agora.time()
    hoje = agora.date()

    if _MANHA_INICIO <= hora < _TARDE_INICIO:
        return Turno(1, "Manhã", hoje)
    if _TARDE_INICIO <= hora < _NOITE_INICIO:
        return Turno(2, "Tarde", hoje)
    if hora >= _NOITE_INICIO:
        # Noite que começou hoje às 22h: é o 1º turno do dia SEGUINTE.
        return Turno(3, "Noite", hoje + timedelta(days=1))
    # Madrugada (antes das 05:20): continua a Noite que já pertence a hoje.
    return Turno(3, "Noite", hoje)


def turno_proximo(turno_id: int, data_ref: date) -> tuple[int, date]:
    """(turno_id, dia de produção) do turno imediatamente seguinte."""
    if turno_id == 3:      # C -> A (mesmo dia de produção)
        return 1, data_ref
    if turno_id == 1:      # A -> B (mesmo dia)
        return 2, data_ref
    return 3, data_ref + timedelta(days=1)   # B -> C, que pertence ao dia SEGUINTE


def turnos_selecionaveis(atual: "Turno") -> list:
    """Os 3 turnos que a pessoa pode escolher na hora de preencher:
    [anterior, atual, próximo]. Cobre quem chega antes da virada (próximo)
    e quem termina depois dela (anterior) — o sistema só adivinha pelo
    relógio, a pessoa corrige."""
    ant_id, ant_data = turno_anterior(atual.turno_id, atual.data_referencia)
    prox_id, prox_data = turno_proximo(atual.turno_id, atual.data_referencia)
    return [
        Turno(ant_id, NOME_TURNO[ant_id], ant_data),
        atual,
        Turno(prox_id, NOME_TURNO[prox_id], prox_data),
    ]


def chave_ordem(turno_id: int, data_ref: date) -> tuple:
    """Chave pra comparar 'qual turno veio antes' dentro da linha do tempo
    de produção: (dia de produção, posição no dia — C, A, B)."""
    return (data_ref, ORDEM_NO_DIA[turno_id])


def turno_anterior(turno_id: int, data_ref: date) -> tuple[int, date]:
    """(turno_id, data de produção) do turno imediatamente anterior."""
    if turno_id == 1:      # A  <- C do mesmo dia
        return 3, data_ref
    if turno_id == 2:      # B  <- A do mesmo dia
        return 1, data_ref
    return 2, data_ref - timedelta(days=1)   # C  <- B do dia anterior


MARGEM_ATRASO_MINUTOS = 60


def horario_programado(data_referencia: date, horario_str: str, turno_nome: str) -> datetime:
    """Combina o dia de produção do turno com o horário de uma ronda do
    template, devolvendo o datetime completo (com timezone) em que aquela
    ronda deveria ter sido feita.

    A Noite cruza a virada do dia e pertence ao dia de produção em que
    TERMINA: rondas da noite antes do meio-dia (00:00–05:20) caem NO dia
    de produção; rondas a partir do meio-dia (22:00, 23:00) caem na
    véspera.
    """
    hora = horario_str if isinstance(horario_str, time) else time.fromisoformat(str(horario_str)[:8])
    dia = data_referencia
    if turno_nome == "Noite" and hora >= time(12, 0):
        dia = data_referencia - timedelta(days=1)
    dt = datetime.combine(dia, hora)
    return dt.replace(tzinfo=_TZ) if _TZ else dt


def esta_atrasado(data_referencia: date, horario_str: str, turno_nome: str, referencia_agora: datetime | None = None) -> bool:
    """True se já passou mais de MARGEM_ATRASO_MINUTOS do horário programado
    daquela ronda, em relação a agora (ou a um instante de referência)."""
    programado = horario_programado(data_referencia, horario_str, turno_nome)
    agora = referencia_agora or agora_local()
    return agora > programado + timedelta(minutes=MARGEM_ATRASO_MINUTOS)


def ronda_vigente(horarios: list, data_referencia: date, turno_nome: str) -> dict | None:
    """Dentre as rondas (horários) de um turno, devolve a ronda VIGENTE —
    a mais recente cujo horário programado já chegou (<= agora). É só
    ELA que pode pedir justificativa de atraso, não todas as rondas
    passadas de uma vez — evita pedir 3 justificativas diferentes só
    porque o colaborador chegou pra preencher tudo de uma vez, atrasado.
    Devolve None se nenhuma ronda do turno começou ainda."""
    agora = agora_local()
    melhor = None
    melhor_programado = None
    for h in horarios:
        programado = horario_programado(data_referencia, h["horario"], turno_nome)
        if programado <= agora and (melhor_programado is None or programado > melhor_programado):
            melhor, melhor_programado = h, programado
    return melhor
