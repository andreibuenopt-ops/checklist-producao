import pytest

from src.itens import listar_faltando


@pytest.fixture
def models():
    import src.models
    return src.models


class _Res:
    def __init__(self, data=None, count=0): self.data, self.count = data or [], count


class _Q:
    def __init__(self, sb, tabela): self.sb, self.t, self.op = sb, tabela, "select"
    def select(self, *a, **k): self.op = "select"; return self
    def delete(self): self.op = "delete"; return self
    def eq(self, *a): return self
    def limit(self, *a): return self
    def execute(self):
        self.sb.log.append((self.op, self.t))
        if self.op == "select":
            return _Res(self.sb.dados.get(self.t, []), count=len(self.sb.dados.get(self.t, [])))
        return _Res()


class _SB:
    def __init__(self, dados): self.dados, self.log = dados, []
    def table(self, t): return _Q(self, t)


def test_remover_horario_com_historico_pede_confirmacao(models, monkeypatch):
    sb = _SB({"checklist_respostas": [{"id": 1}, {"id": 2}]})
    monkeypatch.setattr(models, "supabase", sb)
    msg = models.remover_horario("h1")
    assert msg and "2 respostas" in msg
    assert ("delete", "checklist_template_horarios") not in sb.log   # nada apagado


def test_remover_horario_com_historico_confirmado_apaga_tudo(models, monkeypatch):
    sb = _SB({"checklist_respostas": [{"id": 1}]})
    monkeypatch.setattr(models, "supabase", sb)
    assert models.remover_horario("h1", apagar_historico=True) is None
    apagados = [t for op, t in sb.log if op == "delete"]
    assert apagados.index("checklist_respostas") < apagados.index("checklist_template_horarios")


def test_remover_horario_sem_historico_remove_direto(models, monkeypatch):
    sb = _SB({})
    monkeypatch.setattr(models, "supabase", sb)
    assert models.remover_horario("h1") is None
    assert ("delete", "checklist_template_horarios") in sb.log


def test_listar_faltando_ignora_filhas_de_pai_nao():
    itens = [{"id": "p", "pergunta": "Houve parada?"}, {"id": "f", "pergunta": "Qual?", "pai_item_id": "p"},
             {"id": "x", "pergunta": "Outra"}]
    horarios = [{"id": "h1", "horario": "06:30:00"}, {"id": "h2", "horario": "09:00:00"}]
    resp = {("p", "h1"): {"resposta": "Não"}, ("x", "h1"): {"resposta": "Sim"}}
    r = listar_faltando(itens, resp, horarios)
    assert [(l["horario"], l["pergunta"]) for l in r] == [("09:00", "Houve parada?"), ("09:00", "Outra")]
