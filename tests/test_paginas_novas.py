"""Páginas novas (Histórico/pendentes e Aderência) rodando de verdade no
AppTest, com dados falsos — garante que não quebram ao renderizar."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

PASTA = Path(__file__).resolve().parent / "fixture_apps"
HIST = str(PASTA / "historico_app.py")
ADER = str(PASTA / "aderencia_app.py")


def test_historico_renderiza_e_mostra_o_checklist(monkeypatch):
    at = AppTest.from_file(HIST, default_timeout=30)
    at.run()
    assert not at.exception
    textos = " ".join(m.value for m in at.markdown)
    assert "Correia com danos?" in textos            # item do checklist aberto
    assert any("Trocar amanhã" in c.value for c in at.caption)   # o que foi relatado no "Não"


def test_pendente_assinado_incompleto_conta_como_incompleto(monkeypatch):
    at = AppTest.from_file(HIST, default_timeout=30)
    at.run()
    assert any("incompleto" in w.value.lower() for w in at.warning)   # aviso de que vai ficar incompleto

    [b for b in at.button if "Assinar e concluir" in b.label][0].click()
    at.run()
    assert not at.exception
    assert at.session_state["_assinados_debug"] == [("ck1", "u1", True)]   # faltavam 5 -> incompleto=True


def test_aderencia_supervisor_ve_indice_e_pode_exportar(monkeypatch):
    monkeypatch.setenv("TESTE_PAPEL", "supervisor")
    at = AppTest.from_file(ADER, default_timeout=30)
    at.run()
    assert not at.exception
    assert any(m.label == "Aderência geral" for m in at.metric)
    nomes_botoes = " ".join(str(getattr(e, "proto", "")) for e in at.get("download_button"))
    assert "Relatório mensal em PDF" in nomes_botoes


def test_aderencia_producao_e_bloqueada(monkeypatch):
    monkeypatch.setenv("TESTE_PAPEL", "producao")
    at = AppTest.from_file(ADER, default_timeout=30)
    at.run()
    assert not at.exception
    assert any("não permite" in e.value for e in at.error)
    assert len(at.metric) == 0


ADMIN = str(PASTA / "admin_app.py")


def test_admin_mostra_subpergunta_com_selo_de_foto_obrigatoria():
    at = AppTest.from_file(ADMIN, default_timeout=30)
    at.run()
    assert not at.exception
    textos = " ".join(m.value for m in at.markdown)
    assert "↳" in textos and "foto obrigatória" in textos and "Local da parada está limpo?" in textos


def test_admin_cadastra_subperguntas_a_partir_de_uma_pergunta():
    at = AppTest.from_file(ADMIN, default_timeout=30)
    at.run()
    [b for b in at.button if b.label == "➕ Sub"][0].click()
    at.run()
    area = [t for t in at.text_area if t.key == "txt_sub_pai"][0]
    area.set_value("Piso limpo?\nCalha sem resíduos?")
    [b for b in at.button if "Adicionar sub-perguntas" in b.label][0].click()
    at.run()
    assert not at.exception
    nome, args, kw = at.session_state["_admin_chamadas"][0]
    assert nome == "adicionar_itens" and args[1] == ["Piso limpo?", "Calha sem resíduos?"]
    assert kw["pai_item_id"] == "pai" and kw["exige_foto"] is True


def test_admin_aba_armazenamento_mostra_uso_e_apaga_fotos_antigas():
    at = AppTest.from_file(ADMIN, default_timeout=30)
    at.run()
    assert not at.exception
    assert any("76%" in str(getattr(p, "proto", "")) for p in at.get("progress"))      # banco: 380/500
    assert any("passou de 70%" in w.value for w in at.warning)

    botao = [b for b in at.button if b.label == "Apagar fotos antigas"][0]
    assert botao.disabled                                        # trava até confirmar
    [c for c in at.checkbox if "não podem ser recuperadas" in c.label][0].check()
    at.run()
    [b for b in at.button if b.label == "Apagar fotos antigas"][0].click()
    at.run()
    assert ("apagar_fotos", 90) in at.session_state["_admin_chamadas"]


def test_historico_mostra_a_turma_do_colaborador_e_filtra_por_ela():
    at = AppTest.from_file(HIST, default_timeout=30)
    at.run()
    assert not at.exception
    assert any(m.value == "Karoline Raizel (Turma A)" for m in at.metric)            # turma ao lado do nome
    rotulos = [o for sb in at.selectbox if sb.key == "hist_escolhido" for o in sb.options]
    assert rotulos and all("Karoline (Turma A)" in o for o in rotulos)                # e no rótulo da lista

    [s for s in at.selectbox if s.key == "hist_turma"][0].set_value("B")              # filtra por outra turma
    at.run()
    assert not at.exception
    assert any("Nenhum checklist nesse filtro" in i.value for i in at.info)

    [s for s in at.selectbox if s.key == "hist_turma"][0].set_value("A")
    at.run()
    assert not any("Nenhum checklist nesse filtro" in i.value for i in at.info)
