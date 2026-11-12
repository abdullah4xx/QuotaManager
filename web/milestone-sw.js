// milestone PWA service worker: offline shell + fresh API data.
const CACHE = "milestone-v1";
const SHELL = [
  "/milestone", "/logo.svg",
  "/css/tokens.css",
  "/assets/pub.css", "/assets/pub-theme.js", "/assets/pub-i18n.js",
  "/assets/i18n-milestone.js",
];
["icon-192.png", "icon-512.png", "icon-maskable-512.png"].forEach((n) =>
  SHELL.push("/assets/" + n));

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE)
    .then((c) => Promise.allSettled(SHELL.map((u) => c.add(u))))
    .then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((ks) => Promise.all(ks.filter((k) => k !== CACHE)
      .map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  // data: always fresh when online; a clear offline marker when not.
  if (url.pathname === "/api/milestone") {
    e.respondWith(fetch(req).catch(() => new Response(
      JSON.stringify({ recognized: false, offline: true }),
      { headers: { "Content-Type": "application/json" } })));
    return;
  }
  // static shell: cache-first, then cache what we fetched at runtime.
  e.respondWith(caches.match(req, { ignoreSearch: true }).then((hit) => hit ||
    fetch(req).then((res) => {
      if (res.ok) {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy));
      }
      return res;
    })));
});
