"""Testes de login e autocadastro (verificação de senha via RPC mockada).

Cobre: senha correta/incorreta, papel forçado como 'producao' no
autocadastro, toggle de aprovação, validações de formulário.
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent / "fixture_apps" / "cadastro_app.py")


def _preencher_cadastro(tab, nome, email, matricula, senha, confirmar=None):
    inputs = tab.text_input
    inputs[0].set_value(nome)
    inputs[1].set_value(email)
    inputs[2].set_value(matricula)
    inputs[3].set_value(senha)
    inputs[4].set_value(confirmar if confirmar is not None else senha)


def test_cadastro_entra_como_producao_e_loga_automaticamente(monkeypatch):
    monkeypatch.delenv("TESTE_REQUER_APROVACAO", raising=False)
    at = AppTest.from_file(APP)
    at.run()

    tab_cadastro = at.tabs[1]
    _preencher_cadastro(tab_cadastro, "Ana Costa", "ana@guararapes.com.br", "55501", "minhasenha")
    [b for b in tab_cadastro.button if "Criar minha conta" in b.label][0].click()
    at.run()

    assert not at.exception
    assert any("LOGADO: Ana Costa producao" in el.value for el in at.markdown)


def test_cadastro_com_aprovacao_fica_pendente_sem_logar(monkeypatch):
    monkeypatch.setenv("TESTE_REQUER_APROVACAO", "1")
    at = AppTest.from_file(APP)
    at.run()

    tab_cadastro = at.tabs[1]
    _preencher_cadastro(tab_cadastro, "Bruno Alves", "bruno@guararapes.com.br", "55502", "minhasenha")
    [b for b in tab_cadastro.button if "Criar minha conta" in b.label][0].click()
    at.run()

    assert not at.exception
    assert not any("LOGADO" in el.value for el in at.markdown)
    assert any("pendente" in el.value for el in at.success)


def test_cadastro_bloqueia_senha_curta(monkeypatch):
    monkeypatch.delenv("TESTE_REQUER_APROVACAO", raising=False)
    at = AppTest.from_file(APP)
    at.run()

    tab_cadastro = at.tabs[1]
    _preencher_cadastro(tab_cadastro, "Carlos", "carlos@guararapes.com.br", "55504", "123")
    [b for b in tab_cadastro.button if "Criar minha conta" in b.label][0].click()
    at.run()

    assert any("mínimo 6 caracteres" in el.value for el in at.error)


def test_cadastro_bloqueia_senhas_diferentes(monkeypatch):
    monkeypatch.delenv("TESTE_REQUER_APROVACAO", raising=False)
    at = AppTest.from_file(APP)
    at.run()

    tab_cadastro = at.tabs[1]
    _preencher_cadastro(
        tab_cadastro, "Diana", "diana@guararapes.com.br", "55505",
        "senha123", confirmar="outraSenha",
    )
    [b for b in tab_cadastro.button if "Criar minha conta" in b.label][0].click()
    at.run()

    assert any("não conferem" in el.value for el in at.error)


def test_login_com_senha_correta(monkeypatch):
    monkeypatch.delenv("TESTE_REQUER_APROVACAO", raising=False)
    at = AppTest.from_file(APP)
    at.run()

    tab_entrar = at.tabs[0]
    inputs = tab_entrar.text_input
    inputs[0].set_value("semente@guararapes.com.br")
    inputs[1].set_value("senhaSemente1")
    [b for b in tab_entrar.button if "Entrar" in b.label][0].click()
    at.run()

    assert not at.exception
    assert any("LOGADO: Usuário Semente" in el.value for el in at.markdown)


def test_login_com_senha_errada_nao_entra(monkeypatch):
    monkeypatch.delenv("TESTE_REQUER_APROVACAO", raising=False)
    at = AppTest.from_file(APP)
    at.run()

    tab_entrar = at.tabs[0]
    inputs = tab_entrar.text_input
    inputs[0].set_value("semente@guararapes.com.br")
    inputs[1].set_value("senhaERRADA")
    [b for b in tab_entrar.button if "Entrar" in b.label][0].click()
    at.run()

    assert not any("LOGADO" in el.value for el in at.markdown)
    assert any("Senha incorreta" in el.value for el in at.error)
