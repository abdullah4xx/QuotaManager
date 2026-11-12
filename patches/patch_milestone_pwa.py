#!/usr/bin/env python3
"""milestone PWA: make the user's milestone page installable in Chrome as an
app (PWA) — installable app window, own icon, offline shell.

Writes:
  web/milestone.webmanifest   - app identity: name/icon/start_url/standalone
  web/milestone-sw.js         - offline shell (static cache) + fresh API data
Edits:
  web/milestone.html          - <link rel="manifest"> + icons + SW registration

PNG icons (icon-192.png / icon-512.png / icon-maskable-512.png /
apple-touch-icon.png) are rendered from web/logo.svg and uploaded into
web/assets/ separately — this script references them if present and falls
back to the SVG icon otherwise.

Idempotent: running twice changes nothing the second time.
Usage: python3 patch_milestone_pwa.py /opt/QuotaManager
"""
import json
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else "/opt/QuotaManager")
web = root / "web"
assets = web / "assets"

# --- 1) milestone.webmanifest -------------------------------------------------
manifest_path = web / "milestone.webmanifest"
icons = []
if (assets / "icon-192.png").exists():
    icons.append({"src": "/assets/icon-192.png", "sizes": "192x192",
                  "type": "image/png", "purpose": "any"})
if (assets / "icon-512.png").exists():
    icons.append({"src": "/assets/icon-512.png", "sizes": "512x512",
                  "type": "image/png", "purpose": "any"})
if (assets / "icon-maskable-512.png").exists():
    icons.append({"src": "/assets/icon-maskable-512.png", "sizes": "512x512",
                  "type": "image/png", "purpose": "maskable"})
icons.append({"src": "/logo.svg", "sizes": "any", "type": "image/svg+xml",
              "purpose": "any"})
manifest = {
    "name": "QuotaManager — صفحتي",
    "short_name": "صفحتي",
    "description": "نصيبي من باقة الشبكة وتقسيمي اليومي، من غير تسجيل دخول.",
    "lang": "ar",
    "start_url": "/milestone",
    "scope": "/",
    "display": "standalone",
    "theme_color": "#5B8CFF",
    "background_color": "#101322",
    "icons": icons,
}
want = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
if manifest_path.exists() and manifest_path.read_text(encoding="utf-8") == want:
    print("milestone.webmanifest: already up to date")
else:
    manifest_path.write_text(want, encoding="utf-8")
    print("milestone.webmanifest: written")

# --- 2) milestone-sw.js -------------------------------------------------------
sw = '''// milestone PWA service worker: offline shell + fresh API data.
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
'''
sw_path = web / "milestone-sw.js"
if sw_path.exists() and sw_path.read_text(encoding="utf-8") == sw:
    print("milestone-sw.js: already up to date")
else:
    sw_path.write_text(sw, encoding="utf-8")
    print("milestone-sw.js: written")

# --- 3) milestone.html head/body injection ------------------------------------
html_path = web / "milestone.html"
src = html_path.read_text(encoding="utf-8")
changed = False
if "milestone.webmanifest" not in src:
    head_tags = (
        '<link rel="manifest" href="/milestone.webmanifest">\n'
        '<link rel="icon" type="image/svg+xml" href="/logo.svg">\n'
        '<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">\n'
        '<meta name="theme-color" content="#5B8CFF">\n'
    )
    idx = src.find("</title>")
    if idx == -1:
        print("milestone.html: [FATAL] </title> not found")
        sys.exit(1)
    idx += len("</title>")
    src = src[:idx] + "\n" + head_tags.rstrip("\n") + src[idx:]
    changed = True
if "milestone-sw.js" not in src:
    reg = (
        '<script>\n'
        '  // milestone PWA: register the app shell worker (fails silently on\n'
        '  // plain http — the install still works from the Chrome menu).\n'
        '  if ("serviceWorker" in navigator) {\n'
        '    navigator.serviceWorker.register("/milestone-sw.js", { scope: "/" })\n'
        '      .catch(() => {});\n'
        '  }\n'
        '</script>\n'
    )
    idx = src.rfind("</body>")
    if idx == -1:
        print("milestone.html: [FATAL] </body> not found")
        sys.exit(1)
    src = src[:idx] + reg + src[idx:]
    changed = True
if changed:
    html_path.write_text(src, encoding="utf-8")
    print("milestone.html: manifest + icons + SW registration injected")
else:
    print("milestone.html: already patched")
