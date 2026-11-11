"""Testes do formulário de preenchimento: salvamento em lote (form batching),
bloqueio de conclusão sem confirmar, e limpeza do parâmetro ?area= da URL.
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent / "fixture_apps" / "preenchimento_app.py")


def test_clicar_sem_atualizar_nao_grava_nada(monkeypatch):
    monkeypatch.setenv("TESTE_STATUS", "em_andamento")
    at = AppTest.from_file(APP, default_timeout=20)
    at.run()

    at.segmented_control[0].set_value("Sim")
    at.run()

    assert at.session_state["_chamadas_salvar_debug"] == []


def test_atualizar_respostas_grava_em_uma_chamada_so(monkeypatch):
    monkeypatch.setenv("TESTE_STATUS", "em_andamento")
    at = AppTest.from_file(APP, default_timeout=20)
    at.run()

    at.segmented_control[0].set_value("Sim")
    at.segmented_control[1].set_value("Não")
    [b for b in at.button if "Atualizar" in b.label][0].click()
    at.run()

    chamadas = at.session_state["_chamadas_salvar_debug"]
    assert len(chamadas) == 1  # uma chamada só, não uma por item
    assert len(chamadas[0]) == 2  # com as duas respostas dentro

    estado = at.session_state["estado_preenchimento_checklist-1"]
    assert estado == {"tem_nao": True, "faltando": 0, "faltando_justificativa": 0, "faltando_fotos": 0}
    assert any("Não" in el.value and "conforme" in el.value for el in at.warning)


def test_concluir_sem_atualizar_bloqueia(monkeypatch):
    monkeypatch.setenv("TESTE_STATUS", "em_andamento")
    at = AppTest.from_file(APP, default_timeout=20)
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
    at = AppTest.from_file(APP, default_timeout=20)
    at.run()

    # Dependendo da versão do Streamlit, o valor vem como texto ou como lista.
    assert dict(at.query_params) in ({"area": ["silo-cavaco"]}, {"area": "silo-cavaco"})

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
    at = AppTest.from_file(APP, default_timeout=20)
    at.run()

    assert not at.exception
    assert "area" not in at.query_params
    assert any("já foi concluído" in el.value for el in at.success)


def test_supervisor_pode_assinar_com_outro_usuario_opcionalmente(monkeypatch):
    monkeypatch.setenv("TESTE_STATUS", "em_andamento")
    monkeypatch.setenv("TESTE_PAPEL", "supervisor")
    at = AppTest.from_file(APP, default_timeout=20)
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
        at = AppTest.from_file(APP, default_timeout=20)
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
    at = AppTest.from_file(APP, default_timeout=20)
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
    at = AppTest.from_file(APP, default_timeout=20)
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


def test_turnos_anteriores_so_buscam_quando_o_toggle_e_ligado_e_mostram_dois(monkeypatch):
    from datetime import date
    monkeypatch.setenv("TESTE_STATUS", "em_andamento")
    at = AppTest.from_file(APP, default_timeout=20)
    at.run()
    assert not any("Sem registro desse turno" in el.value for el in at.caption)
    assert "_anterior_chamadas" not in at.session_state          # nada consultado antes de ligar

    at.toggle[0].set_value(True)
    at.run()
    assert not at.exception
    assert sum("Sem registro desse turno" in el.value for el in at.caption) == 2     # 2 turnos mostrados
    # fixture: turno atual = A (Manhã) de 31/08. Anterior = C (31/08); o antes dele = B de 30/08.
    chamadas = at.session_state["_anterior_chamadas"]
    assert [(c[1], c[2]) for c in chamadas] == [(1, date(2026, 8, 31)), (3, date(2026, 8, 31))]
    titulos = " ".join(m.value for m in at.markdown)
    assert "Turno C Noite" in titulos and "Turno B Tarde" in titulos


# ----------------------------------------------------------------- parada (pai Sim -> filhas com foto)
def _marcar(at, **respostas):
    """Define as respostas pelas perguntas na ordem em que aparecem."""
    for i, valor in respostas.items():
        at.segmented_control[int(i.lstrip("p"))].set_value(valor)


def _atualizar(at):
    [b for b in at.button if "Atualizar" in b.label][0].click()
    at.run()


def test_subperguntas_da_parada_so_abrem_com_sim(monkeypatch):
    monkeypatch.setenv("TESTE_STATUS", "em_andamento")
    monkeypatch.setenv("TESTE_GATE", "1")
    at = AppTest.from_file(APP, default_timeout=20)
    at.run()
    assert len(at.segmented_control) == 3                      # 2 perguntas + o pai (filha escondida)
    assert any("abrir as perguntas desta parada" in c.value for c in at.caption)

    _marcar(at, p0="Sim", p1="Sim", p2="Sim")
    _atualizar(at)                                             # salva e redesenha
    assert not at.exception
    assert len(at.segmented_control) == 4                      # a filha apareceu
    assert any("foto do local é obrigatória" in c.value for c in at.caption)


def test_filha_exige_foto_pra_concluir(monkeypatch):
    monkeypatch.setenv("TESTE_STATUS", "em_andamento")
    monkeypatch.setenv("TESTE_GATE", "1")
    at = AppTest.from_file(APP, default_timeout=20)
    at.run()
    _marcar(at, p0="Sim", p1="Sim", p2="Sim")
    _atualizar(at)

    at.segmented_control[3].set_value("Sim")                   # responde a filha, sem foto
    _atualizar(at)
    assert at.session_state["estado_preenchimento_checklist-1"]["faltando_fotos"] == 1
    [b for b in at.button if "Concluir checklist" in b.label][0].click()
    at.run()
    assert any("fotos obrigatórias" in e.value for e in at.error)
    assert "area" in at.query_params                           # NÃO concluiu

    # com foto salva, conclui
    at.session_state["_db_fotos"] = [
        {"id": "f1", "item_id": "filho", "horario_id": "horario-1", "caminho": "ck/filho.jpg"}]
    _atualizar(at)
    assert at.session_state["estado_preenchimento_checklist-1"]["faltando_fotos"] == 0
    [b for b in at.button if "Concluir checklist" in b.label][0].click()
    at.run()
    assert not at.exception
    assert "area" not in at.query_params


def test_pai_que_volta_pra_nao_apaga_as_respostas_das_filhas(monkeypatch):
    monkeypatch.setenv("TESTE_STATUS", "em_andamento")
    monkeypatch.setenv("TESTE_GATE", "1")
    at = AppTest.from_file(APP, default_timeout=20)
    at.run()
    _marcar(at, p0="Sim", p1="Sim", p2="Sim")
    _atualizar(at)
    at.segmented_control[3].set_value("Sim")
    _atualizar(at)
    assert ("filho", "horario-1") in at.session_state["_db_respostas"]

    at.segmented_control[2].set_value("Não")                   # parada foi desmarcada
    _atualizar(at)
    assert not at.exception
    assert ("filho", "horario-1") not in at.session_state["_db_respostas"]
    assert len(at.segmented_control) == 3                      # filha sumiu da tela
