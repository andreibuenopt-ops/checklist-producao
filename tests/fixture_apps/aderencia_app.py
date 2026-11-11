"""App de teste: página de Aderência (índice + relatório mensal)."""
import os
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import src.aderencia as aderencia_mod
import src.auth as auth_mod
import src.models as models_mod
from src.aderencia import calcular_aderencia, por_checklist, por_turno, ranking_esquecimentos, somar
from src.turnos import chave_ordem

PAPEL = os.environ.get("TESTE_PAPEL", "supervisor")


def _usuario():
    return SimpleNamespace(
        id="u1", nome="Teste", papel=PAPEL, matricula="1",
        pode_ver_dashboard=PAPEL != "producao", pode_gerar_qrcodes=False, pode_gerenciar_sistema=False,
        pode_abrir_5_porques=False, pode_exportar_dashboard=PAPEL == "supervisor",
    )


def _relatorio(inicio, fim):
    tpls = [{"id": f"t{i}", "area": f"Checklist {i}", "codigo": f"00{i}", "criado_em": "2000-01-01"} for i in range(1, 4)]
    cks = [{"template_id": "t1", "turno_id": t, "data": inicio.isoformat(), "status": "completo", "incompleto": False}
           for t in (1, 2, 3)]
    linhas = calcular_aderencia(tpls, cks, inicio, fim, chave_ordem(1, fim))
    return {"inicio": inicio, "fim": fim, "linhas": linhas, "geral": somar(linhas), "por_turno": por_turno(linhas),
            "por_checklist": por_checklist(linhas), "ranking": ranking_esquecimentos(linhas),
            "total_nao": 4, "total_atrasos": 1,
            "itens_mais_nao": [{"area": "Checklist 1", "pergunta": "Correia?", "qtd": 3}]}


auth_mod.exigir_login = _usuario
models_mod.obter_cor_primaria = lambda: "#667f38"
models_mod.obter_logo_url_com_fallback = lambda: None
models_mod.obter_logo_bytes_com_fallback = lambda: None
aderencia_mod.montar_relatorio = _relatorio

exec(open(Path(__file__).resolve().parent.parent.parent / "pages" / "9_📈_Aderência.py", encoding="utf-8").read())
