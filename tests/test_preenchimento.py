"""Testes do formulário de preenchimento: salvamento em lote (form batching),
bloqueio de conclusão sem confirmar, e limpeza do parâmetro ?area= da URL.
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent / "fixture_apps" / "preenchimento_app.py")


def test_clicar_sem_atualizar_nao_grava_nada(monkeypatch):
    monkeypatch.setenv("TESTE_STATUS", "em_andamento")
    at = AppTest.from_file(APP)
    at.run()

    at.segmented_control[0].set_value("Sim")
    at.run()

    assert at.session_state["_chamadas_salvar_debug"] == []


def test_atualizar_respostas_grava_em_uma_chamada_so(monkeypatch):
    monkeypatch.setenv("TESTE_STATUS", "em_andamento")
    at = AppTest.from_file(APP)
    at.run()

    at.segmented_control[0].set_value("Sim")
    at.segmented_control[1].set_value("Não")
    [b for b in at.button if "Atualizar" in b.label][0].click()
    at.run()

    chamadas = at.session_state["_chamadas_salvar_debug"]
    assert len(chamadas) == 1  # uma chamada só, não uma por item
    assert len(chamadas[0]) == 2  # com as duas respostas dentro

    estado = at.session_state["estado_preenchimento_checklist-1"]
    assert estado == {"tem_nao": True, "faltando": 0, "faltando_justificativa": 0}
    assert any("Não" in el.value and "conforme" in el.value for el in at.warning)


def test_concluir_sem_atualizar_bloqueia(monkeypatch):
    monkeypatch.setenv("TESTE_STATUS", "em_andamento")
    at = AppTest.from_file(APP)
    at.run()

    at.segmented_control[0].set_value("Sim")
    # Não aperta "Atualizar respostas" — vai direto pro Concluir.
    [b for b in at.button if "Concluir" in b.label][0].click()
    at.run()

    assert not at.exception
    assert at.session_state["_chamadas_salvar_debug"] == []
    assert any("faltam" in el.value for el in at.error)


def test_area_some_da_url_ao_concluir(monkeypatch):
    monkeypatch.setenv("TESTE_STATUS", "em_andamento")
    at = AppTest.from_file(APP)
    at.run()

    assert dict(at.query_params) == {"area": ["silo-cavaco"]}

    at.segmented_control[0].set_value("Sim")
    at.segmented_control[1].set_value("Não")
    [b for b in at.button if "Atualizar" in b.label][0].click()
    at.run()

    # Uma das respostas é "Não" — comentário é opcional, preenche mesmo assim.
    at.text_area[0].set_value("Situação resolvida no local.")

    # usuario_fake é "producao" — conclui sozinho, sem login separado.
    [b for b in at.button if "Concluir" in b.label][0].click()
    at.run()

    assert not at.exception
    assert "area" not in at.query_params


def test_area_some_da_url_ao_abrir_ja_completo(monkeypatch):
    monkeypatch.setenv("TESTE_STATUS", "completo")
    at = AppTest.from_file(APP)
    at.run()

    assert not at.exception
    assert "area" not in at.query_params
    assert any("já foi concluído" in el.value for el in at.success)


def test_supervisor_pode_assinar_com_outro_usuario_opcionalmente(monkeypatch):
    monkeypatch.setenv("TESTE_STATUS", "em_andamento")
    monkeypatch.setenv("TESTE_PAPEL", "supervisor")
    at = AppTest.from_file(APP)
    at.run()

    at.segmented_control[0].set_value("Sim")
    at.segmented_control[1].set_value("Sim")
    [b for b in at.button if "Atualizar" in b.label][0].click()
    at.run()

    # Assinatura por outro usuário continua disponível (expander opcional).
    inputs = at.text_input
    inputs[0].set_value("supervisor@teste.com")
    inputs[1].set_value("senha123")
    [b for b in at.button if "outro usuário" in b.label][0].click()
    at.run()

    assert not at.exception
    assert "area" not in at.query_params


def test_qualquer_papel_conclui_sozinho_com_um_clique(monkeypatch):
    """Operador (e qualquer outro papel) conclui com a própria sessão,
    sem precisar digitar login/senha de ninguém."""
    for papel in ("producao", "supervisor", "master"):
        monkeypatch.setenv("TESTE_STATUS", "em_andamento")
        monkeypatch.setenv("TESTE_PAPEL", papel)
        at = AppTest.from_file(APP)
        at.run()

        at.segmented_control[0].set_value("Sim")
        at.segmented_control[1].set_value("Sim")
        [b for b in at.button if "Atualizar" in b.label][0].click()
        at.run()

        # Sem preencher nenhum campo de login/senha.
        [b for b in at.button if "Concluir checklist" in b.label][0].click()
        at.run()

        assert not at.exception, papel
        assert "area" not in at.query_params, papel


def test_ronda_atrasada_nao_bloqueia_conclusao_sem_justificativa(monkeypatch):
    """Justificativa de atraso é só um campo opcional (expander) — não
    trava a conclusão, nem quando fica em branco."""
    monkeypatch.setenv("TESTE_STATUS", "em_andamento")
    monkeypatch.setenv("TESTE_ATRASADO", "1")
    at = AppTest.from_file(APP)
    at.run()

    assert any("passou de 1h" in el.value.lower() for el in at.caption)

    at.segmented_control[0].set_value("Sim")
    at.segmented_control[1].set_value("Sim")
    # Não preenche a justificativa do atraso — conclui direto mesmo assim.
    [b for b in at.button if "Atualizar" in b.label][0].click()
    at.run()
    [b for b in at.button if "Concluir" in b.label][0].click()
    at.run()

    assert not at.exception
    assert at.session_state["_justificativas_salvas_debug"] == []
    assert "area" not in at.query_params


def test_ronda_atrasada_com_justificativa_tambem_permite_concluir(monkeypatch):
    monkeypatch.setenv("TESTE_STATUS", "em_andamento")
    monkeypatch.setenv("TESTE_ATRASADO", "1")
    at = AppTest.from_file(APP)
    at.run()

    at.segmented_control[0].set_value("Sim")
    at.segmented_control[1].set_value("Sim")
    at.text_area[0].set_value("Rota bloqueada por manutenção corretiva na linha.")
    [b for b in at.button if "Atualizar" in b.label][0].click()
    at.run()

    assert at.session_state["_justificativas_salvas_debug"] != []

    [b for b in at.button if "Concluir" in b.label][0].click()
    at.run()

    assert not at.exception
    assert "area" not in at.query_params
