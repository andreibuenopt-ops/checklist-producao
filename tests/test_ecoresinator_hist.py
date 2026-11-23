from datetime import date

from src.ecoresinator_hist import contar_falhas, montar_grade, resumo

NAO = {"falha_3_vias": "Não", "falha_agulha": "Não", "falha_vazao": "Não"}
REGS = [
    {"id": "a", "data": "2026-11-23", "turno_id": 3, "status": "completo", "horario_real": "22:30",
     "leituras_bicos": [{**NAO, "falha_agulha": "Sim"}, {**NAO, "falha_vazao": "Sim"}]},
    {"id": "b", "data": "2026-11-23", "turno_id": 1, "status": "pendente", "horario_real": "", "leituras_bicos": [NAO]},
    {"id": "c", "data": "2026-11-22", "turno_id": 1, "status": "completo", "horario_real": "06:10", "leituras_bicos": [NAO]},
]


def test_contar_falhas():
    assert contar_falhas(REGS[0]) == 2 and contar_falhas(REGS[2]) == 0 and contar_falhas({}) == 0


def test_grade_status_e_turno_futuro():
    # hoje = 23/11, turno em andamento = A (id 1): o turno B (tarde) ainda não começou
    g = montar_grade(REGS, date(2026, 11, 22), date(2026, 11, 23), date(2026, 11, 23), 1)
    hoje, ontem = g[0], g[1]
    assert hoje["Dia"].startswith("23/11") and ontem["Dia"].startswith("22/11")
    assert hoje["C · Noite"] == "✅ 22:30 · ⚠️ 2 falha(s)"
    assert hoje["A · Manhã"] == "🟡 em andamento"
    assert hoje["B · Tarde"] == "—"                    # ainda não chegou
    assert ontem["A · Manhã"] == "✅ 06:10"
    assert ontem["C · Noite"] == "❌ sem registro" and ontem["B · Tarde"] == "❌ sem registro"


def test_resumo():
    r = resumo(REGS, date(2026, 11, 22), date(2026, 11, 23), date(2026, 11, 23), 1)
    assert r == {"esperados": 5, "concluidos": 2, "andamento": 1, "sem_registro": 2}


def test_pagina_historico_renderiza(monkeypatch):
    from streamlit.testing.v1 import AppTest

    def app():
        from datetime import date as d
        from types import SimpleNamespace
        import src.ecoresinator_hist_ui as ui
        import src.ecoresinator_ui as eui
        regs = [{"id": "a", "data": "2026-11-23", "turno_id": 3, "status": "completo", "horario_real": "22:30",
                 "colaborador_id": "u1", "supervisor_id": "u2", "comentario": "ok", "pressao_bomba_resina": 3.5,
                 "leituras_bicos": [{"numero": 1, "vazao_lmin": 2.0, "eficiencia_pct": 90, "abertura_valvula_pct": 50,
                                     "falha_3_vias": "Não", "falha_agulha": "Sim", "falha_vazao": "Não"}]}]
        ui.turno_e_data_referencia = lambda: SimpleNamespace(data_referencia=d(2026, 11, 23), turno_id=1)
        ui.ecoresinator_historico = lambda i, f: regs
        ui.nomes_usuarios = lambda ids: {"u1": "Ana", "u2": "Beto"}
        eui.nomes_usuarios = ui.nomes_usuarios
        ui.renderizar_historico_ecoresinator()

    at = AppTest.from_function(app, default_timeout=30)
    at.run()
    assert not at.exception
    assert [m.label for m in at.metric][:4] == ["Esperados", "✅ Concluídos", "🟡 Em andamento", "❌ Sem registro"]
    assert any("falha" in o for o in at.selectbox[0].options)
    assert any(m.value == "Ana" for m in at.metric)       # registro aberto na tela, sem PDF
