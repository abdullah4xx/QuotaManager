#!/bin/sh
# ===== strengthen the WiFi and fix the wired uplink =====
set -e
STAMP=$(date +%Y%m%d-%H%M)
mkdir -p /opt/quota-data/config-backups
cp /etc/config/wireless "/opt/quota-data/config-backups/wireless.$STAMP"
cp /etc/config/network "/opt/quota-data/config-backups/network.$STAMP"
echo "backups saved: /opt/quota-data/config-backups/*.$STAMP"

echo "=== 1) scan the 2.4GHz neighbourhood ==="
iw dev phy0-ap0 scan > /tmp/scan2g.txt 2>/dev/null || true
python3 - <<'EOF'
import re
try:
    txt = open("/tmp/scan2g.txt").read()
except OSError:
    txt = ""
# count how many beacons we hear per channel (2.4GHz)
ch = {}
freq = None
for line in txt.splitlines():
    m = re.search(r"freq:\s*(\d+)", line)
    if m:
        freq = int(m.group(1))
    if freq and 2400 <= freq <= 2500:
        ch[freq] = ch.get(freq, 0) + 1
def chan_of(f):
    return {2412: 1, 2437: 6, 2462: 11}.get(f)
best, best_n = 1, 10**9
print("  beacons heard per channel:")
for f in sorted(ch):
    c = chan_of(f)
    if c:
        print(f"    ch{c} ({f} MHz): {ch[f]} beacons")
        if ch[f] < best_n:
            best, best_n = c, ch[f]
print(f"  --> cleanest of 1/6/11 = channel {best} ({best_n} beacons)")
open("/tmp/best_ch.txt", "w").write(str(best))
EOF
BEST=$(cat /tmp/best_ch.txt 2>/dev/null || echo 6)

echo "=== 2) drop the broken phone-hotspot STA (it shares radio0 with the AP) ==="
uci -q delete wireless.wifinet2 || true
uci -q delete wireless.@wifi-iface[1] 2>/dev/null || true
# make sure nothing else is a client on radio0
uci show wireless | grep -E "wifinet2|type='sta'" || echo "  no STA left"

echo "=== 3) radio0 (2.4GHz): EG domain, HT20, max power, clean channel ==="
uci set wireless.radio0.country='EG'
uci set wireless.radio0.htmode='HT20'
uci set wireless.radio0.txpower='20'
uci set wireless.radio0.channel="$BEST"
uci set wireless.radio0.disabled='0'
uci set wireless.radio0.airtime_fairness='1' 2>/dev/null || true

echo "=== 4) radio1 (5GHz): EG domain, channel 149 (UNII-3, allows 30dBm) ==="
uci set wireless.radio1.country='EG'
uci set wireless.radio1.channel='149'
uci set wireless.radio1.txpower='30'
uci set wireless.radio1.htmode='VHT80'
uci set wireless.radio1.disabled='0'
uci set wireless.radio1.airtime_fairness='1' 2>/dev/null || true

echo "=== 5) both APs: no power saving (better speed + lower ping) ==="
for s in ap24 default_radio1; do
  uci set wireless.$s.powersave='0' 2>/dev/null || true
done

echo "=== 6) wired uplink: make sure wan has gateway + dns and the default route ==="
uci set network.wan.proto='static'
uci set network.wan.ipaddr='192.168.1.66/24'
uci set network.wan.gateway='192.168.1.1'
uci set network.wan.dns='8.8.8.8 1.1.1.1'
uci set network.wan.defaultroute='1'
uci set network.wan.peerdns='0'
uci commit wireless
uci commit network

echo "=== 7) apply ==="
/etc/init.d/network restart
sleep 8
wifi reload
sleep 18

echo "=== 8) results ==="
echo "--- default route:"
ip route | grep default || echo "  STILL NO DEFAULT ROUTE"
echo "--- internet:"
ping -c 2 -W 4 8.8.8.8 2>&1 | tail -2
echo "--- dns:"
nslookup openwrt.org 2>&1 | tail -3
echo "--- interfaces:"
iw dev | grep -E "Interface|ssid|txpower|type"
echo "--- regd:"
iw reg get | grep -E "^country|phy #" | head -6
echo "--- channels:"
uci get wireless.radio0.channel
uci get wireless.radio1.channel
echo "=== DONE ==="
