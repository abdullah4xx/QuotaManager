# Quota Manager — OpenWrt edition (fork `abdullah4xx/QuotaManager`)

<div align="center">
  <img src="docs/logo/logo.svg" width="96" height="96" alt="Quota Manager logo">
</div>

<h1 align="center">Quota Manager for OpenWrt</h1>

<p align="center">
  <b>Share one limited internet bundle fairly between everyone at home — on an OpenWrt router.</b>
</p>

> This is a **fork** of [UserJoo9/QuotaManager](https://github.com/UserJoo9/QuotaManager) (MIT).
> The whole engine — byte counting, allowances, the daily split, the VPN — is the
> developer's **original code, untouched**. Every change here lives in a separate,
> **idempotent** patch under [`patches/`](patches/) so it re-applies cleanly after
> any upstream update.
>
> Arabic version: **[README_AR.md](README_AR.md)**

**Tested on:** D-Link **DIR-853 A3** (MediaTek MT7621 — mipsel), **OpenWrt 25.12.6**,
with a USB flash used as the permanent system disk.

---

## What it does

Every person gets an allowance (a fixed number of GB, or an equal share of what's
left). All of their devices share it. When it runs out, **their devices are cut
off** — nobody else is affected.

- See who used how much, live, per person and per device
- Speed limits and low ping for gaming
- Block, kick or pause any device in one tap
- Block ads and adult/gambling sites for the whole house
- Built-in VPN, file sharing, and remote access (Tailscale)
- English and Arabic, light and dark, phone and desktop

Every person also gets **their own usage page**: `/milestone` — **no login**
(the person is resolved from their own device).

---

## Why this fork?

| Obstacle | Fix in this fork |
|---|---|
| No `pydantic-core` wheel for mipsel | `patch_pydantic_v1.py` — back to pydantic v1 |
| Storage space runs out | database + logs on the **flash** (not RAM) + daily backups |
| A reboot wiped every user | `db_path` on flash + a **restore-if-missing** block in the init script |
| New devices auto-registered as empty users | `patch_no_autoreg.py` — **Manage first** |
| The Manage button spawned a stray user | `patch_manage_user_picker.py` — pick the person + delete the temp user |
| Ordinary people couldn't reach their page | `patch_login_user_page.py` — a "My page" button on the login screen |
| The page couldn't be installed | `patch_milestone_pwa.py` — manifest + service worker + icons |
| 30-minute login lockout | `patch_login_throttle.py` |
| Duplicate uplink address | `patch_uplink_alias.py` |
| VPN: the bundled `sing-box` is amd64 | a **mipsle-softfloat** build is documented below |

---

## Quick install

### 1) Router prep (extroot on the flash)

You need a **USB flash** (8 GB is enough) and OpenWrt 25.12.

```sh
apk update
apk add parted lsblk e2fsprogs block-mount
```

Then partition the flash as ext4 and enable extroot — the full walkthrough is in
**[`openwrt/README-extroot.md`](openwrt/README-extroot.md)**.

> **Order matters:** `usb-flash` must mount **before** `quota-manager` starts.

### 2) Install QuotaManager

```sh
wget -O /tmp/install_openwrt.sh https://raw.githubusercontent.com/abdullah4xx/QuotaManager/main/scripts/install_openwrt.sh
sh /tmp/install_openwrt.sh
```

### 3) Apply the patches (after every upstream update)

```sh
cd /opt/QuotaManager
for p in patches/patch_*.py; do python3 "$p" .; done
/etc/init.d/quota-manager restart
```

Every patch is **idempotent** — run it twice and nothing changes; the second run
prints `already patched`.

### 4) Move the database onto the flash (so no reboot can lose it)

```sh
mkdir -p /opt/quota-data/backups
cp /var/lib/quota-gateway/quota.db /opt/quota-data/quota.db
sed -i 's|db_path: /var/lib/quota-gateway/quota.db|db_path: /opt/quota-data/quota.db|' /opt/QuotaManager/config.yaml
```

Copy `openwrt/quota-manager.initd` over `/etc/init.d/quota-manager` (it contains a
**restore-if-missing** block that brings the database back from the newest
automatic backup if it ever disappears), and `openwrt/quota-data-backup.sh` to
`/opt/quota-data/backup.sh`, then add the daily cron:

```sh
echo "17 3 * * * /opt/quota-data/backup.sh >/dev/null 2>&1" >> /etc/crontabs/root
/etc/init.d/cron restart
```

> ⚠️ **Why this matters:** on OpenWrt `/var` is a symlink to `/tmp` (tmpfs) — a
> database living in `/var/lib` is wiped **on every reboot**. That was the real
> cause of "my users disappeared".

---

## The patches

| Patch | File | What it does |
|---|---|---|
| pydantic v1 | `patch_pydantic_v1.py` | pydantic v1 + FastAPI 0.99 (mipsel) |
| uplink alias | `patch_uplink_alias.py` | stops the uplink IP being duplicated on WAN and LAN |
| login throttle | `patch_login_throttle.py` | raises the lockout constants (no logic change) |
| Manage first | `patch_no_autoreg.py` | a brand-new device is **not** auto-registered — it waits under *Unmanaged devices* until you press **Manage** |
| person picker | `patch_manage_user_picker.py` | the Manage dialog asks which person it belongs to, and **deletes the throwaway user** the adopt used to create |
| my-page button | `patch_login_user_page.py` | a "My page" button on the login screen → `/milestone` |
| PWA | `patch_milestone_pwa.py` | manifest + service worker + icons → the page installs as an app |
| WE portal | `patch_we_portal.py` | a "WE" link in the sidebar (TE Data portal) |

---

## After the install

1. **Network**: LAN `192.168.2.0/24` (DHCP `.100–.199`), WAN wired static
   `192.168.1.66/24` + gateway `192.168.1.1` (the ISP router).
2. **Bundle**: **Quota** page → bundle size (e.g. 200 GB) + renewal day.
3. **People**: **People** page → add a person and give them an allowance:
   - `abdullah / mama / baba / mariam / haneen` → **auto** (equal share)
   - `fawry` → **fixed**, 2 GB
4. **Devices**: a new device appears under **Unmanaged devices** → press
   **Manage** → pick the person → it is registered as their device instantly
   (and no empty user is left behind).
5. **Service**:
   ```sh
   ps | grep run.py                 # is it running?
   tail -f /var/log/quota-gateway/quota.log
   /etc/init.d/quota-manager restart
   ```

---

## The user's own page (+ installable app)

Each person opens this **from their registered device**:

```
http://192.168.2.1:8080/milestone
```

- **No login** — the app resolves the person from the device's IP
  (DHCP lease → device → person).
- Shows: their allowance, usage, percentage, the 50/75/100 % markers, the usage
  of each of their devices, and **their daily plan**.
- **Installable as an app in Chrome**: ⋮ menu → *Cast, save and share → Install
  page as app*. The manifest, service worker and icons ship with
  `patch_milestone_pwa.py`.
- The login screen carries a **"My page"** button that takes people straight there.

---

## Daily quota and the split

**Quota** → switch the daily quota on → the person's card → **Daily plan**:

- **fixed**: a fixed number of GB per day.
- **spread**: split what is left of the month over the days that are left.
- carry policy (unused GB to the next day, or spread out), heavier days, and how
  the day's allowance is shared between their devices.

**Self-editing:** with `daily_self_edit` enabled for a person, they can adjust
the **pacing** from their own page (`/milestone`) — carry policy and heavy days
— but they can **never** change their own total. The developer's protections
stay in place: no admin session, a CSRF header, and 10 edits per minute.

Enable it directly in the database:

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

## VPN on the router

The bundled `bin/sing-box` is an **amd64** binary — it cannot run on an MT7621
(mipsel). Use the matching build:

```sh
wget -O /tmp/sb.tar.gz \
  https://github.com/SagerNet/sing-box/releases/download/v1.14.4/sing-box-1.14.4-linux-mipsle-softfloat-musl.tar.gz
tar xzf /tmp/sb.tar.gz -C /tmp
cp /tmp/sing-box-1.14.4-linux-mipsle-softfloat-musl/sing-box /opt/QuotaManager/bin/sing-box
chmod +x /opt/QuotaManager/bin/sing-box
/opt/QuotaManager/bin/sing-box version   # must print: linux/mipsle
```

`geoip.dat` and `geosite.dat` are plain data — architecture independent, they work
as shipped.

---

## WiFi tuning (Egypt)

The legal limits for `country EG`:

| Band | Legal maximum | Suggested channel |
|---|---|---|
| 2.4 GHz | **20 dBm** | 1 / 6 / 11 (pick the quietest) |
| 5 GHz | **23 dBm** (5150–5250) | 36 / 40 / 44 / 48 |

- ⚠️ The **5470–5725 band (channel 149) is not in the Egyptian regdomain** — put it
  there and the radio drops to 9 dBm. Use 36–48.
- Above the ceiling the driver ignores you; without `country` OpenWrt simply
  gives you less power.
- `powersave '0'` and `legacy_rates '0'` → more throughput, lower ping.
- **Never run a STA (client) on the same radio as the AP** — that is what made the
  2.4 GHz drop: the radio follows the other network's channel and the AP falls
  over. Use a **wired uplink**, or put the STA on the other band.

Ready-made scripts: `openwrt/scripts/apply_wifi.sh` and `final_wifi.sh`.

---

## Key files

| File | Purpose |
|---|---|
| `patches/` | every patch (idempotent) — re-run them after each update |
| `openwrt/quota-manager.initd` | init script with the restore-if-missing block |
| `openwrt/quota-data-backup.sh` | daily backup (7 copies + a mirror) |
| `openwrt/config.router.yaml` | QuotaManager config tuned for the router |
| `openwrt/scripts/` | WiFi tuning scripts + an SSH helper |
| `openwrt/pwa-icons/` | app icons (192 / 512 / maskable) |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Users vanished after a reboot | the DB is still on RAM → see *Move the database onto the flash* above |
| `sing-box binary not found` | the bundled binary is amd64 → install the mipsle build above |
| A new device doesn't show up | **People → Unmanaged devices → Manage** (by design, not automatic) |
| `invalid credentials` with a short password | the app requires 12 characters — write the hash straight into the DB (see `openwrt/README-extroot.md`) |
| 30-minute lockout after a few tries | `patch_login_throttle.py` |
| The page doesn't refresh after an edit | force-reload the browser (Ctrl+Shift+R) |
| `pydantic` errors | `patch_pydantic_v1.py` |

---

## ⚠️ Gotchas we hit on OpenWrt (read before configuring quotas)

| Trap | What happens | What to do |
|---|---|---|
| **`allow` list** | The dev's *Manage/adopt* flow puts every new MAC in the allow list (`api/app.py`: `add_mac_list("allow", [mac])`), and an allow-listed MAC is **never quota-blocked** — it silently ignores its person's quota **and** the daily device caps | `patches/patch_manage_user_picker.py` (v3) removes the MAC right after the adopt. Re-run the patches after every update |
| **allowance 0 ≠ cut** | For a normal user, a 0 GB allowance means *unmetered* (the dev's `no allowance => unmetered` guard) — the cut only happens once the usage exceeds it | use `quota_mode: "disabled"` (the onboarding lock) to cut someone immediately |
| **top-ups *and* packs add up** | `allowance = fixed_gb + topup_gb + active user-targeted packs` — a 19 GB pack on top of `fixed 19` gives **38** | keep one of them, not both |
| **`reset-month`** | clears the period usage **and** the top-ups (packs are rolled over, not cleared) | re-check the numbers after a reset |
| **one admin session** | every `/api/login` rotates the session token and kicks the other session | reuse one cookie; re-login on `{"detail":"not logged in"}` |
| **shaping needs two switches** | `config.yaml: shaping.enabled: true` **and** the line speed in the DB (`POST /api/network`) | both, or the per-user speed caps stay unused |
| **speed caps are Mbps** | 500 KB/s = **4 Mbps** (`2 Mbps` = 250 KB/s) | — |
| **caps need a live lease** | the tc shaper only creates a class for devices that currently have an IP | a device that is offline gets its cap when it reconnects |

---

## License

- Original project by [UserJoo9](https://github.com/UserJoo9/QuotaManager) — MIT.
- This fork keeps the same license. Not affiliated with any ISP.
