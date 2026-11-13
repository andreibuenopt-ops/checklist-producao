"""Parada de linha: regras e a página inteira (com foto obrigatória)."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

PASTA = Path(__file__).resolve().parent / "fixture_apps"
PAGINA = str(PASTA / "parada_app.py")
ADMIN = str(PASTA / "admin_app.py")


@pytest.fixture
def paradas():
    import src.paradas
    return src.paradas


# ----------------------------------------------------------------- regras
ITENS = [
    {"id": "a", "exige_foto": True, "ativo": True},
    {"id": "b", "exige_foto": False, "ativo": True},
    {"id": "c", "exige_foto": True, "ativo": False},   # desativada depois
]


def test_itens_visiveis_em_andamento_so_as_ativas(paradas):
    assert [i["id"] for i in paradas.itens_visiveis(ITENS, {}, concluida=False)] == ["a", "b"]


def test_concluida_mantem_pergunta_desativada_que_ja_tinha_resposta(paradas):
    resp = {"c": {"resposta": "Sim"}}
    assert [i["id"] for i in paradas.itens_visiveis(ITENS, resp, concluida=True)] == ["a", "b", "c"]
    assert [i["id"] for i in paradas.itens_visiveis(ITENS, {}, concluida=True)] == ["a", "b"]


def test_faltando_respostas_e_fotos(paradas):
    ativos = ITENS[:2]
    resp = {"a": {"resposta": "Sim"}}
    assert paradas.faltando_respostas(ativos, resp) == 1                      # b sem resposta
    assert paradas.faltando_fotos(ativos, resp, {}) == 1                      # a respondida e sem foto
    assert paradas.faltando_fotos(ativos, resp, {"a": [{}]}) == 0
    assert paradas.faltando_fotos(ativos, resp, {}, recem_enviadas={"a"}) == 0
    assert paradas.faltando_fotos(ativos, {}, {}) == 0                        # sem resposta, ainda não cobra foto


# ----------------------------------------------------------------- página
def _radio(at, prefixo):
    return [r for r in at.radio if (r.key or "").startswith(prefixo)][0]


def test_sem_parada_mostra_so_o_aviso():
    at = AppTest.from_file(PAGINA, default_timeout=30)
    at.run()
    assert not at.exception
    assert any("Nenhuma parada para registrar" in i.value for i in at.info)
    assert not any("Abrir checklist de parada" in b.label for b in at.button)


def test_fluxo_completo_corretiva_com_foto_obrigatoria():
    at = AppTest.from_file(PAGINA, default_timeout=30)
    at.run()
    _radio(at, "houve_parada").set_value("Sim")
    at.run()
    _radio(at, "tipo_parada").set_value("corretiva")
    at.run()
    [b for b in at.button if "Abrir checklist de parada corretiva" in b.label][0].click()
    at.run()
    assert not at.exception
    assert len(at.segmented_control) == 2                              # as 2 perguntas da corretiva
    assert any("foto é obrigatória" in x.value or "obrigatória" in x.value for x in at.markdown)

    at.segmented_control[0].set_value("Sim")
    at.segmented_control[1].set_value("Sim")
    [b for b in at.button if "Atualizar respostas" in b.label][0].click()
    at.run()
    assert at.session_state["pestado_p1"] == {"faltando": 0, "faltando_fotos": 1}

    [b for b in at.button if "Concluir checklist de parada" in b.label][0].click()
    at.run()
    assert any("fotos obrigatórias" in e.value for e in at.error)
    assert at.session_state["_db_paradas"][0]["status"] == "em_andamento"      # NÃO concluiu

    at.session_state["_db_pfotos"] = [{"id": "f1", "parada_id": "p1", "item_id": "i1", "caminho": "paradas/p1/i1.jpg"}]
    [b for b in at.button if "Atualizar respostas" in b.label][0].click()
    at.run()
    assert at.session_state["pestado_p1"]["faltando_fotos"] == 0
    [b for b in at.button if "Concluir checklist de parada" in b.label][0].click()
    at.run()
    assert not at.exception
    assert at.session_state["_db_paradas"][0]["status"] == "completo"


def test_parada_existente_abre_marcada_como_sim():
    at = AppTest.from_file(PAGINA, default_timeout=30)
    at.session_state["_db_paradas"] = [{
        "id": "p9", "tipo": "corretiva", "turno_id": 1, "data": "2026-08-31", "iniciada_em": "2026-08-31T10:00:00+00:00",
        "status": "em_andamento", "descricao": "", "comentario": "", "colaborador_id": "u1", "turnos": {"nome": "Manhã"}}]
    at.run()
    assert not at.exception
    assert _radio(at, "houve_parada").value == "Sim"                    # já existe parada: abre em "Sim"
    assert any("Paradas deste turno" in s.value for s in at.subheader)


# ----------------------------------------------------------------- admin: perguntas por tipo
def test_admin_cadastra_perguntas_de_um_tipo_de_parada():
    at = AppTest.from_file(ADMIN, default_timeout=30)
    at.run()
    assert not at.exception
    [t for t in at.text_area if t.key == "txt_pi_corretiva"][0].set_value("Piso limpo?\nProteções no lugar?")
    [b for b in at.button if b.label == "Adicionar"][-1].click()         # último form da tela = corretiva
    at.run()
    assert not at.exception
    nome, args = at.session_state["_admin_chamadas"][-1][0], at.session_state["_admin_chamadas"][-1][1]
    assert nome == "adicionar_itens_parada" and args == ("corretiva", ["Piso limpo?", "Proteções no lugar?"], True)
