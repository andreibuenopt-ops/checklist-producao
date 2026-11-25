from datetime import datetime, timedelta, timezone

from src.offline_logica import (
    id_cliente_valido, janelas, montar_pacote, sem_conflito, validar_registro,
)

TZ = timezone(timedelta(hours=-3))
AGORA = datetime(2026, 11, 24, 15, 0, tzinfo=TZ)     # terça 15:00 -> turno B, dia 24

ITENS = [
    {"id": "i1", "pergunta": "Parada?", "tipo_resposta": "sim_nao"},
    {"id": "f1", "pergunta": "Qual?", "tipo_resposta": "sim_nao", "pai_item_id": "i1", "exige_foto": True},
    {"id": "i2", "pergunta": "Vazamento?", "tipo_resposta": "sim_nao"},
    {"id": "t1", "pergunta": "Comentário", "tipo_resposta": "texto_livre"},
]


def test_janelas_cobrem_agora_e_noite_pertence_ao_dia_seguinte():
    js = janelas(AGORA)
    atual = [j for j in js if j["ini"] <= AGORA.isoformat() < j["fim"]]
    assert [(j["letra"], j["ref"]) for j in atual] == [("B", "2026-11-24")]
    noite = [j for j in js if j["letra"] == "C" and j["ini"].startswith("2026-11-24T22:00")]
    assert noite and noite[0]["ref"] == "2026-11-25"       # Noite das 22h é o 1º turno do dia seguinte
    assert js == sorted(js, key=lambda j: j["ini"])


def test_pacote_tem_rondas_por_janela_com_horario_absoluto():
    tpl = [{"id": "t", "codigo": "C1", "titulo": "T", "area": "Serras", "tipo_area": "externo",
            "setores_processo": {"nome": "Acabamento"}}]
    hor = {"t": {1: [{"id": "h1", "horario": "07:30:00"}], 2: [{"id": "h2", "horario": "15:30:00"}],
                 3: [{"id": "h3", "horario": "23:30:00"}, {"id": "h4", "horario": "01:00:00"}]}}
    pac = montar_pacote({"id": "u", "nome": "Ana"}, tpl, {"t": ITENS}, hor, AGORA)
    ck = pac["checklists"][0]
    assert ck["setor"] == "Acabamento" and ck["tipo_area"] == "externo"
    assert {i["id"]: i["pai"] for i in ck["itens"]}["f1"] == "i1"
    por_janela = {pac["janelas"][int(k)]["letra"] + pac["janelas"][int(k)]["ref"]: v for k, v in ck["rondas"].items()}
    noite = por_janela["C2026-11-25"]
    # Noite do dia 25: 23:30 cai na véspera (24), 01:00 cai no dia 25
    assert {r["h"]: r["p"][:16] for r in noite} == {"23:30": "2026-11-24T23:30", "01:00": "2026-11-25T01:00"}


def test_validar_descarta_filha_com_pai_fechado_e_resposta_invalida():
    reg = {"respostas": {
        "i1|h": {"r": "Não", "o": "x", "t": AGORA.timestamp() * 1000},
        "f1|h": {"r": "Sim", "t": 1},                          # pai 'Não' -> filha ignorada
        "i2|h": {"r": "Talvez", "t": 1},                       # inválida
        "t1|h": {"r": "Texto", "o": " tudo certo ", "t": 1},
        "zz|h": {"r": "Sim", "t": 1},                          # item de outro checklist
    }, "justificativas": {"h": " trânsito ", "outro": "x"}}
    ok, just, avisos = validar_registro(reg, ITENS, {"h"}, AGORA)
    assert {(r["item_id"], r["resposta"]) for r in ok} == {("i1", "Não"), ("t1", "Texto")}
    assert [r for r in ok if r["item_id"] == "t1"][0]["observacao"] == "tudo certo"
    assert just == {"h": "trânsito"} and avisos


def test_validar_filha_com_pai_sim_e_observacao_so_para_nao():
    reg = {"respostas": {"i1|h": {"r": "Sim", "o": "lixo", "t": 1}, "f1|h": {"r": "Sim", "t": 1}}}
    ok, _, _ = validar_registro(reg, ITENS, {"h"}, AGORA)
    assert {r["item_id"] for r in ok} == {"i1", "f1"}
    assert all(r["observacao"] == "" for r in ok)


def test_timestamp_do_futuro_e_limitado_a_agora():
    reg = {"respostas": {"i2|h": {"r": "Sim", "t": (AGORA.timestamp() + 86400 * 30) * 1000}}}
    ok, _, _ = validar_registro(reg, ITENS, {"h"}, AGORA)
    assert ok[0]["respondido_em"] <= AGORA.astimezone(timezone.utc).isoformat()


def test_conflito_mantem_a_resposta_mais_nova_do_banco():
    novas = [{"item_id": "a", "horario_id": "h", "respondido_em": "2026-11-24T10:00:00+00:00"},
             {"item_id": "b", "horario_id": "h", "respondido_em": "2026-11-24T10:00:00+00:00"}]
    existentes = {("a", "h"): "2026-11-24T11:00:00+00:00", ("b", "h"): "2026-11-24T09:00:00Z"}
    mantidas, puladas = sem_conflito(novas, existentes)
    assert [m["item_id"] for m in mantidas] == ["b"] and puladas == 1


def test_id_cliente():
    assert id_cliente_valido("ABCDEF12-3456") == "abcdef12-3456"
    assert id_cliente_valido("../etc") is None and id_cliente_valido("") is None
