"""Fixtures compartilhadas por todos os testes.

Cria um .streamlit/secrets.toml falso antes de cada teste — src/db.py lê
st.secrets assim que é importado (create_client acontece no import), então
mesmo testes que mockam tudo o resto precisam desse arquivo existir pra a
importação não quebrar.

Também recarrega src.auth/src.models/src.preenchimento_ui do zero antes
de cada teste — os "apps de teste" em fixture_apps/ trocam funções desses
módulos direto (`auth_mod.criar_usuario = fake`), sem usar o monkeypatch
do pytest, que desfaz sozinho. Sem esse reload, um teste que rodasse
depois de um fixture app herdaria a versão falsa da função, não a real.
"""
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def secrets_fake(monkeypatch, tmp_path):
    streamlit_dir = tmp_path / ".streamlit"
    streamlit_dir.mkdir()
    (streamlit_dir / "secrets.toml").write_text(
        'SUPABASE_URL = "https://fake.supabase.co"\n'
        'SUPABASE_KEY = "fake-key-for-test"\n'
        'APP_BASE_URL = "https://fake.streamlit.app"\n'
    )
    monkeypatch.chdir(tmp_path)

    for nome_modulo in ("src.auth", "src.models", "src.preenchimento_ui", "src.pdf_checklist", "src.pdf_dashboard"):
        if nome_modulo in sys.modules:
            importlib.reload(sys.modules[nome_modulo])

    yield

    for nome_modulo in ("src.auth", "src.models", "src.preenchimento_ui", "src.pdf_checklist", "src.pdf_dashboard"):
        if nome_modulo in sys.modules:
            importlib.reload(sys.modules[nome_modulo])
