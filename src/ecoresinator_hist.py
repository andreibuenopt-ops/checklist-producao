"""Histórico do Ecoresinator — lógica pura (sem Streamlit/Supabase):
grade "dia × turno" de preenchimento e contagem de falhas por registro."""
from datetime import date, timedelta

from src.turnos import LETRA_TURNO, NOME_TURNO, ORDEM_NO_DIA

# ordem de leitura dentro do dia de produção: C (noite), A, B
TURNOS_NA_ORDEM = sorted(ORDEM_NO_DIA, key=ORDEM_NO_DIA.get)
DIAS_SEMANA = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]


def rotulo_turno(turno_id: int) -> str:
    return f"{LETRA_TURNO[turno_id]} · {NOME_TURNO[turno_id]}"


def contar_falhas(registro: dict) -> int:
    """Quantas falhas (3 vias / agulha / vazão = 'Sim') há nas leituras dos bicos."""
    return sum(
        1
        for b in (registro.get("leituras_bicos") or [])
        for campo in ("falha_3_vias", "falha_agulha", "falha_vazao")
        if b.get(campo) == "Sim"
    )


def _celula(registro: dict | None, ainda_nao_chegou: bool) -> str:
    if registro is None:
        return "—" if ainda_nao_chegou else "❌ sem registro"
    hora = (registro.get("horario_real") or "").strip()
    if registro.get("status") == "completo":
        texto = f"✅ {hora}".strip()
    else:
        texto = "🟡 em andamento"
    falhas = contar_falhas(registro)
    if falhas:
        texto += f" · ⚠️ {falhas} falha(s)"
    return texto


def montar_grade(registros: list, inicio: date, fim: date, data_ref: date, turno_ref: int) -> list:
    """Uma linha por dia (mais recente primeiro) e uma coluna por turno.
    `data_ref`/`turno_ref` = dia de produção e turno em andamento agora: turnos
    que ainda não começaram aparecem como '—' (não como falta)."""
    por_chave = {(str(r["data"])[:10], r["turno_id"]): r for r in registros}
    linhas = []
    dia = fim
    while dia >= inicio:
        linha = {"Dia": f"{dia.strftime('%d/%m')} ({DIAS_SEMANA[dia.weekday()]})"}
        for tid in TURNOS_NA_ORDEM:
            futuro = dia > data_ref or (dia == data_ref and ORDEM_NO_DIA[tid] > ORDEM_NO_DIA[turno_ref])
            linha[rotulo_turno(tid)] = _celula(por_chave.get((dia.isoformat(), tid)), futuro)
        linhas.append(linha)
        dia -= timedelta(days=1)
    return linhas


def resumo(registros: list, inicio: date, fim: date, data_ref: date, turno_ref: int) -> dict:
    """Totais do período: esperados (turnos que já começaram), concluídos, em andamento, sem registro."""
    esperados = 0
    dia = inicio
    while dia <= min(fim, data_ref):
        esperados += sum(1 for t in TURNOS_NA_ORDEM if not (dia == data_ref and ORDEM_NO_DIA[t] > ORDEM_NO_DIA[turno_ref]))
        dia += timedelta(days=1)
    concl = sum(1 for r in registros if r["status"] == "completo")
    andam = sum(1 for r in registros if r["status"] != "completo")
    return {"esperados": esperados, "concluidos": concl, "andamento": andam,
            "sem_registro": max(esperados - concl - andam, 0)}
