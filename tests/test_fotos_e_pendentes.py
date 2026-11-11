import io
from datetime import date

import pytest
from PIL import Image

import src.turnos as turnos


# src.db lê os secrets assim que é importado — por isso fotos/models são
# importados dentro de fixtures (o conftest cria os secrets antes de cada teste).
@pytest.fixture
def fotos():
    import src.fotos
    return src.fotos


@pytest.fixture
def models():
    import src.models
    return src.models


# ----------------------------------------------------------------- Supabase falso
class _Res:
    def __init__(self, data, count=None):
        self.data, self.count = data, count


class _Query:
    def __init__(self, linhas):
        self.linhas, self._filtros, self._range, self._count, self._limit, self._insert = linhas, [], None, False, None, None

    def select(self, *_a, count=None, **_k):
        self._count = bool(count)
        return self

    def eq(self, col, val): self._filtros.append(("eq", col, val)); return self
    def gte(self, col, val): self._filtros.append(("gte", col, val)); return self
    def lte(self, col, val): self._filtros.append(("lte", col, val)); return self
    def order(self, *_a, **_k): return self
    def limit(self, n): self._limit = n; return self
    def range(self, ini, fim): self._range = (ini, fim); return self

    def execute(self):
        def ok(l):
            for op, col, val in self._filtros:
                v = l.get(col)
                if op == "eq" and v != val: return False
                if op == "gte" and not str(v) >= str(val): return False
                if op == "lte" and not str(v) <= str(val): return False
            return True
        sel = [l for l in self.linhas if ok(l)]
        total = len(sel)
        if self._range:
            sel = sel[self._range[0]:self._range[1] + 1]
        if self._limit:
            sel = sel[:self._limit]
        return _Res(sel, count=total if self._count else None)


class _SupabaseFalso:
    def __init__(self, tabelas): self.tabelas = tabelas
    def table(self, nome): return _Query(self.tabelas[nome])


# ----------------------------------------------------------------- paginação
def test_todas_as_linhas_junta_todas_as_paginas(models, monkeypatch):
    linhas = [{"id": i, "data": "2026-10-01"} for i in range(2500)]
    monkeypatch.setattr(models, "supabase", _SupabaseFalso({"t": linhas}))
    r = models._todas_as_linhas(lambda: models.supabase.table("t").select("*").order("id"))
    assert len(r) == 2500   # sem paginar, voltariam só 1000


# ----------------------------------------------------------------- pendentes de assinatura
def test_pendentes_so_turnos_encerrados_com_respostas(models, monkeypatch):
    atual = turnos.Turno(1, "Manhã", date(2026, 10, 14))     # agora: A do dia 14
    monkeypatch.setattr(models, "turno_e_data_referencia", lambda: atual)

    def ck(cid, turno_id, data, status="em_andamento"):
        return {"id": cid, "template_id": "t1", "turno_id": turno_id, "data": data, "status": status,
                "colaborador_id": "u1"}

    checklists = [
        ck("passado_com_resp", 2, "2026-10-13"),    # B de ontem  -> pendente
        ck("passado_vazio", 3, "2026-10-14"),       # C de hoje, sem respostas -> fora
        ck("atual", 1, "2026-10-14"),               # turno em andamento -> fora
        ck("ja_assinado", 2, "2026-10-13", status="completo"),
    ]
    itens = [{"id": f"i{n}"} for n in range(4)]
    horarios = [{"id": "h1"}, {"id": "h2"}]
    respondidas = {("i0", "h1"): {"resposta": "Sim"}, ("i1", "h1"): {"resposta": "Sim"}, ("i0", "h2"): {"resposta": "Não"}}
    monkeypatch.setattr(models, "supabase", _SupabaseFalso({"checklists": checklists}))
    monkeypatch.setattr(models, "listar_itens", lambda tid: itens)
    monkeypatch.setattr(models, "listar_horarios", lambda tid, turno: horarios)
    monkeypatch.setattr(models, "listar_respostas", lambda cid: respondidas if cid == "passado_com_resp" else {})
    monkeypatch.setattr(models, "listar_fotos", lambda cid: [])

    r = models.listar_pendentes_assinatura()
    assert [c["id"] for c in r] == ["passado_com_resp"]
    assert (r[0]["respondidas"], r[0]["esperadas"], r[0]["faltando"]) == (3, 8, 5)


def test_pendente_conta_foto_obrigatoria_que_falta_como_incompleto(models, monkeypatch):
    atual = turnos.Turno(1, "Manhã", date(2026, 10, 14))
    monkeypatch.setattr(models, "turno_e_data_referencia", lambda: atual)
    checklists = [{"id": "ck", "template_id": "t1", "turno_id": 2, "data": "2026-10-13", "status": "em_andamento"}]
    itens = [{"id": "pai"}, {"id": "filha", "pai_item_id": "pai", "exige_foto": True}]
    horarios = [{"id": "h1"}]
    respostas = {("pai", "h1"): {"resposta": "Sim"}, ("filha", "h1"): {"resposta": "Sim"}}   # tudo respondido
    monkeypatch.setattr(models, "supabase", _SupabaseFalso({"checklists": checklists}))
    monkeypatch.setattr(models, "listar_itens", lambda tid: itens)
    monkeypatch.setattr(models, "listar_horarios", lambda tid, turno: horarios)
    monkeypatch.setattr(models, "listar_respostas", lambda cid: respostas)
    monkeypatch.setattr(models, "listar_fotos", lambda cid: [])    # mas SEM a foto

    r = models.listar_pendentes_assinatura()[0]
    assert (r["faltando_foto"], r["faltando"]) == (1, 1)           # vai ficar marcado como incompleto


