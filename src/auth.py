"""Autenticação: login por e-mail/matrícula + senha (bcrypt), sessão via st.session_state.

Existe autocadastro (aba "Primeira vez aqui?" na tela de login) — quem se
cadastra sozinho entra sempre como 'producao' (nível mais baixo, só
preenche checklist). Master ajusta o nível de acesso depois em
Administração → Usuários → Alterar nível de acesso.
"""
from dataclasses import dataclass

import bcrypt
import streamlit as st

from src.db import supabase
from src.models import obter_autocadastro_requer_aprovacao


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
        return self.papel in ("supervisor", "coordenacao", "administrador", "master")

    @property
    def pode_concluir_proprio_checklist(self) -> bool:
        """Produção pode concluir sozinha o checklist que ela mesma
        preencheu — sem precisar de login separado de um supervisor.
        Usa a própria sessão já autenticada como assinatura."""
        return self.papel == "producao"

    @property
    def pode_ver_dashboard(self) -> bool:
        return self.papel in ("supervisor", "coordenacao", "administrador", "master")

    @property
    def pode_exportar_dashboard(self) -> bool:
        return self.papel in ("supervisor", "administrador", "master")

    @property
    def pode_gerar_qrcodes(self) -> bool:
        return self.papel in ("supervisor", "coordenacao", "administrador", "master")

    @property
    def pode_abrir_5_porques(self) -> bool:
        """Análise 5 Porquês (RCA) só é aberta a critério da coordenação —
        produção e supervisor não decidem sozinhos abrir uma investigação
        formal de causa raiz. O 'Não' já fica registrado (item + descritivo)
        no PDF do checklist independente disso."""
        return self.papel in ("coordenacao", "administrador", "master")

    @property
    def pode_gerenciar_sistema(self) -> bool:
        """Libera a página de Administração. Master e administrador —
        o que muda entre os dois é pode_gerenciar_masters, abaixo."""
        return self.papel in ("administrador", "master")

    @property
    def pode_gerenciar_masters(self) -> bool:
        """Só o master mexe em quem é master — criar, promover, rebaixar
        ou desativar — e no toggle de aprovação de autocadastro. Evita
        que um administrador (mesmo de confiança) tranque o dono do
        sistema pra fora ou crie um "chefe" igual a si mesmo."""
        return self.papel == "master"

    @property
    def pode_escolher_checklist_manualmente(self) -> bool:
        """Produção só preenche via QR Code fixo na área — sem escolher
        manualmente qual checklist abrir. Os demais papéis podem, para
        verificação/teste/administração."""
        return self.papel in ("supervisor", "coordenacao", "administrador", "master")


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
    """identificador: e-mail OU matrícula (crachá). Retorna (Usuario|None, erro|None).

    A verificação da senha acontece DENTRO do Postgres (função
    autenticar_usuario, ver sql/schema.sql) — o hash bcrypt nunca chega
    até aqui. supabase.rpc() chama a função; a resposta já vem só com
    um boolean senha_valida, nunca com o hash.
    """
    identificador = (identificador or "").strip()
    if not identificador or not senha:
        return None, "Preencha usuário e senha."

    res = supabase.rpc("autenticar_usuario", {
        "p_identificador": identificador,
        "p_senha": senha,
    }).execute()

    if not res.data:
        return None, "Usuário não encontrado."

    row = res.data[0]
    if not row["ativo"]:
        return None, "Usuário desativado. Procure o administrador master."

    if not row["senha_valida"]:
        return None, "Senha incorreta."

    return _usuario_from_row(row), None


