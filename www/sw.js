// Only public, same-origin application files are cached; never API responses or user backups.
const PREFIX = 'vacation-plus-shell-' + self.registration.scope + '-';
const CACHE = PREFIX + 'v1';
const root = new URL(self.registration.scope);
const index = new URL('index.html', root).href;
const assets = ['manifest.webmanifest', 'assets/icon-192.png', 'assets/icon-512.png', 'assets/icon-maskable-512.png'].map(p => new URL(p, root).href);
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll([index, ...assets].map(url => new Request(url, {cache:'reload'})))));
});
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    for (const key of await caches.keys()) if (key.startsWith(PREFIX) && key !== CACHE) await caches.delete(key);
    await self.clients.claim();
  })());
});
self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== root.origin) return;
  if (req.mode === 'navigate' && (url.pathname === root.pathname || url.pathname === new URL(index).pathname)) {
    event.respondWith((async () => {
      const cache = await caches.open(CACHE);
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 4500);
      try {
        const response = await fetch(req, {cache:'no-cache', signal:ctrl.signal});
        if (response.ok && !response.redirected && (response.headers.get('content-type') || '').includes('text/html')) {
          try { await cache.put(index, response.clone()); } catch (error) { console.warn('Cache update failed', error); }
          return response;
        }
        if (response.status < 500) return response;
        return await cache.match(index) || response;
      } catch (error) {
        return await cache.match(index) || new Response('Калькулятор пока не сохранён для офлайн-работы.', {status:503,headers:{'Content-Type':'text/plain; charset=utf-8'}});
      } finally { clearTimeout(timer); }
    })());
  } else if (assets.includes(url.href)) {
    event.respondWith((async () => {
      const cache = await caches.open(CACHE);
      try {
        const response = await fetch(req, {cache:'no-cache'});
        if (response.ok && !response.redirected) { try { await cache.put(req,response.clone()); } catch {} return response; }
        return await cache.match(req) || response;
      } catch (error) { return await cache.match(req) || Response.error(); }
    })());
  }
});
