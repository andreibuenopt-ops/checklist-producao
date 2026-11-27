"""App de teste (navegador real): página Modo offline com banco FALSO em arquivo."""
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import streamlit as st

import src.auth as auth_mod
import src.models as models_mod
import src.offline as off
import src.sidebar as sidebar_mod

LOG = Path(os.environ["E2E_LOG"])
ITENS = [
    {"id": "i1", "pergunta": "Houve parada?", "criticidade": "alta", "tipo_resposta": "sim_nao"},
    {"id": "f1", "pergunta": "Qual o local?", "criticidade": "media", "tipo_resposta": "sim_nao", "pai_item_id": "i1", "exige_foto": True},
    {"id": "i2", "pergunta": "Vazamento de óleo?", "criticidade": "critica", "tipo_resposta": "sim_nao"},
    {"id": "t1", "pergunta": "Comentário", "criticidade": "media", "tipo_resposta": "texto_livre"},
]
TPL = [{"id": "tpl1", "codigo": "FR-1", "titulo": "Serras", "area": "Área das Serras", "tipo_area": "externo",
        "setores_processo": {"nome": "Acabamento"}}]
HOR = {1: [{"id": "h1", "horario": "07:30:00"}], 2: [{"id": "h2", "horario": "15:30:00"}], 3: [{"id": "h3", "horario": "23:30:00"}]}


def _anota(**k):
    with LOG.open("a") as f:
        f.write(json.dumps(k, ensure_ascii=False) + "\n")


off.listar_templates = lambda *a, **k: TPL
off.listar_itens = lambda tid, incluir_inativos=False: ITENS
off.listar_horarios = lambda tid, turno: HOR[turno]
off.obter_ou_criar_checklist = lambda t, turno, d: {"id": f"ck-{t}-{turno}-{d}", "status": "em_andamento"}
off.definir_colaborador = lambda *a: None
off.listar_fotos = lambda ckid: []
off.salvar_justificativa_atraso = lambda ck, h, txt, u: _anota(tipo="just", ck=ck, h=h, txt=txt)
off.enviar_foto = lambda ck, i, h, conteudo, u, id_cliente=None: _anota(tipo="foto", ck=ck, item=i, h=h, bytes=len(conteudo), idc=id_cliente)


class _Q:
    def __init__(self): self.rows = []
    def select(self, *a): return self
    def eq(self, *a): return self
    def upsert(self, rows, on_conflict=None):
        _anota(tipo="upsert", rows=rows); return self
    def execute(self): return SimpleNamespace(data=[])


off.supabase = SimpleNamespace(table=lambda n: _Q())
usuario = SimpleNamespace(id="u1", nome="Operador Teste", papel="producao", matricula="1",
                          pode_ver_dashboard=False, pode_gerar_qrcodes=False, pode_gerenciar_sistema=False,
                          pode_abrir_5_porques=False, pode_exportar_dashboard=False, pode_escolher_checklist_manualmente=False)
auth_mod.exigir_login = lambda: usuario
sidebar_mod.mostrar_usuario_logado = lambda u: None
sidebar_mod.obter_logo_url_com_fallback = lambda: None
models_mod.obter_cor_primaria = lambda: "#667f38"
models_mod.obter_logo_url_com_fallback = lambda: None

exec(open(ROOT / "pages" / "11_📴_Modo_offline.py", encoding="utf-8").read())
