"""Testes da hierarquia administrador/master.

Regra: administrador faz a administração do dia a dia, mas só o master
cria/promove/rebaixa/desativa/reseta senha de outro master, e só o
master mexe no toggle de aprovação de autocadastro. Testado direto nas
funções de src/auth.py (sem UI) — é a barreira que protege contra um
administrador comprometido travar o dono do sistema pra fora.

Import de src.auth é feito DENTRO da fixture `auth_mod` (não no topo do
arquivo) — src/db.py cria o client do Supabase assim que é importado,
lendo st.secrets; se importássemos no topo, isso rodaria na hora do
pytest coletar os testes, antes da fixture secrets_fake (em conftest.py)
ter criado o secrets.toml falso.
"""
from types import SimpleNamespace

import pytest


@pytest.fixture
def auth_mod(secrets_fake):
    import src.auth
    return src.auth


def _usuario(auth_mod, papel: str):
    return auth_mod.Usuario(
        id=f"id-{papel}", nome=f"Fulano {papel}", email=f"{papel}@x.com",
        matricula="00000", papel=papel, ativo=True, senha_temporaria=False,
    )


class _FakeTable:
    """Mock mínimo de supabase.table('usuarios') — só o suficiente pras
    funções de auth.py rodarem sem bater no Supabase de verdade."""

    def __init__(self, banco, papel_do_alvo=None):
        self.banco = banco
        self.papel_do_alvo = papel_do_alvo
        self._filtro_id = None

    def insert(self, dados, returning=None):
        self.banco.append(dict(dados))
        return self

    def update(self, dados, returning=None):
        self._ultima_atualizacao = dados
        return self

    def select(self, *_a, **_k):
        return self

    def eq(self, _campo, valor):
        self._filtro_id = valor
        return self

    def limit(self, _n):
        return self

    def execute(self):
        if self.papel_do_alvo is not None:
            return SimpleNamespace(data=[{"papel": self.papel_do_alvo}])
        return SimpleNamespace(data=[])


@pytest.fixture
def banco_falso(auth_mod, monkeypatch):
    """Substitui supabase.table('usuarios') por um mock, parametrizável
    com o papel do usuário-alvo da operação (pra simular "o alvo é
    master" vs "o alvo não é master")."""
    inseridos = []

    def _factory(papel_do_alvo=None):
        fake_supabase = SimpleNamespace(
            table=lambda nome: _FakeTable(inseridos, papel_do_alvo=papel_do_alvo)
        )
        monkeypatch.setattr(auth_mod, "supabase", fake_supabase)
        return inseridos

    return _factory


# ---------------------------------------------------------------------
# criar_usuario — só master cria outro master
# ---------------------------------------------------------------------
def test_master_pode_criar_outro_master(auth_mod, banco_falso):
    banco_falso()
    master = _usuario(auth_mod, "master")
    auth_mod.criar_usuario("Novo Master", "nm@x.com", "111", "senha123456", "master", master.id, quem_cria=master)


def test_administrador_nao_pode_criar_master(auth_mod, banco_falso):
    banco_falso()
    administrador = _usuario(auth_mod, "administrador")
    with pytest.raises(ValueError, match="Só o master"):
        auth_mod.criar_usuario(
            "Tentativa", "t@x.com", "222", "senha123456", "master",
            administrador.id, quem_cria=administrador,
        )


def test_administrador_pode_criar_supervisor(auth_mod, banco_falso):
    banco_falso()
    administrador = _usuario(auth_mod, "administrador")
    auth_mod.criar_usuario(
        "Novo Supervisor", "ns@x.com", "333", "senha123456", "supervisor",
        administrador.id, quem_cria=administrador,
    )


def test_ninguem_logado_nao_pode_criar_master(auth_mod, banco_falso):
    banco_falso()
    with pytest.raises(ValueError, match="Só o master"):
        auth_mod.criar_usuario("Tentativa", "t2@x.com", "444", "senha123456", "master", None, quem_cria=None)


# ---------------------------------------------------------------------
# atualizar_papel_usuario — só master promove a master ou mexe em master
# ---------------------------------------------------------------------
def test_administrador_nao_pode_promover_a_master(auth_mod, banco_falso):
    banco_falso(papel_do_alvo="supervisor")
    administrador = _usuario(auth_mod, "administrador")
    with pytest.raises(ValueError, match="Só o master"):
        auth_mod.atualizar_papel_usuario("algum-id", "master", quem_altera=administrador)


def test_administrador_nao_pode_alterar_nivel_de_um_master(auth_mod, banco_falso):
    banco_falso(papel_do_alvo="master")
    administrador = _usuario(auth_mod, "administrador")
    with pytest.raises(ValueError, match="Só o master"):
        auth_mod.atualizar_papel_usuario("algum-id-master", "coordenacao", quem_altera=administrador)


def test_administrador_pode_promover_producao_a_supervisor(auth_mod, banco_falso):
    banco_falso(papel_do_alvo="producao")
    administrador = _usuario(auth_mod, "administrador")
    auth_mod.atualizar_papel_usuario("algum-id", "supervisor", quem_altera=administrador)  # não levanta


def test_master_pode_alterar_nivel_de_outro_master(auth_mod, banco_falso):
    banco_falso(papel_do_alvo="master")
    master = _usuario(auth_mod, "master")
    auth_mod.atualizar_papel_usuario("algum-id-master", "coordenacao", quem_altera=master)  # não levanta


# ---------------------------------------------------------------------
# alternar_status — só master desativa outro master
# ---------------------------------------------------------------------
def test_administrador_nao_pode_desativar_master(auth_mod, banco_falso):
    banco_falso(papel_do_alvo="master")
    administrador = _usuario(auth_mod, "administrador")
    with pytest.raises(ValueError, match="Só o master"):
        auth_mod.alternar_status("algum-id-master", False, quem_altera=administrador)


def test_administrador_pode_desativar_supervisor(auth_mod, banco_falso):
    banco_falso(papel_do_alvo="supervisor")
    administrador = _usuario(auth_mod, "administrador")
    auth_mod.alternar_status("algum-id", False, quem_altera=administrador)  # não levanta


# ---------------------------------------------------------------------
# resetar_senha — só master reseta senha de outro master
# ---------------------------------------------------------------------
def test_administrador_nao_pode_resetar_senha_de_master(auth_mod, banco_falso):
    banco_falso(papel_do_alvo="master")
    administrador = _usuario(auth_mod, "administrador")
    with pytest.raises(ValueError, match="Só o master"):
        auth_mod.resetar_senha("algum-id-master", "novaSenha123", quem_altera=administrador)


def test_administrador_pode_resetar_senha_de_supervisor(auth_mod, banco_falso):
    banco_falso(papel_do_alvo="supervisor")
    administrador = _usuario(auth_mod, "administrador")
    auth_mod.resetar_senha("algum-id", "novaSenha123", quem_altera=administrador)  # não levanta


# ---------------------------------------------------------------------
# Propriedades de permissão do dataclass Usuario
# ---------------------------------------------------------------------
def test_administrador_acessa_administracao(auth_mod):
    assert _usuario(auth_mod, "administrador").pode_gerenciar_sistema is True


def test_producao_nao_acessa_administracao(auth_mod):
    assert _usuario(auth_mod, "producao").pode_gerenciar_sistema is False


def test_so_master_gerencia_masters(auth_mod):
    assert _usuario(auth_mod, "master").pode_gerenciar_masters is True
    assert _usuario(auth_mod, "administrador").pode_gerenciar_masters is False
    assert _usuario(auth_mod, "coordenacao").pode_gerenciar_masters is False
