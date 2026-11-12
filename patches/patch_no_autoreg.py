#!/usr/bin/env python3
"""manage-first: stop auto-registering brand-new devices as empty users.

A device that joins via DHCP stays UNMANAGED (no device row, no user row).
The rogue scan flags it (People > Unmanaged devices) and the unmanaged-block
policy keeps it cut off until the admin presses Manage and picks a person.

Changes (run.py only):
  1. _persist_lease: the brand-new-device branch logs and returns instead of
     minting a device + user in the DISABLED onboarding lock.
  2. _scan_rogues: the known-set now only contains MACs that HAVE a device row
     (plus deny/refused/kicked), so DHCP clients awaiting adoption surface as
     rogues with a Manage button.

Idempotent: running twice changes nothing the second time.
Usage: python3 patch_no_autoreg.py /opt/QuotaManager
"""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else "/opt/QuotaManager")
run = root / "run.py"
src = run.read_text(encoding="utf-8")
MARK = "manage-first"
if MARK in src:
    print("already patched")
    sys.exit(0)

changed = []

# --- 1) _persist_lease: brand-new-device branch -----------------------------
pat = re.compile(
    r"                else:\n"
    r"                    # Brand-new device:.*?\"info\", dev\.id\)\n",
    re.DOTALL,
)
new_else = (
    "                else:\n"
    "                    # manage-first PATCH: a brand-new device stays\n"
    "                    # UNMANAGED - no device row, no user row, no share.\n"
    "                    # It shows up in People > Unmanaged devices (rogue\n"
    "                    # scan) and stays cut off until the admin presses\n"
    "                    # Manage and picks a person.\n"
    "                    log.info(\"new MAC %s (%s) stays unmanaged - adopt it\"\n"
    "                             \" from People > Unmanaged devices > Manage\",\n"
    "                             mac, ip)\n"
    "                    return\n"
)
src, n = pat.subn(new_else, src, count=1)
if n != 1:
    print("[FATAL] brand-new-device branch not matched - nothing written")
    sys.exit(1)
changed.append("_persist_lease else-branch")

# --- 2) _scan_rogues: known-set requires a device row -----------------------
old_known = (
    "            leases = await self.database.list_leases()\n"
    "            known = {l.mac for l in leases}\n"
    "            known |= set(await self.service.static_hosts())  # adopted static-IP devices\n"
    "            rogues = await asyncio.to_thread(self.arp_scanner.scan, known)\n"
)
new_known = (
    "            leases = await self.database.list_leases()\n"
    "            # manage-first PATCH: only MACs with a device row are known,\n"
    "            # so a DHCP client the admin has not adopted yet shows up as\n"
    "            # a rogue below (People > Unmanaged devices > Manage).\n"
    "            devices = {d.mac for d in await self.database.list_devices()}\n"
    "            known = {l.mac for l in leases if l.mac in devices}\n"
    "            known |= set(await self.service.static_hosts())  # adopted static-IP devices\n"
    "            known |= {m.lower() for m in await self.database.get_mac_list(\"deny\")}\n"
    "            known |= {m.lower() for m in await self.service.refused_macs()}\n"
    "            known |= {m.lower() for m in await self.service.refused_random_macs()}\n"
    "            known |= {m.lower() for m in self.service.active_kicked_macs()}\n"
    "            rogues = await asyncio.to_thread(self.arp_scanner.scan, known)\n"
)
if old_known in src:
    src = src.replace(old_known, new_known, 1)
    changed.append("_scan_rogues known-set")
else:
    print("[FATAL] rogue known-set not matched - nothing written")
    sys.exit(1)

run.write_text(src, encoding="utf-8")
print("patched:", changed)
