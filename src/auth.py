"""Autenticação: login por e-mail/matrícula + senha (bcrypt), sessão via st.session_state.

Não existe autocadastro. Usuários só são criados pelo master, na página
de Administração — é a única forma de entrar no sistema (crachá,
e-mail da empresa e senha pessoal).
"""
from dataclasses import dataclass

import bcrypt
import streamlit as st

from src.db import supabase


@dataclass
class Usuario:
    id: str
    nome: str
    email: str
    matricula: str
    papel: str
    ativo: bool
    senha_temporaria: bool

    @property
    def eh_master(self) -> bool:
        return self.papel == "master"

    @property
    def pode_assinar_checklist(self) -> bool:
        return self.papel in ("supervisor", "coordenacao", "master")

    @property
    def pode_ver_dashboard(self) -> bool:
        return self.papel in ("supervisor", "coordenacao", "master")

    @property
    def pode_exportar_dashboard(self) -> bool:
        return self.papel in ("supervisor", "master")

    @property
    def pode_gerar_qrcodes(self) -> bool:
        return self.papel in ("supervisor", "coordenacao", "master")

    @property
    def pode_gerenciar_sistema(self) -> bool:
        return self.papel == "master"

    @property
    def pode_escolher_checklist_manualmente(self) -> bool:
        """Produção só preenche via QR Code fixo na área — sem escolher
        manualmente qual checklist abrir. Os demais papéis podem, para
        verificação/teste/administração."""
        return self.papel in ("supervisor", "coordenacao", "master")


def _usuario_from_row(row: dict) -> Usuario:
    return Usuario(
        id=row["id"],
        nome=row["nome"],
        email=row["email"],
        matricula=row["matricula"],
        papel=row["papel"],
        ativo=row["ativo"],
        senha_temporaria=row.get("senha_temporaria", False),
    )


def autenticar(identificador: str, senha: str):
    """identificador: e-mail OU matrícula (crachá). Retorna (Usuario|None, erro|None)."""
    identificador = (identificador or "").strip()
    if not identificador or not senha:
        return None, "Preencha usuário e senha."

    campo = "email" if "@" in identificador else "matricula"
    res = supabase.table("usuarios").select("*").eq(campo, identificador).limit(1).execute()
    if not res.data:
        return None, "Usuário não encontrado."

    row = res.data[0]
    if not row["ativo"]:
        return None, "Usuário desativado. Procure o administrador master."

    if not bcrypt.checkpw(senha.encode(), row["senha_hash"].encode()):
        return None, "Senha incorreta."

    return _usuario_from_row(row), None


def exigir_login() -> Usuario:
    if "usuario" in st.session_state:
        return st.session_state["usuario"]

    st.title("🔐 Login")
    st.caption("Acesse com seu e-mail da empresa ou número do crachá e sua senha pessoal.")
    with st.form("form_login"):
        identificador = st.text_input("E-mail ou matrícula (crachá)")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar", type="primary", use_container_width=True)

    if entrar:
        usuario, erro = autenticar(identificador, senha)
        if usuario:
            st.session_state["usuario"] = usuario
            st.rerun()
        else:
            st.error(erro)

    st.stop()


def logout():
    st.session_state.pop("usuario", None)


def criar_usuario(nome: str, email: str, matricula: str, senha: str, papel: str, criado_por_id: str):
    if papel not in ("producao", "supervisor", "coordenacao", "master"):
        raise ValueError("Papel inválido.")
    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    return (
        supabase.table("usuarios")
        .insert({
            "nome": nome,
            "email": email,
            "matricula": matricula,
            "senha_hash": senha_hash,
            "papel": papel,
            "criado_por": criado_por_id,
        })
        .execute()
    )


def resetar_senha(usuario_id: str, nova_senha_temporaria: str):
    """Master reseta a senha; o usuário é obrigado a trocá-la no próximo login."""
    senha_hash = bcrypt.hashpw(nova_senha_temporaria.encode(), bcrypt.gensalt()).decode()
    supabase.table("usuarios").update({
        "senha_hash": senha_hash,
        "senha_temporaria": True,
    }).eq("id", usuario_id).execute()


def trocar_senha(usuario_id: str, nova_senha: str):
    senha_hash = bcrypt.hashpw(nova_senha.encode(), bcrypt.gensalt()).decode()
    supabase.table("usuarios").update({
        "senha_hash": senha_hash,
        "senha_temporaria": False,
    }).eq("id", usuario_id).execute()
    if "usuario" in st.session_state:
        st.session_state["usuario"].senha_temporaria = False


def alternar_status(usuario_id: str, ativo: bool):
    supabase.table("usuarios").update({"ativo": ativo}).eq("id", usuario_id).execute()
