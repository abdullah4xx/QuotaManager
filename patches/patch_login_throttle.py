#!/usr/bin/env python3
"""Disable the QuotaManager login throttling.

The app ships a progressive failed-login throttle (api/app.py):
  LOGIN_FREE_FAILURES = 3       instant attempts, then an exponential backoff
  LOGIN_LOCKOUT_FAILURES = 12   -> 30-minute lockout
  LOGIN_GLOBAL_MAX_FAILURES = 50 across all source IPs -> 30-minute lockout

On a home setup with one admin that is pure friction: a typo locks you out
of your own dashboard for half an hour ("too many failed logins - try again
later"), and there is no way to clear it from the UI.

This patch raises the thresholds so the throttle never triggers. It touches
only the five constants - no logic changes.

Idempotent: running it twice changes nothing the second time.

Usage: python3 patch_login_throttle.py /opt/QuotaManager
"""
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else "/opt/QuotaManager")
app = root / "api" / "app.py"

src = app.read_text(encoding="utf-8")

REPLACEMENTS = [
    ("LOGIN_FREE_FAILURES = 3",
     "LOGIN_FREE_FAILURES = 1000000"),
    ("LOGIN_LOCKOUT_FAILURES = 12",
     "LOGIN_LOCKOUT_FAILURES = 1000000"),
    ("LOGIN_GLOBAL_MAX_FAILURES = 50",
     "LOGIN_GLOBAL_MAX_FAILURES = 1000000"),
    ("LOGIN_BACKOFF_BASE_SEC = 1.0",
     "LOGIN_BACKOFF_BASE_SEC = 0.0"),
    ("LOGIN_MAX_BACKOFF_SEC = 300.0",
     "LOGIN_MAX_BACKOFF_SEC = 0.0"),
    ("LOGIN_LOCKOUT_SEC = 1800.0",
     "LOGIN_LOCKOUT_SEC = 0.0"),
]

changed = []
for old, new in REPLACEMENTS:
    if new in src:
        print(f"  [skip] {old}  (already patched)")
        continue
    if old not in src:
        print(f"  [WARN] not found: {old}")
        continue
    src = src.replace(old, new, 1)
    changed.append(old)

if changed:
    app.write_text(src, encoding="utf-8")
    print("patched:", changed)
else:
    print("nothing to patch")
