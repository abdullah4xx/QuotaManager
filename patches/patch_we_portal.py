#!/usr/bin/env python3
"""Add a 'WE' entry to the QuotaManager sidebar that opens the WE (TE Data)
self-care portal login in a new tab.

What it touches (4 small edits, nothing else):
  1. web/js/components/icons.js  -> add the "we" icon (circle)
  2. web/js/core/dom.js          -> render the "we" icon with the word "we" inside
  3. web/js/main.js              -> nav item + external-link rendering
  4. web/js/i18n/{en,ar}.js      -> the "nav.we" label

Idempotent: running it twice changes nothing the second time.

Usage: python3 patch_we_portal.py /opt/QuotaManager
"""
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else "/opt/QuotaManager")
WEB = root / "web" / "js"
changed = []


def edit(path, old, new, tag):
    p = WEB / path
    s = p.read_text(encoding="utf-8")
    if new in s:
        print(f"  [skip] {path} ({tag} already applied)")
        return
    if old not in s:
        print(f"  [WARN] {path}: anchor for {tag} not found - skipped")
        return
    p.write_text(s.replace(old, new, 1), encoding="utf-8")
    changed.append(f"{path} ({tag})")
    print(f"  [ok] {path} ({tag})")


print("patching", WEB)

# 1) the icon path (a circle = the WE logo mark)
edit(
    "components/icons.js",
    '  close: "M6 6l12 12 M18 6L6 18",',
    '  close: "M6 6l12 12 M18 6L6 18",\n'
    '  we: "M12 2.6a9.4 9.4 0 1 0 0 18.8 9.4 9.4 0 0 0 0-18.8z",',
    "we icon",
)

# 2) draw the word "we" inside the circle
edit(
    "core/dom.js",
    """    p.setAttribute("d", d); svg.append(p);
  }
  return svg;
}""",
    """    p.setAttribute("d", d); svg.append(p);
  }
  if (name === "we") {
    const tx = document.createElementNS("http://www.w3.org/2000/svg", "text");
    tx.setAttribute("x", "12"); tx.setAttribute("y", "16");
    tx.setAttribute("text-anchor", "middle");
    tx.setAttribute("font-size", "10"); tx.setAttribute("font-weight", "700");
    tx.setAttribute("font-family", "system-ui, sans-serif");
    tx.setAttribute("letter-spacing", "-0.5");
    tx.setAttribute("fill", "currentColor"); tx.setAttribute("stroke", "none");
    tx.textContent = "we";
    svg.append(tx);
  }
  return svg;
}""",
    "we glyph",
)

# 3) the nav entry + external link rendering
edit(
    "main.js",
    '  { id: "system", icon: "system", group: "nav.tools", page: system },\n];',
    '  { id: "system", icon: "system", group: "nav.tools", page: system },\n'
    '  { id: "we", icon: "we", group: "nav.tools", external: '
    '"https://my.te.eg/echannel/#/login" },\n];',
    "nav entry",
)

edit(
    "main.js",
    """      g.items.map((r) => h("a", { class: "nav-i" + (s.route === r.id ? " on" : ""), href: "#/" + r.id, title: t("nav." + r.id), "aria-current": s.route === r.id ? "page" : null, onclick: () => store.set({ navOpen: false }) },
        icon(r.icon), h("span", { class: "nav-t" }, t("nav." + r.id)),
        r.count && s.dashboard ? h("span", { class: "nav-badge" }, num(s.dashboard.users.filter((u) => !u.protected).length, 0)) : null))))),""",
    """      g.items.map((r) => r.external
        ? h("a", { class: "nav-i", href: r.external, target: "_blank", rel: "noopener noreferrer", title: t("nav." + r.id), onclick: () => store.set({ navOpen: false }) },
          icon(r.icon), h("span", { class: "nav-t" }, t("nav." + r.id)))
        : h("a", { class: "nav-i" + (s.route === r.id ? " on" : ""), href: "#/" + r.id, title: t("nav." + r.id), "aria-current": s.route === r.id ? "page" : null, onclick: () => store.set({ navOpen: false }) },
        icon(r.icon), h("span", { class: "nav-t" }, t("nav." + r.id)),
        r.count && s.dashboard ? h("span", { class: "nav-badge" }, num(s.dashboard.users.filter((u) => !u.protected).length, 0)) : null))))),""",
    "external nav rendering",
)

# 4) labels
edit(
    "i18n/en.js",
    '  "nav.share": "Share", "nav.system": "System",',
    '  "nav.share": "Share", "nav.system": "System", "nav.we": "WE",',
    "en label",
)
edit(
    "i18n/ar.js",
    '  "nav.share": "المشاركة", "nav.system": "النظام",',
    '  "nav.share": "المشاركة", "nav.system": "النظام", "nav.we": "WE",',
    "ar label",
)

print()
print("changed:", changed if changed else "nothing (already patched)")
