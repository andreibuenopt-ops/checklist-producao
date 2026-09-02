"""Bootstrap do primeiro usuário master.

Rode este script UMA VEZ, localmente, com o venv do projeto ativado:
    python scripts/criar_master.py

Depois disso, TODOS os demais usuários (produção, supervisor, coordenação,
outros masters) são cadastrados pela própria tela de Administração do app,
logado como este master.

Não commite este arquivo com a senha preenchida — ele pede a senha em
tempo de execução (getpass) e não a expõe no terminal.
"""
import getpass
import sys
from pathlib import Path

import bcrypt
from supabase import create_client

# ---------------------------------------------------------------------
# Lê as credenciais do mesmo secrets.toml usado pelo Streamlit, se existir.
# Senão, pede no terminal.
# ---------------------------------------------------------------------
def _ler_secrets():
    caminho = Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml"
    if not caminho.exists():
        return None, None
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
    with open(caminho, "rb") as f:
        dados = tomllib.load(f)
    return dados.get("SUPABASE_URL"), dados.get("SUPABASE_KEY")


url, key = _ler_secrets()
if not url:
    url = input("SUPABASE_URL: ").strip()
if not key:
    key = input("SUPABASE_KEY: ").strip()

sb = create_client(url, key)

print("=== Criação do usuário MASTER ===")
nome = input("Nome completo: ").strip()
email = input("E-mail da empresa: ").strip()
matricula = input("Número do crachá (matrícula): ").strip()
senha = getpass.getpass("Senha mestre: ")
confirmar = getpass.getpass("Confirme a senha mestre: ")

if not all([nome, email, matricula, senha]):
    print("Todos os campos são obrigatórios.")
    sys.exit(1)

if senha != confirmar:
    print("As senhas não conferem.")
    sys.exit(1)

if len(senha) < 6:
    print("Senha muito curta (mínimo 6 caracteres).")
    sys.exit(1)

senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

try:
    sb.table("usuarios").insert({
        "nome": nome,
        "email": email,
        "matricula": matricula,
        "senha_hash": senha_hash,
        "papel": "master",
    }).execute()
    print(f"\nUsuário master '{nome}' criado com sucesso.")
    print("Faça login no app com esse e-mail/matrícula e a senha definida.")
except Exception as e:
    print(f"\nErro ao criar o usuário master (e-mail/matrícula já existe?): {e}")
    sys.exit(1)
