"""Servidor do modo offline: o que é aceito e o que é recusado."""
import base64
from types import SimpleNamespace

import pytest

USUARIO = SimpleNamespace(id="u1", nome="Ana")
ITENS = [
    {"id": "i1", "pergunta": "Parada?", "tipo_resposta": "sim_nao"},
    {"id": "i2", "pergunta": "Vazamento?", "tipo_resposta": "sim_nao"},
]


@pytest.fixture()
def off(monkeypatch):
    import src.offline as off
    estado = SimpleNamespace(upserts=[], justs=[], fotos_enviadas=[], status="em_andamento", fotos_banco=[],
                             existentes=[], colaborador=[])

    class Q:
        def __init__(self, tabela): self.tabela = tabela
        def select(self, *a): return self
        def eq(self, *a): return self
        def upsert(self, rows, on_conflict=None): estado.upserts += rows; return self
        def execute(self): return SimpleNamespace(data=estado.existentes if self.tabela == "checklist_respostas" else [])

    monkeypatch.setattr(off, "supabase", SimpleNamespace(table=Q))
    monkeypatch.setattr(off, "listar_templates", lambda *a, **k: [{"id": "t1"}])
    monkeypatch.setattr(off, "listar_itens", lambda t: ITENS)
    monkeypatch.setattr(off, "listar_horarios", lambda t, turno: [{"id": "h1"}])
    monkeypatch.setattr(off, "obter_ou_criar_checklist", lambda t, turno, d: {"id": "ck", "status": estado.status})
    monkeypatch.setattr(off, "definir_colaborador", lambda ck, u: estado.colaborador.append((ck, u)))
    monkeypatch.setattr(off, "salvar_justificativa_atraso", lambda ck, h, t, u: estado.justs.append((h, t)))
    monkeypatch.setattr(off, "listar_fotos", lambda ck: estado.fotos_banco)
    monkeypatch.setattr(off, "enviar_foto", lambda *a, **k: estado.fotos_enviadas.append((a, k)))
    off.estado = estado
    return off


def _ronda(**extra):
    return {"tipo": "ronda", "template_id": "t1", "turno_id": 2, "data_ref": "2026-11-24", "user_id": "u1",
            "respostas": {"i1|h1": {"r": "Sim", "t": 1700000000000}, "i2|h1": {"r": "Não", "o": "óleo", "t": 1700000000000}},
            "justificativas": {"h1": "estava no pátio"}, **extra}


def test_grava_respostas_e_justificativa_com_o_usuario_logado(off):
    r = off.gravar_ronda(_ronda(), USUARIO)
    assert r["estado"] == "ok"
    assert {(u["item_id"], u["resposta"], u["respondido_por"]) for u in off.estado.upserts} == {("i1", "Sim", "u1"), ("i2", "Não", "u1")}
    assert off.estado.justs == [("h1", "estava no pátio")] and off.estado.colaborador == [("ck", "u1")]


def test_recusa_registro_de_outra_pessoa(off):
    r = off.gravar_ronda(_ronda(user_id="outro"), USUARIO)
    assert r["estado"] == "bloqueado" and "outra pessoa" in r["msg"] and not off.estado.upserts


def test_recusa_checklist_ja_assinado(off):
    off.estado.status = "completo"
    r = off.gravar_ronda(_ronda(), USUARIO)
    assert r["estado"] == "bloqueado" and "assinado" in r["msg"] and not off.estado.upserts


def test_recusa_turno_invalido_e_template_inexistente(off):
    assert off.gravar_ronda(_ronda(turno_id=9), USUARIO)["estado"] == "bloqueado"
    assert off.gravar_ronda(_ronda(template_id="nao-existe"), USUARIO)["estado"] == "bloqueado"


def test_nao_sobrescreve_resposta_mais_nova_do_banco(off):
    off.estado.existentes = [{"item_id": "i1", "horario_id": "h1", "respondido_em": "2030-01-01T00:00:00+00:00"}]
    r = off.gravar_ronda(_ronda(), USUARIO)
    assert [u["item_id"] for u in off.estado.upserts] == ["i2"] and r["avisos"]


def _foto(**extra):
    return {"tipo": "foto", "id": "abcdef1234567890", "template_id": "t1", "turno_id": 2, "data_ref": "2026-11-24",
            "user_id": "u1", "item_id": "i1", "horario_id": "h1", "b64": base64.b64encode(b"jpegbytes").decode(), **extra}


def test_foto_ok_usa_id_do_celular_no_nome(off):
    assert off.gravar_foto(_foto(), USUARIO)["estado"] == "ok"
    (args, kw), = off.estado.fotos_enviadas
    assert args[:3] == ("ck", "i1", "h1") and args[3] == b"jpegbytes" and kw["id_cliente"] == "abcdef1234567890"


def test_foto_repetida_nao_duplica(off):
    off.estado.fotos_banco = [{"item_id": "i1", "horario_id": "h1", "caminho": "ck/i1_h1_abcdef123456.jpg"}]
    assert off.gravar_foto(_foto(), USUARIO)["estado"] == "ok"
    assert not off.estado.fotos_enviadas


def test_foto_respeita_limite_e_valida_entrada(off):
    off.estado.fotos_banco = [{"item_id": "i1", "horario_id": "h1", "caminho": f"x{n}"} for n in range(3)]
    assert "limite" in off.gravar_foto(_foto(), USUARIO)["msg"] and not off.estado.fotos_enviadas
    assert off.gravar_foto(_foto(id="../../x"), USUARIO)["estado"] == "bloqueado"
    assert off.gravar_foto(_foto(b64="!!!"), USUARIO)["estado"] == "bloqueado"
    assert off.gravar_foto(_foto(item_id="inexistente"), USUARIO)["estado"] == "bloqueado"
