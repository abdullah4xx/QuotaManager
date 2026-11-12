#!/usr/bin/env python3
"""manage-first UI: the Manage button opens a dialog that registers the device
AND picks the person it belongs to, in one step.

Changes:
  web/js/components/peopleDialogs.js - add openAdoptDevice(rogue, refresh)
  web/js/pages/people.js             - Manage button opens that dialog
  web/js/i18n/ar.js + en.js          - two new keys

Idempotent: running twice changes nothing the second time.
Usage: python3 patch_manage_user_picker.py /opt/QuotaManager
"""
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else "/opt/QuotaManager")
MARK = "openAdoptDevice"

# --- peopleDialogs.js -------------------------------------------------------
pd = root / "web" / "js" / "components" / "peopleDialogs.js"
src = pd.read_text(encoding="utf-8")
if MARK in src and "res.user_id" not in src:
    # upgrade v1 -> v2: also delete the auto-minted user after assigning
    old = ('      if (owner.value) await api.patch("/api/devices/" + res.id,\n'
           '        { user_id: +owner.value });\n')
    new = ('      if (owner.value) {\n'
           '        await api.patch("/api/devices/" + res.id, { user_id: +owner.value });\n'
           '        if (res.user_id) await api.del("/api/users/" + res.user_id);\n'
           '      }\n')
    if old in src:
        src = src.replace(old, new, 1)
        pd.write_text(src, encoding="utf-8")
        print("peopleDialogs.js: upgraded - mints no leftover user")
    else:
        print("peopleDialogs.js: [WARN] v1 onSubmit not found - check manually")
elif MARK in src:
    print("peopleDialogs.js: already patched")
if MARK not in src:
    if 'from "../core/api.js"' not in src:
        src = src.replace(
            'import { h } from "../core/dom.js";',
            'import { h } from "../core/dom.js";\nimport { api } from "../core/api.js";',
            1,
        )
    helper = (
        "\n\n"
        "// manage-first PATCH: register the device AND pick its person in one step\n"
        "export function openAdoptDevice(rogue, refresh) {\n"
        "  const name = h(\"input\", { class: \"input\" });\n"
        "  const owner = h(\"select\", { class: \"select\" },\n"
        "    h(\"option\", { value: \"\" }, t(\"add.dev.owner.later\")));\n"
        "  openDialog({ title: t(\"pp.rogue.manage\"),\n"
        "    sub: [rogue.mac, rogue.ip].filter(Boolean).join(\" - \"),\n"
        "    submitLabel: t(\"add.submit\"),\n"
        "    content: [f(t(\"add.dev.name\"), name), f(t(\"add.dev.owner\"), owner),\n"
        "      h(\"span\", { class: \"sub\" }, t(\"pp.rogue.manage.hint\"))],\n"
        "    onSubmit: async () => {\n"
        "      const res = await api.post(\"/api/rogue/adopt\",\n"
        "        { mac: rogue.mac, ip: rogue.ip || \"\", name: name.value.trim() });\n"
        "      if (owner.value) await api.patch(\"/api/devices/\" + res.id,\n"
        "        { user_id: +owner.value });\n"
        "      toast(t(\"pp.rogue.adopted\")); await refresh(); return true;\n"
        "    } });\n"
        "  api.get(\"/api/users\").then((us) =>\n"
        "    us.filter((u) => !u.protected && u.name)\n"
        "      .forEach((u) => owner.append(h(\"option\", { value: String(u.id) }, u.name))))\n"
        "    .catch(() => {});\n"
        "}\n"
    )
    src = src.rstrip() + "\n" + helper
    pd.write_text(src, encoding="utf-8")
    print("peopleDialogs.js: added openAdoptDevice")
else:
    print("peopleDialogs.js: already patched")

# --- people.js --------------------------------------------------------------
pp = root / "web" / "js" / "pages" / "people.js"
src = pp.read_text(encoding="utf-8")
if "openAdoptDevice(r, ctx.refresh)" not in src:
    src = src.replace(
        'import { openAddUser, openAddDevice } from "../components/peopleDialogs.js";',
        'import { openAddUser, openAddDevice, openAdoptDevice } from "../components/peopleDialogs.js";',
        1,
    )
    old_btn = ('onclick: act(async () => { await api.post("/api/rogue/adopt", '
               '{ mac: r.mac, ip: r.ip }); toast(t("pp.rogue.adopted")); })')
    new_btn = "onclick: act(() => openAdoptDevice(r, ctx.refresh))"
    if old_btn in src:
        src = src.replace(old_btn, new_btn, 1)
        pp.write_text(src, encoding="utf-8")
        print("people.js: Manage button now opens the person picker")
    else:
        print("people.js: [WARN] Manage button pattern not found - check manually")
else:
    print("people.js: already patched")

# --- i18n -------------------------------------------------------------------
I18N = {
    "web/js/i18n/ar.js": [
        ("pp.rogue.manage.hint",
         "الجهاز هيتسجل ويتشال من القطع. اختار الشخص اللي يتبع له، أو سيبه فاضي وحدده لاحقاً من «تابع لـ»."),
        ("add.dev.owner.later",
         "بدون شخص - أحدده لاحقاً"),
    ],
    "web/js/i18n/en.js": [
        ("pp.rogue.manage.hint",
         "Registers the device and lifts the cut. Pick the person it belongs to, or leave empty and assign later from the device row."),
        ("add.dev.owner.later",
         "No person - assign later"),
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
        idx = next((i for i, l in enumerate(lines) if '"pp.rogue.adopted"' in l), None)
        if idx is None:
            idx = next((i for i, l in enumerate(lines) if '"pp.rogue.manage"' in l), None)
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
