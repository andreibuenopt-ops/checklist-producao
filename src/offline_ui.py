"""Ponte entre a página "Modo offline" e o armazenamento do celular.

Um componente (Streamlit Components v2, roda direto na página, sem iframe) lê o
IndexedDB do aparelho — o mesmo que offline_pwa/offline.html grava — e:
  - guarda o PACOTE (checklists/rondas) quando o usuário toca em "Preparar";
  - registra o service worker (deixa a tela offline abrir sem internet);
  - envia, um por vez, as rondas e fotos preenchidas sem sinal. O Python grava
    no banco e devolve o resultado; só então o celular apaga/marca como enviado.
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# A tela offline (HTML/JS/service worker) é servida como arquivos de um COMPONENTE do Streamlit:
# funciona em qualquer versão/hospedagem, ao contrário de /app/static (que o Streamlit Cloud não serve).
_PWA = components.declare_component("ck_offline", path=str(Path(__file__).resolve().parent.parent / "offline_pwa"))
BASE_PWA = f"/component/{_PWA.name}"

_JS = r"""
export default function (component) {
  const { data, setTriggerValue, setStateValue } = component;
  const G = (window.__ckoff = window.__ckoff || { tentados: new Set(), n: 0, aguardando: null, resumo: '', pacote: null, res: null });
  (async () => {
    let DB;
    try { DB = await import(location.origin + data.base + '/offline-db.js'); }
    catch (e) { setStateValue('erro', 'Não consegui abrir o armazenamento do aparelho: ' + e); return; }

    if (data.pacote && G.pacote !== data.pacote.gerado) {
      G.pacote = data.pacote.gerado;
      await DB.guardarPacote({ ...data.pacote, link: location.href });
      let sw = false; try { sw = await DB.registrarSW(data.base); } catch (e) {}
      setStateValue('preparo', { sw, id: data.pacote.gerado, checklists: data.pacote.checklists.length });
    }
    if (data.resultado && G.res !== data.resultado.n) {
      G.res = data.resultado.n; G.aguardando = null;
      await DB.aplicarResultado(data.resultado);
    }
    const r = await DB.resumo();
    const txt = JSON.stringify(r);
    if (txt !== G.resumo) { G.resumo = txt; setStateValue('resumo', r); }

    if (data.enviar && G.aguardando === null) {
      const prox = await DB.proximo(G.tentados);
      G.n += 1; G.aguardando = G.n;
      if (prox) { G.tentados.add(prox.ref); setTriggerValue('item', { n: G.n, ...prox }); }
      else { G.aguardando = null; G.tentados.clear(); setTriggerValue('fim', { n: G.n }); }
    }
  })();
}
"""

_componente = st.components.v2.component("ck_offline_sync", js=_JS)


def sincronizador(pacote=None, enviar=False, resultado=None):
    """Monta o componente. Devolve o resultado do Streamlit (.item, .fim,
    .resumo, .preparo, .erro)."""
    nada = lambda: None
    return _componente(
        key="ck_off_sync",
        data={"base": BASE_PWA, "pacote": pacote, "enviar": enviar, "resultado": resultado},
        on_item_change=nada, on_fim_change=nada, on_resumo_change=nada,
        on_preparo_change=nada, on_erro_change=nada,
    )
