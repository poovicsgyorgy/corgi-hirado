const CACHE = "corgi-hirado-v3";
const SHELL = ["./", "index.html", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
// Hálózat először (hogy mindig friss legyen), offline esetén a tárolt változat
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  e.respondWith(
    fetch(e.request).then(res => {
      const copy = res.clone();
      const key = url.origin + url.pathname;
      caches.open(CACHE).then(c => c.put(key, copy));
      return res;
    }).catch(() => caches.match(url.origin + url.pathname).then(r => r || caches.match("index.html")))
  );
});
