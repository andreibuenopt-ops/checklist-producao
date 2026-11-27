"""Remover pergunta: com histórico DESATIVA (nada se perde); sem histórico apaga; sem a coluna `ativo` avisa."""
from types import SimpleNamespace

import pytest


@pytest.fixture
def models():
    import src.models
    src.models._ITEM_TEM_ATIVO = False
    return src.models


class _Q:
    def __init__(self, sb, tabela): self.sb, self.t, self.op, self.payload, self.filtros = sb, tabela, "select", None, []
    def select(self, *a, **k): self.op = "select"; self.cols = a; return self
    def update(self, p): self.op, self.payload = "update", p; return self
    def delete(self): self.op = "delete"; return self
    def eq(self, c, v): self.filtros.append(("eq", c, v)); return self
    def in_(self, c, v): self.filtros.append(("in", c, list(v))); return self
    def neq(self, c, v): self.filtros.append(("neq", c, v)); return self
    def limit(self, *a): return self
    def order(self, *a): return self
    def execute(self):
        self.sb.log.append((self.op, self.t, self.payload, self.filtros))
        if self.op == "select" and self.cols[:1] == ("ativo",) and not self.sb.tem_ativo:
            from postgrest.exceptions import APIError
            raise APIError({"message": "column ativo does not exist", "code": "42703"})
        if self.op == "select" and self.t == "checklist_template_itens":
            return SimpleNamespace(data=self.sb.filhas, count=None)
        if self.op == "select":
            return SimpleNamespace(data=[], count=self.sb.historico.get(self.t, 0))
        return SimpleNamespace(data=[], count=None)


class _SB:
    def __init__(self, historico=None, tem_ativo=True, filhas=None):
        self.historico, self.tem_ativo, self.filhas, self.log = historico or {}, tem_ativo, filhas or [], []
    def table(self, t): return _Q(self, t)


def _ops(sb, op, tabela):
    return [l for l in sb.log if l[0] == op and l[1] == tabela]


def test_com_historico_desativa_e_nao_apaga(models, monkeypatch):
    sb = _SB(historico={"checklist_respostas": 12}, filhas=[{"id": "f1"}])
    monkeypatch.setattr(models, "supabase", sb)
    assert models.remover_item("i1") == "desativado"
    (_, _, payload, filtros), = _ops(sb, "update", "checklist_template_itens")
    assert payload == {"ativo": False} and ("in", "id", ["i1", "f1"]) in filtros     # a filha vai junto
    assert not _ops(sb, "delete", "checklist_template_itens")


def test_so_com_fotos_tambem_desativa(models, monkeypatch):
    sb = _SB(historico={"checklist_fotos": 1})
    monkeypatch.setattr(models, "supabase", sb)
    assert models.remover_item("i1") == "desativado"


def test_sem_historico_apaga_de_vez_e_solta_sugestoes(models, monkeypatch):
    sb = _SB()
    monkeypatch.setattr(models, "supabase", sb)
    assert models.remover_item("i1") == "excluido"
    assert _ops(sb, "delete", "checklist_template_itens")
    assert _ops(sb, "update", "checklist_sugestoes")[0][2] == {"item_id": None}


def test_com_historico_mas_sem_a_coluna_ativo_pede_a_migracao(models, monkeypatch):
    sb = _SB(historico={"checklist_respostas": 3}, tem_ativo=False)
    monkeypatch.setattr(models, "supabase", sb)
    with pytest.raises(models.ItemSemMigracao):
        models.remover_item("i1")
    assert not _ops(sb, "delete", "checklist_template_itens")                      # nada foi apagado


def test_restaurar_reativa_item_e_filhas(models, monkeypatch):
    sb = _SB(filhas=[{"id": "f1"}])
    monkeypatch.setattr(models, "supabase", sb)
    models.restaurar_item("i1")
    (_, _, payload, filtros), = _ops(sb, "update", "checklist_template_itens")
    assert payload == {"ativo": True} and ("in", "id", ["i1", "f1"]) in filtros


def test_listar_itens_esconde_removidas_so_se_a_coluna_existe(models, monkeypatch):
    sb = _SB()
    monkeypatch.setattr(models, "supabase", sb)
    models.listar_itens("t1")
    assert ("neq", "ativo", False) in _ops(sb, "select", "checklist_template_itens")[-1][3]
    sb.log.clear()
    models.listar_itens("t1", incluir_inativos=True)                               # histórico mostra tudo
    assert ("neq", "ativo", False) not in _ops(sb, "select", "checklist_template_itens")[-1][3]
    models._ITEM_TEM_ATIVO = False
    sb2 = _SB(tem_ativo=False)
    monkeypatch.setattr(models, "supabase", sb2)
    models.listar_itens("t1")                                                      # antes da migração: sem filtro, sem erro
    assert ("neq", "ativo", False) not in _ops(sb2, "select", "checklist_template_itens")[-1][3]
