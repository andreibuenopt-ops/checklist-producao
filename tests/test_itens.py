from src.itens import (
    contar_esperadas, faltando_fotos, faltando_respostas, ids_filhos_inativos, itens_da_ronda, separar_itens,
)

PAI = {"id": "p", "pergunta": "Houve parada programada?"}
F1 = {"id": "f1", "pai_item_id": "p", "exige_foto": True}
F2 = {"id": "f2", "pai_item_id": "p", "exige_foto": True}
OUTRA = {"id": "o", "pergunta": "Outra pergunta"}
ITENS = [PAI, F1, F2, OUTRA]
HORARIOS = [{"id": "h1"}]


def _r(**kw):
    return {(k, "h1"): {"resposta": v} for k, v in kw.items()}


def test_separar_itens():
    topo, filhos = separar_itens(ITENS)
    assert [i["id"] for i in topo] == ["p", "o"]
    assert [i["id"] for i in filhos["p"]] == ["f1", "f2"]


def test_filhas_so_aparecem_quando_o_pai_e_sim():
    ids = lambda r: [i["id"] for i, _ in itens_da_ronda(ITENS, r, "h1")]
    assert ids({}) == ["p", "o"]
    assert ids(_r(p="Não")) == ["p", "o"]
    assert ids(_r(p="Sim")) == ["p", "f1", "f2", "o"]      # filhas logo depois do pai
    assert [eh for _, eh in itens_da_ronda(ITENS, _r(p="Sim"), "h1")] == [False, True, True, False]


def test_valor_atual_da_tela_tem_prioridade_sobre_o_salvo():
    salvo_nao = _r(p="Não")
    ids = [i["id"] for i, _ in itens_da_ronda(ITENS, salvo_nao, "h1", resposta_de=lambda _id: "Sim")]
    assert "f1" in ids


def test_contagem_de_esperadas_e_faltando():
    assert contar_esperadas(ITENS, {}, HORARIOS) == 2
    r = _r(p="Sim", o="Sim")
    assert contar_esperadas(ITENS, r, HORARIOS) == 4
    assert faltando_respostas(ITENS, r, HORARIOS) == 2      # f1 e f2 ainda sem resposta
    assert faltando_respostas(ITENS, {**r, **_r(f1="Sim", f2="Não")}, HORARIOS) == 0


def test_foto_obrigatoria_so_conta_filha_respondida_e_ativa():
    r = _r(p="Sim", o="Sim", f1="Sim")           # f1 respondida, f2 não
    assert faltando_fotos(ITENS, r, {}, HORARIOS) == 1        # só f1 (f2 ainda nem respondida)
    assert faltando_fotos(ITENS, r, {("f1", "h1"): [{}]}, HORARIOS) == 0
    assert faltando_fotos(ITENS, r, {}, HORARIOS, recem_enviadas={("f1", "h1")}) == 0
    # pai virou "Não": filha some e não exige mais nada
    assert faltando_fotos(ITENS, _r(p="Não", f1="Sim"), {}, HORARIOS) == 0


def test_filhas_orfas_quando_o_pai_muda_de_sim_pra_nao():
    r = _r(p="Sim", f1="Sim", f2="Não")
    assert ids_filhos_inativos(ITENS, r, "h1", resposta_de=lambda _id: "Não") == ["f1", "f2"]
    assert ids_filhos_inativos(ITENS, r, "h1") == []          # ainda Sim: nada a limpar
