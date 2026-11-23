"""Rascunho no NAVEGADOR (localStorage) das respostas ainda não salvas.

Problema: as perguntas ficam num st.form — nada vai pro servidor até apertar
"Atualizar respostas". Se a rede cai ou o navegador recarrega a página (celular
que "dorme", troca de app), a sessão do servidor some e o que foi marcado se perde.

Solução: um script (injetado no documento da página) guarda a cada clique/
digitação o que está marcado, no localStorage do aparelho, e — ao reabrir — marca
de novo SÓ o que ainda não está salvo no banco. Depois de "Atualizar respostas"
(ou de concluir) o rascunho é apagado.

Não depende de rede e não grava nada no Supabase. Se o JS falhar, o app segue
funcionando normal (é só uma rede de segurança).
"""
import json

import streamlit as st
import streamlit.components.v1 as components

_JS = r"""
(function () {
  const CK = __CK__;                // id do checklist
  const SALVAS = new Set(__SALVAS__);  // chaves de widgets já gravadas no banco
  const LIMPAR = __LIMPAR__;
  const P = window.parent, D = P.document;
  const LS = 'ckdraft_' + CK, MAXH = 14 * 3600 * 1000;
  const lerLS = () => { try { const o = JSON.parse(P.localStorage.getItem(LS) || 'null');
      return (o && Date.now() - o.t < MAXH) ? o.v : {}; } catch (e) { return {}; } };
  const gravarLS = (v) => { try { P.localStorage.setItem(LS, JSON.stringify({t: Date.now(), v: v})); } catch (e) {} };

  if (LIMPAR) { try { P.localStorage.removeItem(LS); } catch (e) {} P['__ckdraft_' + CK] = 'limpo'; return; }

  const grupo = (el) => el.closest('[class*="st-key-resp_' + CK + '"], [class*="st-key-obs_' + CK + '"]');
  const chaveDe = (box) => { const m = (box.className || '').match(/st-key-((?:resp|obs)_[^\s]+)/); return m ? m[1] : null; };

  // 1) CAPTURA (uma vez por carregamento de página)
  if (!P['__ckdraft_cap_' + CK]) {
    P['__ckdraft_cap_' + CK] = true;
    const salvar = (box) => {
      const k = chaveDe(box); if (!k) return;
      const v = lerLS();
      if (k.startsWith('resp_')) {
        const bs = Array.from(box.querySelectorAll('button[role="radio"]'));
        const i = bs.findIndex(b => b.getAttribute('aria-checked') === 'true');
        if (i >= 0) v[k] = i; else delete v[k];
      } else {
        const ta = box.querySelector('textarea');
        if (ta) { if (ta.value) v[k] = ta.value; else delete v[k]; }
      }
      gravarLS(v);
    };
    D.addEventListener('click', (e) => { const b = grupo(e.target); if (b && chaveDe(b).startsWith('resp_')) setTimeout(() => salvar(b), 150); }, true);
    D.addEventListener('input', (e) => { const b = grupo(e.target); if (b && chaveDe(b).startsWith('obs_')) salvar(b); }, true);
  }

  // 2) RESTAURA (uma vez por carregamento): só o que NÃO está salvo no banco
  if (!P['__ckdraft_rest_' + CK]) {
    P['__ckdraft_rest_' + CK] = true;
    const v = lerLS(); const chaves = Object.keys(v);
    if (!chaves.length) return;
    let tent = 0;
    const timer = setInterval(() => {
      tent++;
      let faltam = 0, feitos = 0;
      chaves.forEach(k => {
        if (SALVAS.has(k) || v[k] === undefined) return;
        const box = D.querySelector('.st-key-' + k);
        if (!box) { faltam++; return; }
        if (k.startsWith('resp_')) {
          const bs = box.querySelectorAll('button[role="radio"]');
          if (!bs.length) { faltam++; return; }
          if (!bs[v[k]]) return;
          if (bs[v[k]].getAttribute('aria-checked') !== 'true') bs[v[k]].click();
        } else {
          const ta = box.querySelector('textarea');
          if (!ta) { faltam++; return; }
          if (!ta.value) {
            const set = Object.getOwnPropertyDescriptor(P.HTMLTextAreaElement.prototype, 'value').set;
            set.call(ta, v[k]);
            ta.dispatchEvent(new P.Event('input', {bubbles: true}));
            ta.dispatchEvent(new P.Event('blur', {bubbles: true}));
          }
        }
        feitos++;
      });
      if (!faltam || tent > 40) clearInterval(timer);
    }, 500);
  }
})();
"""


def rascunho_local(checklist_id: str, chaves_salvas: set, limpar: bool = False):
    """Injeta o script do rascunho. `chaves_salvas` = chaves de widgets
    (resp_…/obs_…) que já têm valor no banco — o rascunho nunca as sobrescreve."""
    js = (
        _JS.replace("__CK__", json.dumps(str(checklist_id)))
        .replace("__SALVAS__", json.dumps(sorted(chaves_salvas)))
        .replace("__LIMPAR__", "true" if limpar else "false")
    )
    html = f"<script>{js}</script>"
    try:                       # Streamlit novo: st.iframe (components.html foi descontinuado)
        st.iframe(html, height=1)
    except Exception:          # versões antigas
        components.html(html, height=0)
