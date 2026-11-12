# QuotaManager — نسخة OpenWrt (فورك abdullah4xx)

> النسخة الإنجليزية: **[README.md](README.md)**

<div align="center">
  <img src="docs/logo/logo.svg" width="96" height="96" alt="Quota Manager logo">
</div>

<h1 align="center">Quota Manager for OpenWrt</h1>

<p align="center">
  <b>توزيع عادل للباقة بين كل بيت — على راوتر OpenWrt.</b>
</p>

> هذا **فورك** من مشروع [UserJoo9/QuotaManager](https://github.com/UserJoo9/QuotaManager)
> (MIT). كل كود المحرك (عدّاد الجيجات، الحصص، التقسيم اليومي، الـ VPN) **كود
> المطور الأصلي بدون أي تعديل** — التعديلات كلها **باتشات idempotent** منفصلة في
> مجلد [`patches/`](patches/) عشان تنطبق بسهولة على أي تحديث جديد للمشروع.

**النسخة المجرّبة فعلياً على:** D-Link **DIR-853 A3** (MediaTek MT7621 — mipsel)
مع **OpenWrt 25.12.6** و USB flash مساحة نظام دائمة.

---

## المحتويات

- [إيه اللي بيعمله](#إيه-اللي-بيعمله)
- [ليه فورك OpenWrt؟](#ليه-فورك-openwrt)
- [التثبيت السريع](#التثبيت-السريع)
- [الباتشات (patches)](#الباتشات-patches)
- [الإعداد بعد التثبيت](#الإعداد-بعد-التثبيت)
- [صفحة المستخدم + التطبيق (PWA)](#صفحة-المستخدم--التطبيق-pwa)
- [الحصة اليومية والتقسيم](#الحصة-اليومية-والتقسيم)
- [الـ VPN على الراوتر](#ال-vpn-على-الراوتر)
- [ضبط الواي فاي (مصر)](#ضبط-الواي-فاي-مصر)
- [الملفات المهمة](#الملفات-المهمة)
- [حل المشاكل](#حل-المشاكل)
- [الرخصه](#الرخصه)

---

## إيه اللي بيعمله

كل شخص في البيت بياخد نصيب (مبلغ ثابت، أو نصيب متساوي من الباقة). كل أجهزته
بتشارك في النصيب ده. لما النصيب يخلص، **أجهزته بتتقطع** — والباقي مش بيتأثر.

- شوف مين استخدم قد إيه، لايف، لكل شخص وكل جهاز
- حدود سرعة + troubleshooting ping
- بلوك/كيك/إيقاف أي جهاز بضغطة
- فلترة إعلانات ومحتوى إباحي للبيت كله
- VPN مدمج، مشاركة ملفات، ووصول من برّه (Tailscale)
- عربي + إنجليزي، فاتح/غامق، موبايل وكمبيوتر

صفحة الاستخدام لكل شخص: `/milestone` — **من غير تسجيل دخول** (الشخص بيتعرف من جهازه).

---

## ليه فورك OpenWrt؟

| العقبة | الحل في هذا الفورك |
|---|---|
| `pydantic-core` مفيش wheel لـ mipsel | `patch_pydantic_v1.py` — رجوع لـ pydantic v1 |
| المساحة بتخلص بسرعة | قاعدة البيانات + اللوج على **الفلاشة** (مش الرام) + نسخ احتياطي يومي |
| الجهاز الجديد بيتسجل لوحده كمستخدم فاضي | `patch_no_autoreg.py` — "Manage أولاً" |
| زر Manage بيعمل يوزر غريب | `patch_manage_user_picker.py` — اختيار الشخص + مسح اليوزر المؤقت |
| المستخدم العادي مش عارف يوصل صفحته | `patch_login_user_page.py` — زر «صفحتي» في شاشة الدخول |
| الصفحة مش قابلة للتثبيت | `patch_milestone_pwa.py` — manifest + service worker + أيقونات |
| قفل الدخول بعد محاولات فاشلة | `patch_login_throttle.py` |
| عنوان الـ uplink المكرر | `patch_uplink_alias.py` |
| VPN: `sing-box` المرفق amd64 | نسخة **mipsle-softfloat** منفّذة في `openwrt/` |
| الإقلاع بيمسح اليوزرز | `db_path` على الفلاشة + `restore-if-missing` في init script |

---

## التثبيت السريع

### 1) تجهيز الراوتر (extroot على الفلاشة)

محتاج **USB flash** (٨ جيجا كفاية) + OpenWrt 25.12 مثبّت.

```sh
#舉 ثبّت الحزم الأساسية
apk update
apk add parted lsblk e2fsprogs block-mount

# قسم الفلاشة ext4 + تفعيل extroot
# (الخطوات كاملة في openwrt/README-extroot.md)
```

> **مهم:** ترتيب الإقلاع مهم — `usb-flash` لازم يركّب **قبل** `quota-manager`.

### 2) تثبيت QuotaManager

```sh
wget -O /tmp/install_openwrt.sh https://raw.githubusercontent.com/abdullah4xx/QuotaManager/main/scripts/install_openwrt.sh
sh /tmp/install_openwrt.sh
```

### 3) تطبيق الباتشات (بعد كل تحديث للمشروع)

```sh
cd /opt/QuotaManager
for p in patches/patch_*.py; do python3 "$p" .; done
/etc/init.d/quota-manager restart
```

كل الباتشات **idempotent** — تشغيلها مرتين ما بيغيّرش حاجة، واللي اتطبّق بيقول
`already patched`.

### 4) نقل قاعدة البيانات للفلاشة (عشان متضيعش مع أي reboot)

```sh
mkdir -p /opt/quota-data/backups
cp /var/lib/quota-gateway/quota.db /opt/quota-data/quota.db
sed -i 's|db_path: /var/lib/quota-gateway/quota.db|db_path: /opt/quota-data/quota.db|' /opt/QuotaManager/config.yaml
```

انسخ `openwrt/quota-manager.initd` فوق `/etc/init.d/quota-manager` (فيه كتلة
**restore-if-missing** بترجّع الـ DB من أحدث نسخة احتياطية لو ضاعت)، و
`openwrt/quota-data-backup.sh` في `/opt/quota-data/backup.sh` + cron يومي:

```sh
echo "17 3 * * * /opt/quota-data/backup.sh >/dev/null 2>&1" >> /etc/crontabs/root
/etc/init.d/cron restart
```

> ⚠️ **ليه مهم:** على OpenWrt الـ `/var` هو symlink لـ `/tmp` (tmpfs) — يعني أي
> قاعدة بيانات في `/var/lib` بتتنسخ **مع كل reboot**. ده كان سبب ضياع
> المستخدمين في تجربتنا الأولى.

---

## الباتشات (patches)

| الباتش | الملف | بيعمل إيه |
|---|---|---|
| pydantic v1 | `patch_pydantic_v1.py` | رجوع لـ pydantic v1 + FastAPI 0.99 (mipsel) |
| uplink alias | `patch_uplink_alias.py` | يمنع تكرار عنوان الـ uplink بين WAN و LAN |
| login throttle | `patch_login_throttle.py` | يرفع ثوابت قفل الدخول (منطق بدون تغيير) |
| Manage أولاً | `patch_no_autoreg.py` | الجهاز الجديد مايتسجلش تلقائياً — يفضل "غير مُدار" لحد ما تضغط Manage |
| اختيار الشخص | `patch_manage_user_picker.py` | مودال Manage فيه اختيار الشخص + **مسح اليوزر المؤقت** اللي بيولد مع الـ adopt |
| زر صفحتي | `patch_login_user_page.py` | زر «صفحتي» في شاشة تسجيل الدخول → `/milestone` |
| PWA | `patch_milestone_pwa.py` | manifest + service worker + أيقونات → تثبيت الصفحة كتطبيق |
| أيقونة WE | `patch_we_portal.py` | رابط بوابة TE Data في الشريط الجانبي |

---

## الإعداد بعد التثبيت

1. **شبكة**: LAN على `192.168.2.0/24` (DHCP ‎.100–.199)، والـ WAN سلك ثابت
   `192.168.1.66/24` + gateway `192.168.1.1` (راوتر الـ ISP).
2. **الباقة**: من صفحة **Quota** → حجم الباقة (مثال 200 GB) + يوم التجديد.
3. **الأشخاص**: من صفحة **الأشخاص** → أضف شخص وحدد نصيبه:
   - `abdullah / mama / baba / mariam / haneen` → **auto** (نصيب متساوي من الباقة)
   - `fawry` → **fixed** بنصيب 2 GB
4. **الأجهزة**: الجهاز الجديد يظهر تحت **أجهزة غير مُدارة** → تضغط **Manage**
   → تختار الشخص → يتسجل كجهاز ليه فوراً. (من غير ما يعمل يوزر فاضي.)
5. **الـ CLI/لوج**:
   ```sh
   ps | grep run.py                 # الخدمة شغالة
   tail -f /var/log/quota-gateway/quota.log
   /etc/init.d/quota-manager restart
   ```

---

## صفحة المستخدم + التطبيق (PWA)

كل شخص يفتح من **جهازه المسجّل**:

```
http://192.168.2.1:8080/milestone
```

- **من غير تسجيل دخول** — التطبيق بيعرف الشخص من IP جهازه (DHCP lease → جهاز → شخص).
- بيعرض: نصيبه، استهلاكه، نسبته، علامات 50/75/100%، استهلاك كل جهاز من أجهزته،
  و**خطته اليومية**.
- **قابلة للتثبيت كتطبيق في كروم**: قا菜单 النقاط الثلاثة → *حفظ ومشاركة → تثبيت
  الصفحة كتطبيق*. الأيقونة والـ manifest موجودين في `patch_milestone_pwa.py`.
- وتقدر توصله بضغطة من **شاشة تسجيل الدخول** — زر «صفحتي».

---

## الحصة اليومية والتقسيم

من **Quota** → فعّل مفتاح الحصة اليومية → كارت الشخص → **Daily plan**:

- **fixed**: جيجا ثابتة كل يوم.
- **spread**: تقسيم المتبقي من الشهر على الأيام المتبقية.
- سياسة النقل (الجيجا الزايدة تنقل لليوم بعده ولا تتوزع)، أيام أثقل، وتقسيم
  نصيب اليوم بين أجهزة الشخص.

**التعديل الذاتي:** لو فعّلت `daily_self_edit` للشخص، يقدر من صفحته نفسها
(`/milestone`) يغيّر **سياسة الإيقاع** (النقل + الأيام الأثقل) — **بس مش يقدر
يغيّر نصيبه الكلي**. الحماية زي ما المطور عاملها: بدون جلسة أدمن، CSRF header،
وحد 10 تعديلات في الدقيقة.

تفعيله مباشرة في الـ DB:

```sh
python3 - <<'EOF'
import sqlite3
c = sqlite3.connect("/opt/quota-data/quota.db")
c.execute("insert or replace into settings(key,value) values('daily_quota_enabled','1')")
c.execute("update users set daily_mode='spread', daily_self_edit=1 where name in "
          "('abdullah','mama','baba','mariam','haneen')")
c.commit()
EOF
```

---

## الـ VPN على الراوتر

الملف المرفق `bin/sing-box` في المشروع الأصلي معمول لـ **amd64** → **مش هيشتغل**
على MT7621 (mipsel). النسخة الصح:

```sh
# sing-box v1.14.4 linux-mipsle-softfloat-musl
wget -O /tmp/sb.tar.gz \
  https://github.com/SagerNet/sing-box/releases/download/v1.14.4/sing-box-1.14.4-linux-mipsle-softfloat-musl.tar.gz
tar xzf /tmp/sb.tar.gz -C /tmp
cp /tmp/sing-box-1.14.4-linux-mipsle-softfloat-musl/sing-box /opt/QuotaManager/bin/sing-box
chmod +x /opt/QuotaManager/bin/sing-box
/opt/QuotaManager/bin/sing-box version   # لازم يطبع: linux/mipsle
```

`geoip.dat` و `geosite.dat` داتا عامة (مش معمارية) → شغالة زي ما هي.

---

## ضبط الواي فاي (مصر)

الحدود القانونية (`country EG`):

| الباند | السقف القانوني | قناة مقترحة |
|---|---|---|
| 2.4 GHz | **20 dBm** | 1 / 6 / 11 (الأنظف حسب الزحمة) |
| 5 GHz | **23 dBm** (5150–5250) | 36 / 40 / 44 / 48 |

- ⚠️ نطاق **5470–5725 (قناة 149) مش موجود في الـ regd المصري** → لو حطيتها، الراديو
  بينزل لـ 9 dBm. استخدم قنوات 36–48.
- `txpower` فوق السقف بينستIgnore، ومن غير `country` بيدّ OpenWrt طاقة أقل.
- `powersave '0'` + `legacy_rates '0'` → سرعة أعلى وping أقل.
- **متحطّش STA (كلاينت) على نفس راديو الـ AP** — ده سبب فصل الـ 2.4: الراديو
  بيتبع قناة الشبكة التانية فالـ AP بيقع. حط الـ uplink **سلك**، أو حط الـ STA
  على الباند التاني.

سكربتات الضبط الجاهزة: `openwrt/scripts/apply_wifi.sh` و `final_wifi.sh`.

---

## الملفات المهمة

| الملف | وظيفته |
|---|---|
| `patches/` | كل الباتشات (idempotent) — شغّلها بعد كل تحديث |
| `openwrt/quota-manager.initd` | init script فيه restore-if-missing للـ DB |
| `openwrt/quota-data-backup.sh` | نسخ احتياطي يومي (7 نسخ + مرايا) |
| `openwrt/config.router.yaml` | إعدادات QuotaManager مخصّصة للراوتر |
| `openwrt/scripts/` | سكربتات ضبط الواي فاي + مساعد SSH |
| `openwrt/pwa-icons/` | أيقونات التطبيق (192/512/maskable) |

---

## حل المشاكل

| المشكلة | الحل |
|---|---|
| اليوزرز اختفوا بعد reboot | الـ DB لسه على الرام → شوف "نقل قاعدة البيانات للفلاشة" فوق |
| `sing-box binary not found` | الـ binary المرفق amd64 → نزّل نسخة mipsle (فوق) |
| الجهاز الجديد مش ظاهر | **الأشخاص → أجهزة غير مُدارة → Manage** (مش تلقائي بالتصميم) |
| `invalid credentials` وباسورد قصير | التطبيق يفرض 12 حرف — غيّر الهاش مباشرة في الـ DB (شوف `docs/openwrt-notes.md`) |
| قفل 30 دقيقة بعد محاولات فاشلة | `patch_login_throttle.py` |
| الصفحة مش بتتحدّث بعد تعديل | تحديث إجباري بالمتصفح (Ctrl+Shift+R) |
| `pydantic` error | `patch_pydantic_v1.py` |

---

## الرخصه

- الكود الأصلي للمطور [UserJoo9/QuotaManager](https://github.com/UserJoo9/QuotaManager) — MIT.
- هذا الفورك: نفس الرخصة. مش تابع لأي مزوّد خدمة.
