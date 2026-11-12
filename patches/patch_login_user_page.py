#!/usr/bin/env python3
"""user page button: add a "صفحتي" button on the admin login screen that sends
the ordinary household user to their own milestone page (/milestone).

The milestone page is public by design and resolves the person from the
requesting device's DHCP lease, so the button needs no login at all.

Changes:
  web/js/main.js       - renderLogin(): a ghost button under the submit button
                         (location.href = "/milestone")
  web/js/i18n/ar.js    - key "login.my.page" (+ hint)
  web/js/i18n/en.js    - key "login.my.page" (+ hint)

Idempotent: running twice changes nothing the second time.
Usage: python3 patch_login_user_page.py /opt/QuotaManager
"""
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else "/opt/QuotaManager")

# --- web/js/main.js ----------------------------------------------------------
mj = root / "web" / "js" / "main.js"
src = mj.read_text(encoding="utf-8")
if "login.my.page" in src:
    print("main.js: already patched")
else:
    anchor = '  const form = h("form", { class: "login-card", onsubmit: async (e) => {'
    if anchor not in src:
        print("main.js: [FATAL] form anchor not found - nothing written")
        sys.exit(1)
    button = (
        '  // user-page PATCH: send the household user to their own public\n'
        '  // milestone page (the person is resolved from the device IP, no login)\n'
        '  const userBtn = h("button", { class: "btn ghost", type: "button",\n'
        '    style: { width: "100%", marginTop: "10px" }, title: t("login.my.page.hint"),\n'
        '    onclick: () => { location.href = "/milestone"; } }, t("login.my.page"));\n'
    )
    src = src.replace(anchor, button + anchor, 1)
    tail_old = '    btn);\n  mount(document.getElementById("root"), h("div", { class: "login" }, form));'
    tail_new = '    btn,\n    userBtn);\n  mount(document.getElementById("root"), h("div", { class: "login" }, form));'
    if tail_old not in src:
        print("main.js: [FATAL] form-tail anchor not found - nothing written")
        sys.exit(1)
    src = src.replace(tail_old, tail_new, 1)
    mj.write_text(src, encoding="utf-8")
    print("main.js: user button added to the login card")

# --- i18n ---------------------------------------------------------------------
I18N = {
    "web/js/i18n/ar.js": [
        ("login.my.page",
         "صفحتي — استهلاكي وتقسيمي"),
        ("login.my.page.hint",
         "افتحها من جهازك المسجّل: هتشوف نصيبك من الباقة وتقسيمك اليومي، من غير تسجيل دخول."),
    ],
    "web/js/i18n/en.js": [
        ("login.my.page",
         "My page — my usage & plan"),
        ("login.my.page.hint",
         "Open it from your registered device: your quota share and daily plan, no login needed."),
    ],
}
for rel, pairs in I18N.items():
    p = root / rel
    src = p.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)
    touched = False
    for key, value in pairs:
        if f'"{key}"' in src:
            continue
        idx = next((i for i, l in enumerate(lines) if '"login.wrongcode"' in l), None)
        if idx is None:
            print(f"{rel}: [WARN] no anchor for {key}")
            continue
        lines.insert(idx + 1, f'  "{key}": "{value}",\n')
        touched = True
    if touched:
        p.write_text("".join(lines), encoding="utf-8")
        print(f"{rel}: keys added")
    else:
        print(f"{rel}: already patched")
