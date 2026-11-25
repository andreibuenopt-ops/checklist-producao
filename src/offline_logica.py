"""Modo offline — lógica PURA (sem Streamlit/banco), para poder testar à parte.

Fluxo: com internet, o app monta um PACOTE (checklists, perguntas, rondas e as
janelas de turno das próximas ~36 h) e o celular guarda. Sem internet, a tela
estática (static/offline.html) preenche usando só o pacote e grava no aparelho.
Quando volta o sinal, cada ronda/foto é enviada e validada aqui.
"""
import re
from datetime import date, datetime, timedelta, timezone

from src.itens import itens_da_ronda
from src.turnos import LETRA_TURNO, NOME_TURNO, _TZ, horario_programado

VERSAO_PACOTE = 1
RESPOSTAS_VALIDAS = {"Sim", "Não", "N/A"}
MAX_OBS = 2000
MAX_FOTO_BYTES = 2_000_000
_ID_CLIENTE = re.compile(r"^[a-f0-9-]{8,40}$")


# ---------------------------------------------------------------------
# Janelas de turno (A 05:20–13:40 · B 13:40–22:00 · C 22:00–05:20)
# ---------------------------------------------------------------------
def janelas(agora: datetime, antes_h: int = 14, depois_h: int = 36) -> list[dict]:
    """Janelas de turno que tocam [agora-antes_h, agora+depois_h], em ordem."""
    base = agora.date() - timedelta(days=2)

    def dt(d: date, h: int, m: int):
        x = datetime(d.year, d.month, d.day, h, m)
        return x.replace(tzinfo=agora.tzinfo or _TZ)

    todas = []
    for k in range(6):
        d = base + timedelta(days=k)
        todas += [
            (1, d, dt(d, 5, 20), dt(d, 13, 40)),
            (2, d, dt(d, 13, 40), dt(d, 22, 0)),
            (3, d + timedelta(days=1), dt(d, 22, 0), dt(d + timedelta(days=1), 5, 20)),  # Noite pertence ao dia SEGUINTE
        ]
    ini_j, fim_j = agora - timedelta(hours=antes_h), agora + timedelta(hours=depois_h)
    return [
        {"turno_id": t, "nome": NOME_TURNO[t], "letra": LETRA_TURNO[t], "ref": ref.isoformat(),
         "ini": ini.isoformat(), "fim": fim.isoformat()}
        for t, ref, ini, fim in todas if fim > ini_j and ini < fim_j
    ]


def montar_pacote(usuario: dict, templates: list, itens_por_template: dict, horarios_por_template: dict,
                  agora: datetime) -> dict:
    """`horarios_por_template` = {template_id: {turno_id: [{"id","horario"}]}}."""
    jans = janelas(agora)
    checklists = []
    for t in templates:
        itens = itens_por_template.get(t["id"]) or []
        horarios = horarios_por_template.get(t["id"]) or {}
        if not itens:
            continue
        rondas = {}
        for i, j in enumerate(jans):
            lista = []
            for h in horarios.get(j["turno_id"]) or []:
                prog = horario_programado(date.fromisoformat(j["ref"]), h["horario"], j["nome"])
                lista.append({"id": h["id"], "h": str(h["horario"])[:5], "p": prog.isoformat()})
            if lista:
                rondas[str(i)] = lista
        if not rondas:
            continue
        checklists.append({
            "id": t["id"], "codigo": t.get("codigo", ""), "titulo": t.get("titulo", ""), "area": t.get("area", ""),
            "setor": (t.get("setores_processo") or {}).get("nome", "Outros"),
            "tipo_area": t.get("tipo_area", "interno"),
            "itens": [{
                "id": i["id"], "pergunta": i["pergunta"], "crit": i.get("criticidade", "media"),
                "tipo": "texto_livre" if i.get("tipo_resposta") == "texto_livre" else "sim_nao",
                "foto": bool(i.get("exige_foto")), "pai": i.get("pai_item_id"),
            } for i in itens],
            "rondas": rondas,
        })
    return {
        "v": VERSAO_PACOTE, "gerado": agora.isoformat(),
        "usuario": {"id": usuario["id"], "nome": usuario["nome"]},
        "janelas": jans, "checklists": checklists,
        "margem_atraso_min": 60,
    }


# ---------------------------------------------------------------------
# Validação do que o celular mandou (nunca confiar no cliente)
# ---------------------------------------------------------------------
def _iso_de_ms(ms, agora: datetime) -> str:
    try:
        dt = datetime.fromtimestamp(float(ms) / 1000, tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return agora.astimezone(timezone.utc).isoformat()
    teto = agora.astimezone(timezone.utc)
    return min(dt, teto).isoformat()


def validar_registro(registro: dict, itens: list, horarios_ids: set, agora: datetime):
    """→ (respostas_ok, justificativas_ok, avisos).

    respostas_ok = [{"item_id","horario_id","resposta","observacao","respondido_em"}]
    Descarta: item/horário que não pertencem ao checklist, resposta inválida e
    sub-perguntas cujo pai não está "Sim" na mesma ronda."""
    por_id = {i["id"]: i for i in itens}
    brutas = registro.get("respostas") or {}
    avisos, ok = [], {}

    def resposta_de(horario_id):
        return lambda item_id: ((brutas.get(f"{item_id}|{horario_id}") or {}).get("r"))

    for horario_id in sorted(horarios_ids):
        for item, _ in itens_da_ronda(itens, {}, horario_id, resposta_de=resposta_de(horario_id)):
            bruta = brutas.get(f"{item['id']}|{horario_id}")
            if not bruta:
                continue
            r, obs = bruta.get("r"), str(bruta.get("o") or "").strip()[:MAX_OBS]
            if item.get("tipo_resposta") == "texto_livre":
                if not obs:
                    continue
                r = "Texto"
            elif r not in RESPOSTAS_VALIDAS:
                continue
            elif r != "Não":
                obs = ""
            ok[(item["id"], horario_id)] = {
                "item_id": item["id"], "horario_id": horario_id, "resposta": r, "observacao": obs,
                "respondido_em": _iso_de_ms(bruta.get("t"), agora),
            }
    descartadas = [k for k in brutas if k.split("|")[0] in por_id and tuple(k.split("|")) not in ok]
    if descartadas:
        avisos.append(f"{len(descartadas)} resposta(s) ignorada(s) (sub-pergunta fechada, vazia ou inválida).")

    just = {}
    for horario_id, texto in (registro.get("justificativas") or {}).items():
        texto = str(texto or "").strip()[:MAX_OBS]
        if horario_id in horarios_ids and texto:
            just[horario_id] = texto
    return list(ok.values()), just, avisos


def sem_conflito(respostas: list, existentes: dict) -> tuple[list, int]:
    """Descarta a resposta offline se já existe uma MAIS NOVA no banco
    (alguém respondeu online depois). `existentes` = {(item_id, horario_id): respondido_em ISO}."""
    mantidas, puladas = [], 0
    for r in respostas:
        atual = existentes.get((r["item_id"], r["horario_id"]))
        if atual and _parse(atual) > _parse(r["respondido_em"]):
            puladas += 1
        else:
            mantidas.append(r)
    return mantidas, puladas


def _parse(valor: str) -> datetime:
    dt = datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def id_cliente_valido(valor) -> str | None:
    valor = str(valor or "").lower()
    return valor if _ID_CLIENTE.match(valor) else None