def test_checklist_anterior_usa_a_sequencia_c_a_b(models, monkeypatch):
    chamadas = []
    monkeypatch.setattr(models, "buscar_checklist_por_chave", lambda t, turno, d: chamadas.append((turno, d)))
    models.checklist_anterior("t1", 3, date(2026, 10, 14))   # C do dia 14 <- B do dia 13
    models.checklist_anterior("t1", 1, date(2026, 10, 14))   # A do dia 14 <- C do dia 14
    assert chamadas == [(2, date(2026, 10, 13)), (3, date(2026, 10, 14))]


# ----------------------------------------------------------------- fotos
def _imagem(tamanho=(4000, 3000), modo="RGB", fmt="JPEG"):
    buf = io.BytesIO()
    Image.new(modo, tamanho, (10, 120, 200) if modo == "RGB" else (10, 120, 200, 80)).save(buf, fmt)
    return buf.getvalue()


def test_comprimir_reduz_tamanho_e_resolucao(fotos):
    original = _imagem()
    saida = fotos.comprimir_imagem(original)
    img = Image.open(io.BytesIO(saida))
    assert max(img.size) <= fotos.MAX_LADO and img.format == "JPEG"
    assert len(saida) < len(original)


def test_comprimir_respeita_o_limite_de_bytes_mesmo_com_foto_cheia_de_detalhe(fotos):
    import random
    random.seed(1)
    ruido = Image.new("RGB", (3000, 2000))
    ruido.putdata([(random.randrange(256), random.randrange(256), random.randrange(256)) for _ in range(3000 * 2000)])
    buf = io.BytesIO(); ruido.save(buf, "PNG")                    # pior caso: ruído puro
    assert len(fotos.comprimir_imagem(buf.getvalue())) <= fotos.LIMITE_BYTES


def test_miniatura_e_bem_menor_que_a_foto(fotos):
    jpeg = fotos.comprimir_imagem(_imagem())
    mini = fotos.criar_miniatura(jpeg)
    assert max(Image.open(io.BytesIO(mini)).size) <= fotos.MAX_LADO_MINIATURA
    assert len(mini) < len(jpeg) / 3


def test_caminho_da_miniatura(fotos):
    assert fotos.caminho_miniatura("ck/a_b_c.jpg") == "ck/a_b_c_t.jpg"


def test_comprimir_aceita_png_com_transparencia(fotos):
    img = Image.open(io.BytesIO(fotos.comprimir_imagem(_imagem((300, 200), "RGBA", "PNG"))))
    assert img.mode == "RGB"


def test_comprimir_recusa_arquivo_que_nao_e_imagem(fotos):
    with pytest.raises(ValueError):
        fotos.comprimir_imagem(b"isto nao e uma foto")


class _Storage:
    def __init__(self): self.enviados, self.removidos = [], []
    def from_(self, bucket): self.bucket = bucket; return self
    def upload(self, caminho, conteudo, opcoes): self.enviados.append((self.bucket, caminho, len(conteudo), opcoes))
    def remove(self, caminhos): self.removidos.extend(caminhos)


def test_enviar_foto_sobe_no_bucket_e_registra_no_banco(fotos, monkeypatch):
    class _Sb:
        storage = _Storage()
        inseridos = []
        def table(self, nome):
            sb = self
            class _T:
                def insert(self, payload): sb.inseridos.append(payload); return self
                def execute(self): return _Res([sb.inseridos[-1]])
            return _T()

    sb = _Sb()
    monkeypatch.setattr(fotos, "supabase", sb)
    linha = fotos.enviar_foto("ck1", "item1", "hor1", _imagem((800, 600)), "u1")

    assert len(sb.storage.enviados) == 2                          # foto + miniatura
    bucket, caminho, tam_foto, opcoes = sb.storage.enviados[0]
    assert bucket == "checklist-fotos" and caminho.startswith("ck1/item1_hor1_") and caminho.endswith(".jpg")
    assert sb.storage.enviados[1][1] == caminho[:-4] + "_t.jpg" and sb.storage.enviados[1][2] < tam_foto
    assert opcoes["content-type"] == "image/jpeg"
    assert linha["checklist_id"] == "ck1" and linha["caminho"] == caminho and linha["enviado_por"] == "u1"


def test_agrupar_por_item(fotos):
    g = fotos.agrupar_por_item([
        {"item_id": "a", "horario_id": "1"}, {"item_id": "a", "horario_id": "1"}, {"item_id": "b", "horario_id": "1"},
    ])
    assert len(g[("a", "1")]) == 2 and len(g[("b", "1")]) == 1


def test_remover_fotos_apaga_foto_e_miniatura_do_storage_e_a_linha(fotos, monkeypatch):
    class _Sb:
        storage = _Storage()
        apagados = []
        def table(self, nome):
            sb = self
            class _T:
                def delete(self): return self
                def in_(self, col, ids): sb.apagados.append((col, ids)); return self
                def execute(self): return _Res([])
            return _T()
    sb = _Sb()
    monkeypatch.setattr(fotos, "supabase", sb)
    n = fotos.remover_fotos([{"id": "1", "caminho": "ck/a.jpg"}, {"id": "2", "caminho": "ck/b.jpg"}])
    assert n == 2
    assert sb.storage.removidos == ["ck/a.jpg", "ck/a_t.jpg", "ck/b.jpg", "ck/b_t.jpg"]
    assert sb.apagados == [("id", ["1", "2"])]
