"""Testes de permissão na página de Preencher Checklist: produção sem QR
vê lista somente-leitura, sem nenhum widget clicável pra abrir checklist.
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent / "fixture_apps" / "preencher_manual_app.py")


def test_producao_sem_qr_ve_bloqueio_e_lista_somente_leitura():
    at = AppTest.from_file(APP, default_timeout=20)
    at.run()

    assert not at.exception
    assert any("Escaneie o QR Code" in el.value for el in at.error)
    assert any("Sifter" in el.value for el in at.caption)
    assert any("Silo de Cavaco" in el.value for el in at.caption)


def test_producao_sem_qr_nao_ve_selectbox_nenhum():
    at = AppTest.from_file(APP, default_timeout=20)
    at.run()

    assert not at.exception
    assert len(at.main.selectbox) == 0      # (o sidebar tem o seletor "Minha turma")
