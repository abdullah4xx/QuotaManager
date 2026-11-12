#!/bin/sh
# auto-backup of the QuotaManager DB (persistent on the USB flash)
SRC=/opt/quota-data/quota.db
DST=/opt/quota-data/backups
mkdir -p "$DST"
[ -s "$SRC" ] || exit 0
cp "$SRC" "$DST/quota-$(date +%Y%m%d).db"
ls -t "$DST"/quota-*.db 2>/dev/null | tail -n +8 | xargs -r rm -f
if grep -qs " /mnt/usb ext4" /proc/mounts; then
  mkdir -p /mnt/usb/backups
  cp "$SRC" "/mnt/usb/backups/quota-auto-$(date +%Y%m%d).db"
  ls -t /mnt/usb/backups/quota-auto-*.db 2>/dev/null | tail -n +8 | xargs -r rm -f
fi
