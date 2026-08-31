"""App de teste: página de Preencher Checklist, papel 'producao', sem QR.

Usado por tests/test_preencher_manual.py via AppTest.from_file(). Confirma
que produção vê a lista somente-leitura, sem nenhum widget clicável pra
abrir/preencher um checklist manualmente.
"""
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import src.auth as auth_mod
import src.models as models_mod


def _fake_exigir_login():
    return SimpleNamespace(
        id="u1", nome="Operador Teste", papel="producao",
        pode_escolher_checklist_manualmente=False,
        matricula="12345",
    )


def _fake_listar_templates(apenas_ativos=True):
    return [
        {"id": "t1", "titulo": "Checklist de inspeções - Sifter", "codigo": "FRCDM2011.r02",
         "setores_processo": {"nome": "Planta Térmica", "ordem": 3}, "ordem_processo": 35},
        {"id": "t2", "titulo": "Checklist de inspeções - Silo de Cavaco", "codigo": "FRCDM2004.r01",
         "setores_processo": {"nome": "Silo de Cavaco", "ordem": 2}, "ordem_processo": 20},
    ]


auth_mod.exigir_login = _fake_exigir_login
models_mod.listar_templates = _fake_listar_templates
models_mod.obter_cor_primaria = lambda: "#667f38"
models_mod.obter_logo_url_com_fallback = lambda: None

exec(open(
    Path(__file__).resolve().parent.parent.parent / "pages" / "1_📋_Preencher_Checklist.py",
    encoding="utf-8",
).read())
