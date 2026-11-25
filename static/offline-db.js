// Armazenamento local (IndexedDB) do modo offline — usado pela tela offline
// (offline.html) e pelo componente da página "Modo offline" do app, que
// enviam o que foi preenchido sem internet. Mesma origem => mesmo banco.
const NOME = 'ckoff', VERSAO = 1;
let _db = null;

export function abrir() {
  if (_db) return _db;
  _db = new Promise((res, rej) => {
    const r = indexedDB.open(NOME, VERSAO);
    r.onupgradeneeded = () => {
      const d = r.result;
      d.createObjectStore('rondas', { keyPath: 'key' });
      d.createObjectStore('fotos', { keyPath: 'id' });
      d.createObjectStore('meta', { keyPath: 'k' });
    };
    r.onsuccess = () => res(r.result);
    r.onerror = () => { _db = null; rej(r.error); };
  });
  return _db;
}

async function op(store, modo, fn) {
  const d = await abrir();
  return new Promise((res, rej) => {
    const t = d.transaction(store, modo);
    const req = fn(t.objectStore(store));
    t.oncomplete = () => res(req ? req.result : undefined);
    t.onerror = () => rej(t.error);
    t.onabort = () => rej(t.error);
  });
}
const pegar = (s, k) => op(s, 'readonly', st => st.get(k));
const gravar = (s, v) => op(s, 'readwrite', st => st.put(v));
const apagar = (s, k) => op(s, 'readwrite', st => st.delete(k));
const todos = (s) => op(s, 'readonly', st => st.getAll());

// ---- pacote (checklists/perguntas/rondas baixados com internet) ----
export const guardarPacote = (p) => gravar('meta', { k: 'pacote', v: p });
export const lerPacote = async () => (await pegar('meta', 'pacote'))?.v || null;

// ---- rondas preenchidas ----
export const chaveRonda = (tpl, turno, ref) => `${tpl}|${turno}|${ref}`;
export const lerRonda = (key) => pegar('rondas', key);
export const todasRondas = () => todos('rondas');
export async function salvarRonda(rec) {
  rec.v = (rec.v || 0) + 1; rec.sujo = true; rec.t = Date.now(); rec.erro = null;
  await gravar('rondas', rec);
  return rec;
}
export const descartarRonda = async (key) => {
  for (const f of await fotosDaRonda(key)) await apagar('fotos', f.id);
  await apagar('rondas', key);
};

// ---- fotos (arquivo fica no aparelho até enviar) ----
export const addFoto = (f) => gravar('fotos', f);
export const delFoto = (id) => apagar('fotos', id);
export const todasFotos = () => todos('fotos');
export const fotosDaRonda = async (key) => (await todasFotos()).filter(f => f.key === key);

// ---- o que falta enviar ----
const temConteudo = (r) => Object.keys(r.respostas || {}).length || Object.values(r.justificativas || {}).some(Boolean);
export async function resumo() {
  const rondas = (await todasRondas()).filter(r => r.sujo && temConteudo(r));
  const fotos = await todasFotos();
  return {
    rondas: rondas.length, fotos: fotos.length,
    erros: rondas.filter(r => r.erro).length + fotos.filter(f => f.erro).length,
    usuarios: [...new Set(rondas.map(r => r.user_id))],
  };
}

const paraBase64 = (blob) => new Promise((res, rej) => {
  const fr = new FileReader();
  fr.onload = () => res(String(fr.result).split(',')[1] || '');
  fr.onerror = () => rej(fr.error);
  fr.readAsDataURL(blob);
});

// Próximo item a enviar (ronda primeiro, depois fotos). `tentados` evita
// ficar repetindo um item que o servidor recusou nesta sessão.
export async function proximo(tentados) {
  const rondas = await todasRondas();
  for (const r of rondas) {
    if (!r.sujo || !temConteudo(r) || tentados.has('r:' + r.key)) continue;
    return { tipo: 'ronda', ref: 'r:' + r.key, key: r.key, v: r.v, template_id: r.template_id,
             turno_id: r.turno_id, data_ref: r.data_ref, user_id: r.user_id,
             respostas: r.respostas || {}, justificativas: r.justificativas || {} };
  }
  for (const f of await todasFotos()) {
    if (tentados.has('f:' + f.id)) continue;
    const r = rondas.find(x => x.key === f.key);
    if (!r) { await apagar('fotos', f.id); continue; }
    return { tipo: 'foto', ref: 'f:' + f.id, id: f.id, key: f.key, template_id: r.template_id,
             turno_id: r.turno_id, data_ref: r.data_ref, user_id: r.user_id,
             item_id: f.item_id, horario_id: f.horario_id, b64: await paraBase64(f.blob) };
  }
  return null;
}

// Resposta do servidor para um item enviado.
export async function aplicarResultado(res) {
  if (!res || !res.tipo) return;
  if (res.tipo === 'ronda') {
    const r = await lerRonda(res.key); if (!r) return;
    if (res.estado === 'ok') { if (r.v === res.v) { r.sujo = false; r.erro = null; r.enviado_t = Date.now(); } }
    else r.erro = res.msg || 'Não foi possível enviar.';
    await gravar('rondas', r);
  } else {
    const f = await pegar('fotos', res.id);
    const r = await lerRonda(res.key);
    if (res.estado === 'ok') {
      await apagar('fotos', res.id);
      if (r && f) { const k = `${f.item_id}|${f.horario_id}`; r.fotos_env = r.fotos_env || {}; r.fotos_env[k] = (r.fotos_env[k] || 0) + 1; await gravar('rondas', r); }
    } else if (f) { f.erro = res.msg || 'Não foi possível enviar.'; await gravar('fotos', f); }
  }
}

// Apaga o que já foi enviado há mais de 3 dias.
export async function limparAntigos() {
  const lim = Date.now() - 3 * 86400e3;
  for (const r of await todasRondas()) if (!r.sujo && (r.enviado_t || r.t) < lim) await descartarRonda(r.key);
}

// ---- service worker (deixa a tela abrir sem internet) ----
export async function registrarSW(base) {
  if (!('serviceWorker' in navigator)) return false;
  const reg = await navigator.serviceWorker.register(`${base}/offline-sw.js`, { scope: `${base}/` });
  const w = reg.active || reg.waiting || reg.installing;
  if (!w) return false;
  if (w.state === 'activated') return true;
  return new Promise((res) => {
    const fim = () => { if (w.state === 'activated') res(true); else if (w.state === 'redundant') res(false); };
    w.addEventListener('statechange', fim); setTimeout(() => res(w.state === 'activated'), 15000);
  });
}
