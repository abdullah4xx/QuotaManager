#!/bin/sh
# ===== final WiFi tuning: legal-max power for EG + best throughput settings =====
set -e
STAMP=$(date +%Y%m%d-%H%M)
cp /etc/config/wireless "/opt/quota-data/config-backups/wireless.$STAMP.pre-final"
echo "backup: wireless.$STAMP.pre-final"

echo "=== 0) what does the hardware/regd allow per channel? ==="
iw phy phy0 info 2>/dev/null | grep -E '\* 2437 MHz' | head -2
iw phy phy1 info 2>/dev/null | grep -E '\* 5180 MHz|\* 5200 MHz' | head -2
iw reg get | sed -n '2,6p'

echo "=== 1) radio0 = 2.4 GHz : 20 dBm (EG legal max), HT20, clean channel 6 ==="
uci set wireless.radio0.country='EG'
uci set wireless.radio0.htmode='HT20'
uci set wireless.radio0.txpower='20'
uci set wireless.radio0.channel='6'
uci set wireless.radio0.cell_density='0'
uci set wireless.radio0.disabled='0'
uci set wireless.radio0.legacy_rates='0'      # drop 802.11b: less noise, more speed
uci set wireless.radio0.noscan='0'

echo "=== 2) radio1 = 5 GHz : 23 dBm (EG legal max), ch36, VHT80 ==="
uci set wireless.radio1.country='EG'
uci set wireless.radio1.htmode='VHT80'
uci set wireless.radio1.txpower='23'
uci set wireless.radio1.channel='36'
uci set wireless.radio1.cell_density='0'
uci set wireless.radio1.disabled='0'
uci set wireless.radio1.legacy_rates='0'

echo "=== 3) APs: no power save, WMM on, same SSID for roaming ==="
for s in ap24 default_radio1; do
  uci set wireless.$s.powersave='0'
  uci set wireless.$s.wmm='1'
  uci set wireless.$s.disabled='0'
  uci set wireless.$s.encryption='sae-mixed'
  uci set wireless.$s.key='asdf1234'
done
uci set wireless.ap24.ssid='OpenWrt'
uci set wireless.default_radio1.ssid='OpenWrt'
uci set wireless.ap24.network='lan'
uci set wireless.default_radio1.network='lan'

uci commit wireless
wifi reload
sleep 20

echo "=== 4) verify ==="
for i in $(iw dev | awk '/Interface/{print $2}'); do
  echo "-- $i"
  iw dev $i info | grep -E 'ssid|channel|txpower|type'
done
echo "--- STA must be gone (2.4 = pure AP):"
iw dev | awk '/Interface/{print $2}' | grep -c sta || true
echo "--- wan + internet:"
ip route | grep default
ping -c 3 -W 4 8.8.8.8 2>&1 | tail -2
echo "=== DONE ==="
