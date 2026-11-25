"""Teste ponta a ponta no NAVEGADOR REAL (Chromium) do modo offline.

Sobe o Streamlit com banco falso, prepara o aparelho, fica SEM internet,
preenche (com foto), volta a internet e confere o que chegou ao banco.
Lento (~30 s): só roda com  E2E=1 pytest tests/test_offline_e2e.py
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(os.environ.get("E2E") != "1", reason="teste de navegador: rode com E2E=1")
ROOT = Path(__file__).resolve().parent.parent


def _porta():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture()
def servidor(tmp_path):
    from PIL import Image
    app = ROOT / "tests" / "e2e_apps"
    segredos = ROOT / ".streamlit" / "secrets.toml"
    tinha = segredos.exists()
    if not tinha:
        segredos.write_text('SUPABASE_URL="https://fake.supabase.co"\nSUPABASE_KEY="fake"\nAPP_BASE_URL="http://x"\n')
    log = tmp_path / "banco.jsonl"
    log.write_text("")
    porta = _porta()
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(app / "offline_app.py"), "--server.port", str(porta),
         "--server.headless", "true", "--server.enableStaticServing", "false",
          "--browser.gatherUsageStats", "false"],
        cwd=ROOT, env={**os.environ, "E2E_LOG": str(log)}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    url = f"http://127.0.0.1:{porta}"
    for _ in range(60):
        try:
            urllib.request.urlopen(url + "/_stcore/health", timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    foto = tmp_path / "foto.jpg"
    Image.new("RGB", (2400, 1800), (200, 30, 30)).save(foto, quality=95)
    yield {"url": url, "log": log, "foto": foto, "proc": proc}
    proc.terminate()
    if not tinha:
        segredos.unlink(missing_ok=True)


def test_preparar_preencher_sem_internet_e_enviar(servidor):
    from playwright.sync_api import expect, sync_playwright

    url = servidor["url"]
    with sync_playwright() as p:
        nav = p.chromium.launch()
        ctx = nav.new_context(viewport={"width": 420, "height": 900}, service_workers="allow")
        pg = ctx.new_page()
        erros = []
        pg.on("pageerror", lambda e: erros.append(str(e)))

        # 1) com internet: prepara o aparelho
        pg.goto(url + "/")
        expect(pg.get_by_text("Nada aguardando envio")).to_be_visible(timeout=30000)
        pg.get_by_role("button", name="📥 Preparar este aparelho").click()
        expect(pg.get_by_text("Aparelho preparado: 1 checklist(s)")).to_be_visible(timeout=30000)
        assert "⚠️ o navegador não liberou" not in pg.content()

        # 2) sem internet: a tela offline abre pelo service worker
        ctx.set_offline(True)
        pg.goto(url + "/component/src.offline_ui.ck_offline/offline.html")
        expect(pg.get_by_text("Sem internet")).to_be_visible(timeout=15000)
        pg.get_by_role("button", name="Área das Serras").click()
        expect(pg.get_by_text("Houve parada?")).to_be_visible()

        # 3) preenche: Sim abre a sub-pergunta com foto obrigatória
        ronda = pg.locator("section.ronda").first
        ronda.locator(".card", has_text="Houve parada?").get_by_role("button", name="✅ Sim").click()
        sub = ronda.locator(".filhas .card", has_text="Qual o local?")
        expect(sub).to_be_visible()
        expect(sub.get_by_text("obrigatória")).to_be_visible()
        sub.get_by_role("button", name="✅ Sim").click()
        sub.locator("input[type=file]").set_input_files(str(servidor["foto"]))
        expect(sub.get_by_text("Foto do local ✅")).to_be_visible(timeout=15000)
        card = ronda.locator(".card", has_text="Vazamento de óleo?")
        card.get_by_role("button", name="❌ Não").click()
        card.locator("textarea").fill("Mangueira da prensa pingando")
        ronda.locator(".card", has_text="Comentário").locator("textarea").fill("Tudo certo no resto")
        expect(pg.get_by_text("Salvo neste aparelho")).to_be_visible(timeout=5000)
        expect(pg.locator("#rodape-txt")).to_contain_text("1 checklist(s) e 1 foto(s)")

        # 4) recarrega ainda sem internet: nada se perde
        pg.reload()
        pg.get_by_role("button", name="Área das Serras").click()
        expect(pg.get_by_text("Houve parada?")).to_be_visible()
        expect(pg.locator("section.ronda .resp button.sel")).to_have_count(3)    # Sim, Sim, Não
        expect(pg.locator("section.ronda .fotos img")).to_have_count(1)

        # 5) volta a internet: abre o app e o envio é automático
        ctx.set_offline(False)
        pg.goto(url + "/")
        expect(pg.get_by_text("Nada aguardando envio")).to_be_visible(timeout=40000)     # só aparece DEPOIS de enviar tudo
        assert "Verificando" not in pg.inner_text("body")
        assert not erros, erros
        nav.close()

    linhas = [json.loads(x) for x in servidor["log"].read_text().splitlines() if x.strip()]
    ups = [r for l in linhas if l["tipo"] == "upsert" for r in l["rows"]]
    por_item = {(r["item_id"], r["horario_id"]): r for r in ups}
    assert {k[0] for k in por_item} == {"i1", "f1", "i2", "t1"}
    i2 = next(r for r in ups if r["item_id"] == "i2")
    assert (i2["resposta"], i2["observacao"], i2["respondido_por"]) == ("Não", "Mangueira da prensa pingando", "u1")
    assert next(r for r in ups if r["item_id"] == "t1")["resposta"] == "Texto"
    fotos = [l for l in linhas if l["tipo"] == "foto"]
    assert len(fotos) == 1 and 1000 < fotos[0]["bytes"] < 200_000 and fotos[0]["item"] == "f1"
