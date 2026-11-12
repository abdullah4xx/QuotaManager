# extroot على فلاشة USB — خطوة بخطوة (OpenWrt 25.12)

الفلاشة USB هي **مساحة النظام الدائمة** لكل حاجة: المشروع، الـ venv، قاعدة
البيانات، والسكربتات. من غيرها، أي `apk add` أو `git pull` بيملا الفلاش الداخلي
(5 MB في ROM!) ويكسر النظام.

> **ليه مهم:** على OpenWrt الفلاش الداخلي `/rom` صغير جداً (5 MB) والرام
> `/tmp` بيمسح مع كل reboot. لازم الفلاشة تكون extroot.

---

## 1) تجهيز الفلاشة

```sh
apk update
apk add parted lsblk e2fsprogs block-mount

# اسم الفلاشة (شوفها ب lsblk)
lsblk
# مثال: /dev/sda  (بعد sda1 و sda2 هيгоوا system/data)

# فك القرص:
diskpart /dev/sda
#   erase part1
#   erase part2
#   make part1 ext4 512
#   make part2 ext4 1024
#   quit

# فورمات:
mkfs.ext4 /dev/sda1
mkfs.ext4 /dev/sda2

# تفعيل extroot
extroot enable
extroot reboot
```

## 2) تثبيت QuotaManager (بعد ما يرجع الراوتر)

```sh
wget -O /tmp/install_openwrt.sh \
  https://raw.githubusercontent.com/abdullah4xx/QuotaManager/main/scripts/install_openwrt.sh
sh /tmp/install_openwrt.sh
```

## 3) ترتيب الإقلاع (مهم!)

`usb-flash` لازم يركّب **قبل** `quota-manager`:

```sh
/etc/init.d/usb-flash enable      # S99
/etc/init.d/quota-manager enable   # S95
ls /etc/rc.d/ | grep -E 'usb-flash|quota-manager'
```

لو `quota-manager` اشتغل قبل ما الفلاشة تتركّب، الـ DB مكانش هيلقى مكانه.

## 4) نقل قاعدة البيانات للفلاشة

```sh
mkdir -p /opt/quota-data/backups
cp /var/lib/quota-gateway/quota.db /opt/quota-data/quota.db
sed -i 's|db_path: /var/lib/quota-gateway/quota.db|db_path: /opt/quota-data/quota.db|' \
  /opt/QuotaManager/config.yaml
grep -n db_path /opt/QuotaManager/config.yaml
```

انسخ `quota-manager.initd` من مجلد `openwrt/` فوق `/etc/init.d/quota-manager` —
فيه كتلة **restore-if-missing** بترجّع القاعدة من أحدث نسخة احتياطية.

## 5) النسخ الاحتياطي التلقائي

```sh
cp openwrt/quota-data-backup.sh /opt/quota-data/backup.sh
chmod +x /opt/quota-data/backup.sh
echo "17 3 * * * /opt/quota-data/backup.sh >/dev/null 2>&1" >> /etc/crontabs/root
/etc/init.d/cron restart
/opt/quota-data/backup.sh      # جرّبها دلوقتي
ls -la /opt/quota-data/backups/
```

النسخ بتروح مكانين: `/opt/quota-data/backups/` و `/mnt/usb/backups/` (مرايا)،
وبيتمسح الأقدم من 7 نسخ.

## 6) مكان كل الملفات بعد كل ده

| المسار | المحتوى |
|---|---|
| `/opt/QuotaManager/` | كود المشروع (على الفلاشة) |
| `/opt/quota-data/quota.db` | قاعدة البيانات الدائمة |
| `/opt/quota-data/backups/` | النسخ الاحتياطية |
| `/opt/quota-data/config-backups/` | نسخ إعدادات wireless/network |
| `/etc/config/` | إعدادات النظام (على الـ overlay = الفلاشة) |

---

## تغيير كلمة سر الأدمن (اختياري)

التطبيق يفرض **12 حرف** على الأقل على كلمة السر، فلو عايز كلمة أقصر اكتب
الهاش مباشرة:

```sh
python3 - <<'EOF'
import hashlib, secrets, sqlite3
salt = secrets.token_bytes(16)
dk = hashlib.pbkdf2_hmac("sha256", b"YOUR-PASSWORD", salt, 200000)
stored = f"{salt.hex()}$200000${dk.hex()}"
c = sqlite3.connect("/opt/quota-data/quota.db")
c.execute("insert or replace into settings(key,value) values('admin_password',?)", (stored,))
c.commit()
EOF
```

صيغة الهاش: `salt.hex()$iterations$dk.hex()` (PBKDF2-HMAC-SHA256).

---

## صيانة الفلاشة

```sh
# فحص دوري للفلاشة (ext4 ممكن يعمل أخطاء بعد انقطاع كهرباء)
e2fsck -f /dev/sda1

# اقرا حالة الفلاشة
smartctl -a /dev/sda        # لو smartmontools متثبت
```

> 💡 **نصيحة:** لو الفلاشة بتظهر مشاكل، اعمل نسخة من `/opt/quota-data` على
> جهاز تاني — الـ `backup.sh` بيعمل نسخة تلقائي كل يوم، بس نسخة برّه البت
> أحسن من نسخة على نفس الفلاشة.
