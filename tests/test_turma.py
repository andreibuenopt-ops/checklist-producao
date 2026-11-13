"""Turma fixa do colaborador + escolha do turno na hora de preencher."""
from datetime import date
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

PASTA = Path(__file__).resolve().parent / "fixture_apps"
PREENCHER = str(PASTA / "preenchimento_app.py")
HIST = str(PASTA / "historico_app.py")


# ----------------------------------------------------------------- escolha do turno
def test_padrao_abre_o_turno_atual_e_pode_escolher_o_anterior(monkeypatch):
    monkeypatch.setenv("TESTE_STATUS", "em_andamento")
    at = AppTest.from_file(PREENCHER, default_timeout=20)
    at.run()
    assert not at.exception
    # fixture: turno atual = A (Manhã) de 31/08  ->  opções [C anterior, A atual, B próximo]
    assert [o for o in at.radio[0].options] == ["Anterior: C Noite", "Atual: A Manhã", "Próximo: B Tarde"]
    assert at.session_state["_abertos_debug"][-1] == (1, date(2026, 8, 31))
    assert not any("não é o turno atual" in w.value for w in at.warning)

    at.radio[0].set_value((3, date(2026, 8, 31)))                    # chegou cedo/terminando: escolhe C
    at.run()
    assert not at.exception
    assert at.session_state["_abertos_debug"][-1] == (3, date(2026, 8, 31))
    assert any("C Noite" in w.value and "não é o turno atual" in w.value for w in at.warning)


def test_escolher_o_proximo_turno_usa_o_dia_certo(monkeypatch):
    monkeypatch.setenv("TESTE_STATUS", "em_andamento")
    at = AppTest.from_file(PREENCHER, default_timeout=20)
    at.run()
    at.radio[0].set_value((2, date(2026, 8, 31)))                    # B Tarde, mesmo dia de produção
    at.run()
    assert at.session_state["_abertos_debug"][-1] == (2, date(2026, 8, 31))


# ----------------------------------------------------------------- sidebar: minha turma
def test_sidebar_mostra_e_salva_a_turma_escolhida():
    at = AppTest.from_file(HIST, default_timeout=30)
    at.run()
    caixa = at.sidebar.selectbox[0]
    assert caixa.label == "Minha turma" and caixa.value == ""        # ainda não definida
    caixa.set_value("C")
    at.run()
    assert not at.exception
    assert at.session_state["_turmas_salvas"] == [("u1", "C")]


# ----------------------------------------------------------------- regras no auth
class _Sb:
    def __init__(self):
        self.inseridos, self.atualizados = [], []

    def table(self, nome):
        sb = self

        class _T:
            def insert(self, payload, returning=None): sb.inseridos.append(payload); return self
            def update(self, payload, returning=None): sb.atualizados.append(payload); return self
            def eq(self, *a): return self
            def execute(self): return None
        return _T()


@pytest.fixture
def auth():
    import src.auth
    return src.auth


def test_criar_usuario_so_envia_turma_quando_informada(auth, monkeypatch):
    sb = _Sb()
    monkeypatch.setattr(auth, "supabase", sb)
    auth.criar_usuario("A", "a@x.com", "1", "senha123", "producao", None)
    auth.criar_usuario("B", "b@x.com", "2", "senha123", "producao", None, turma="C")
    assert "turma" not in sb.inseridos[0]          # não quebra banco que ainda não tem a coluna
    assert sb.inseridos[1]["turma"] == "C"


def test_turma_invalida_e_recusada(auth, monkeypatch):
    monkeypatch.setattr(auth, "supabase", _Sb())
    with pytest.raises(ValueError):
        auth.criar_usuario("A", "a@x.com", "1", "senha123", "producao", None, turma="Z")
    with pytest.raises(ValueError):
        auth.atualizar_turma_usuario("u1", "E")


def test_atualizar_turma_aceita_limpar(auth, monkeypatch):
    sb = _Sb()
    monkeypatch.setattr(auth, "supabase", sb)
    auth.atualizar_turma_usuario("u1", "B")
    auth.atualizar_turma_usuario("u1", None)
    assert sb.atualizados == [{"turma": "B"}, {"turma": None}]


def test_login_nao_quebra_se_a_coluna_turma_ainda_nao_existe(auth, monkeypatch):
    class _Quebrado:
        def table(self, nome):
            raise RuntimeError("column usuarios.turma does not exist")
    monkeypatch.setattr(auth, "supabase", _Quebrado())
    assert auth._buscar_turma("u1") is None
