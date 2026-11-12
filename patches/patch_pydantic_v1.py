#!/usr/bin/env python3
"""Patch QuotaManager for pydantic v1 (pure-python, no Rust wheel needed).

pydantic-core (Rust) has no mipsel wheels, so on the OpenWrt router we
must run pydantic 1.x + FastAPI 0.99 (pure python). This rewrites the few
v2-only constructs.

Usage: python3 patch_pydantic_v1.py /path/to/QuotaManager
"""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
schemas = root / "api" / "schemas.py"
app = root / "api" / "app.py"

changed = []

# --- api/schemas.py -------------------------------------------------------
s = schemas.read_text()
orig = s

s = s.replace(
    "from pydantic import BaseModel, Field, field_validator",
    "from pydantic import BaseModel, Field, validator as field_validator",
)
# Field(..., pattern="...")  ->  Field(..., regex="...")
s = re.sub(r"\bpattern\s*=", "regex=", s)

if s != orig:
    schemas.write_text(s)
    changed.append(str(schemas))

# --- api/app.py -----------------------------------------------------------
a = app.read_text()
orig = a
a = a.replace("body.model_dump(exclude_none=True)", "body.dict(exclude_none=True)")
if a != orig:
    app.write_text(a)
    changed.append(str(app))

print("patched:")
for c in changed:
    print("  -", c)
if not changed:
    print("  (nothing to patch - already compatible)")
