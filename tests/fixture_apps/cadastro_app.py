"""App de teste: login e autocadastro, com Supabase mockado em memória.

Usado por tests/test_auth.py via AppTest.from_file(). A variável de
ambiente TESTE_REQUER_APROVACAO controla o toggle de aprovação de
autocadastro pra cada cenário de teste.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

import src.auth as auth_mod

USUARIOS_FAKE = {}


class _FakeRPCResult:
    def __init__(self, data):
        self.data = data


def _fake_rpc(nome_funcao, params):
    class _Chamada:
        def execute(self_inner):
            identificador = params["p_identificador"]
            senha = params["p_senha"]
            for u in USUARIOS_FAKE.values():
                if u["email"] == identificador or u["matricula"] == identificador:
                    return _FakeRPCResult([{
                        "id": u["id"], "nome": u["nome"], "email": u["email"],
                        "matricula": u["matricula"], "papel": u["papel"],
                        "ativo": u["ativo"], "senha_temporaria": u["senha_temporaria"],
                        "senha_valida": senha == u["_senha_real"],
                    }])
            return _FakeRPCResult([])
    return _Chamada()


def _fake_criar_usuario(nome, email, matricula, senha, papel, criado_por_id, ativo=True, quem_cria=None, turma=None):
    if any(u["email"] == email or u["matricula"] == matricula for u in USUARIOS_FAKE.values()):
        raise Exception("duplicate key value violates unique constraint")
    uid = f"user-{len(USUARIOS_FAKE) + 1}"
    USUARIOS_FAKE[uid] = {
        "id": uid, "nome": nome, "email": email, "matricula": matricula,
        "_senha_real": senha, "papel": papel, "ativo": ativo, "senha_temporaria": False,
    }
    return uid


auth_mod.supabase = type("FakeSupabase", (), {"rpc": staticmethod(_fake_rpc)})()
auth_mod.criar_usuario = _fake_criar_usuario
auth_mod.obter_autocadastro_requer_aprovacao = lambda: os.environ.get("TESTE_REQUER_APROVACAO") == "1"

# Usuário pré-existente, pra testar a aba "Entrar"
USUARIOS_FAKE["seed-1"] = {
    "id": "seed-1", "nome": "Usuário Semente", "email": "semente@guararapes.com.br",
    "matricula": "10000", "_senha_real": "senhaSemente1", "papel": "producao",
    "ativo": True, "senha_temporaria": False,
}

usuario = auth_mod.exigir_login()
st.write("LOGADO:", usuario.nome, usuario.papel, usuario.ativo)