def exigir_login() -> Usuario:
    if "usuario" in st.session_state:
        return st.session_state["usuario"]

    st.title("🔐 Login")

    tab_entrar, tab_cadastrar = st.tabs(["Entrar", "🆕 Primeira vez aqui?"])

    with tab_entrar:
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

    with tab_cadastrar:
        st.caption(
            "Crie sua conta com seu crachá e e-mail da empresa. Você entra já "
            "com acesso de **Produção** (preencher checklist); o administrador "
            "master ajusta seu nível de acesso depois, se for o caso."
        )
        with st.form("form_cadastro"):
            nome = st.text_input("Nome completo")
            email = st.text_input("E-mail da empresa")
            matricula = st.text_input("Número do crachá (matrícula)")
            senha_nova = st.text_input("Crie uma senha", type="password")
            senha_confirmar = st.text_input("Confirme a senha", type="password")
            cadastrar = st.form_submit_button("Criar minha conta", type="primary", use_container_width=True)

        if cadastrar:
            if not all([nome.strip(), email.strip(), matricula.strip(), senha_nova]):
                st.error("Preencha todos os campos.")
            elif len(senha_nova) < 6:
                st.error("A senha deve ter no mínimo 6 caracteres.")
            elif senha_nova != senha_confirmar:
                st.error("As senhas não conferem.")
            else:
                requer_aprovacao = obter_autocadastro_requer_aprovacao()
                try:
                    criar_usuario(
                        nome.strip(), email.strip(), matricula.strip(), senha_nova,
                        "producao", None, ativo=not requer_aprovacao,
                    )
                except Exception as e:
                    st.error(f"Não foi possível criar a conta (e-mail ou matrícula já cadastrados?): {e}")
                else:
                    if requer_aprovacao:
                        st.success(
                            "Cadastro enviado! Sua conta fica pendente até o "
                            "administrador master ativar seu acesso."
                        )
                    else:
                        usuario, erro = autenticar(email.strip(), senha_nova)
                        if usuario:
                            st.session_state["usuario"] = usuario
                            st.success("Conta criada! Bem-vindo(a).")
                            st.rerun()
                        else:
                            st.warning("Conta criada. Vá na aba \"Entrar\" pra fazer login.")

    st.stop()


def logout():
    st.session_state.pop("usuario", None)


PAPEIS_VALIDOS = ("producao", "supervisor", "coordenacao", "administrador", "master")


def criar_usuario(
    nome: str, email: str, matricula: str, senha: str, papel: str, criado_por_id: str,
    ativo: bool = True, quem_cria=None,
):
    if papel not in PAPEIS_VALIDOS:
        raise ValueError("Papel inválido.")
    if papel == "master" and not (quem_cria and quem_cria.pode_gerenciar_masters):
        raise ValueError("Só o master pode criar outro usuário master.")
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
            "ativo": ativo,
        }, returning="minimal")
        .execute()
    )


def resetar_senha(usuario_id: str, nova_senha_temporaria: str, quem_altera=None):
    """Master reseta a senha; o usuário é obrigado a trocá-la no próximo login."""
    if not (quem_altera and quem_altera.pode_gerenciar_masters):
        alvo = supabase.table("usuarios").select("papel").eq("id", usuario_id).limit(1).execute()
        if alvo.data and alvo.data[0]["papel"] == "master":
            raise ValueError("Só o master pode resetar a senha de outro usuário master.")
    senha_hash = bcrypt.hashpw(nova_senha_temporaria.encode(), bcrypt.gensalt()).decode()
    supabase.table("usuarios").update({
        "senha_hash": senha_hash,
        "senha_temporaria": True,
    }, returning="minimal").eq("id", usuario_id).execute()


def trocar_senha(usuario_id: str, nova_senha: str):
    senha_hash = bcrypt.hashpw(nova_senha.encode(), bcrypt.gensalt()).decode()
    supabase.table("usuarios").update({
        "senha_hash": senha_hash,
        "senha_temporaria": False,
    }, returning="minimal").eq("id", usuario_id).execute()
    if "usuario" in st.session_state:
        st.session_state["usuario"].senha_temporaria = False


def alternar_status(usuario_id: str, ativo: bool, quem_altera=None):
    if not ativo and not (quem_altera and quem_altera.pode_gerenciar_masters):
        alvo = supabase.table("usuarios").select("papel").eq("id", usuario_id).limit(1).execute()
        if alvo.data and alvo.data[0]["papel"] == "master":
            raise ValueError("Só o master pode desativar outro usuário master.")
    supabase.table("usuarios").update({"ativo": ativo}, returning="minimal").eq("id", usuario_id).execute()


def atualizar_papel_usuario(usuario_id: str, novo_papel: str, quem_altera=None):
    """Usado pra promover/rebaixar alguém — em especial quem se
    autocadastrou (sempre entra como 'producao'). Só o master mexe em
    quem já é master, ou promove alguém a master."""
    if novo_papel not in PAPEIS_VALIDOS:
        raise ValueError("Papel inválido.")
    pode_masters = bool(quem_altera and quem_altera.pode_gerenciar_masters)
    if novo_papel == "master" and not pode_masters:
        raise ValueError("Só o master pode promover alguém a master.")
    if not pode_masters:
        alvo = supabase.table("usuarios").select("papel").eq("id", usuario_id).limit(1).execute()
        if alvo.data and alvo.data[0]["papel"] == "master":
            raise ValueError("Só o master pode alterar o nível de outro usuário master.")
    supabase.table("usuarios").update({"papel": novo_papel}, returning="minimal").eq("id", usuario_id).execute()
    if st.session_state.get("usuario") and st.session_state["usuario"].id == usuario_id:
        st.session_state["usuario"].papel = novo_papel
