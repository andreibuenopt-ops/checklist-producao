// Service worker do modo offline: guarda a tela offline para abrir sem internet.
const CACHE = 'ckoff-v2';
const ARQUIVOS = ['offline.html', 'offline-db.js', 'manifest.json', 'offline-icon.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ARQUIVOS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
// Abre do cache na hora e atualiza em segundo plano quando há internet.
self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  e.respondWith(caches.open(CACHE).then(async (c) => {
    const guardado = await c.match(req, { ignoreSearch: true });
    const rede = fetch(req).then(r => { if (r && r.ok) c.put(req, r.clone()); return r; }).catch(() => null);
    return guardado || (await rede) || (req.mode === 'navigate' ? c.match('offline.html') : Response.error());
  }));
});
