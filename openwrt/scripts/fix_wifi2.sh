#!/bin/sh
# restore the 2.4GHz AP (deleted by mistake) and set legal max power for EG
set -e
BACKUP=/opt/quota-data/config-backups/wireless.20261112-1250

echo "=== 1) restore the wireless config from the backup ==="
cp "$BACKUP" /etc/config/wireless
uci show wireless | grep -E "wifi-iface|device|ssid" | head -12

echo "=== 2) remove ONLY the broken STA (named section) ==="
uci -q delete wireless.wifinet2 || true
uci show wireless | grep "wifinet2" && echo "  STILL THERE" || echo "  STA removed"

echo "=== 3) radio0 = 2.4GHz: EG, HT20, 20 dBm (legal max), channel 6 ==="
uci set wireless.radio0.country='EG'
uci set wireless.radio0.htmode='HT20'
uci set wireless.radio0.txpower='20'
uci set wireless.radio0.channel='6'
uci set wireless.radio0.disabled='0'

echo "=== 4) radio1 = 5GHz: EG, channel 36 (23 dBm legal max), VHT80 ==="
uci set wireless.radio1.country='EG'
uci set wireless.radio1.channel='36'
uci set wireless.radio1.txpower='23'
uci set wireless.radio1.htmode='VHT80'
uci set wireless.radio1.disabled='0'

echo "=== 5) both APs: no power saving ==="
for s in ap24 default_radio1; do
  uci set wireless.$s.powersave='0'
  uci set wireless.$s.disabled='0'
done

uci commit wireless
wifi reload
sleep 20

echo "=== 6) results ==="
for i in $(iw dev | awk '/Interface/{print $2}'); do
  echo "-- $i"
  iw dev $i info | grep -E 'ssid|channel|txpower|type'
done
echo "--- wan:"
ip route | grep default
ping -c 2 -W 4 8.8.8.8 2>&1 | tail -2
echo "=== DONE ==="
