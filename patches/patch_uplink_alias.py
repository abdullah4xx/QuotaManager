#!/usr/bin/env python3
"""Patch QuotaManager for a router whose uplink is a SEPARATE interface.

The upstream project assumes ONE NIC: the box carries both the client
gateway IP (192.168.2.1) and the uplink IP (e.g. 192.168.1.110) on the
same interface, so `ensure_network_infrastructure()` re-adds the uplink IP
to the LAN interface when it is missing.

On an OpenWrt router the uplink is a separate interface (WiFi STA ->
phy0-sta0). Adding the uplink IP to br-lan as well creates a DUPLICATE
address on two interfaces, which breaks the NAT reply path (the kernel
delivers the un-NATed reply locally instead of forwarding it).

This patch makes the check global: if the uplink IP already exists on ANY
interface, the LAN alias is not added.

Usage: python3 patch_uplink_alias.py /opt/QuotaManager
"""
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
target = root / "quota" / "startup_health.py"

HELPER = '''
def _addr_exists_anywhere(run, ip: str) -> bool:
    """True when the address is already configured on ANY interface."""
    code, out = run(["ip", "-4", "-o", "addr", "show"])
    if code != 0:
        return False
    return any(f" {ip}/" in line for line in out.splitlines())


'''

OLD = """    # Uplink / router-admin alias (required in both LAN and WAN mode).
    if uplink_ip:
        ul_cidr = f"{uplink_ip}/{lan_cidr}"
        if ul_cidr not in addrs:
            matched = any(a.startswith(uplink_ip + "/") for a in addrs)
            if not matched:
                log.warning("LAN interface %s missing uplink alias %s — re-adding",
                            iface, ul_cidr)
                needed[ul_cidr] = uplink_ip
"""

NEW = """    # Uplink / router-admin alias (required in both LAN and WAN mode).
    # PATCH: skip when the uplink IP already lives on another interface
    # (router setup: the uplink is a separate NIC/STA). Adding it here too
    # would create a duplicate address and break the NAT reply path.
    if uplink_ip:
        ul_cidr = f"{uplink_ip}/{lan_cidr}"
        if ul_cidr not in addrs:
            matched = any(a.startswith(uplink_ip + "/") for a in addrs)
            if not matched and not _addr_exists_anywhere(run, uplink_ip):
                log.warning("LAN interface %s missing uplink alias %s — re-adding",
                            iface, ul_cidr)
                needed[ul_cidr] = uplink_ip
"""

src = target.read_text()
if "PATCH: skip when the uplink IP already lives on another interface" in src:
    print("already patched")
    raise SystemExit(0)

if OLD not in src:
    print("ERROR: anchor block not found — upstream changed?")
    raise SystemExit(1)

src = src.replace(OLD, NEW)

# insert the helper right before ensure_network_infrastructure
anchor = "def ensure_network_infrastructure("
idx = src.index(anchor)
src = src[:idx] + HELPER.lstrip("\n") + src[idx:]

target.write_text(src)
print("patched:", target)
