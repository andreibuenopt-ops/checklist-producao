"""Fixtures compartilhadas por todos os testes.

Cria um .streamlit/secrets.toml falso antes de cada teste — src/db.py lê
st.secrets assim que é importado (create_client acontece no import), então
mesmo testes que mockam tudo o resto precisam desse arquivo existir pra a
importação não quebrar.
"""
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
