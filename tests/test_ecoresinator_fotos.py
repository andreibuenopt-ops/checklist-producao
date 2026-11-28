"""Ecoresinator só com foto: concluir exige 1 foto OU leituras digitadas."""
import pytest


@pytest.fixture
def ui():
    import src.ecoresinator_ui as m
    return m


def _vazio():
    return {"leituras_bicos": [{"numero": 1, "vazao_lmin": None, "eficiencia_pct": None, "abertura_valvula_pct": None}],
            "rodizio_ligado": None, "pressao_bomba_resina": None, "bicos_em_manutencao": ""}


def test_sem_nada_digitado_nao_conta(ui):
    assert ui.tem_leituras_digitadas(_vazio()) is False


def test_zero_padrao_do_number_input_nao_conta(ui):
    c = _vazio(); c["pressao_bomba_resina"] = 0.0
    assert ui.tem_leituras_digitadas(c) is False


def test_bico_preenchido_conta(ui):
    c = _vazio(); c["leituras_bicos"][0]["vazao_lmin"] = 12.5
    assert ui.tem_leituras_digitadas(c) is True


def test_parametro_preenchido_conta(ui):
    c = _vazio(); c["rodizio_ligado"] = "Sim"
    assert ui.tem_leituras_digitadas(c) is True
