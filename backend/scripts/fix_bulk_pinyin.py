# -*- coding: utf-8 -*-
"""Fix bulk herb name_pinyin that used unicode codepoint tokens like u4e24."""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

from pypinyin import lazy_pinyin

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "herbs.db"
BULK_JSON = ROOT / "data" / "herbs_bulk.json"

U_TOKEN = re.compile(r"^u[0-9a-f]{4}$", re.I)


def is_broken_pinyin(py: str | None) -> bool:
    if not py:
        return True
    return any(U_TOKEN.match(tok) for tok in str(py).split())


def proper_pinyin(name_zh: str) -> str:
    parts = lazy_pinyin(name_zh or "")
    return " ".join(p.capitalize() for p in parts if p)


def fix_db() -> int:
    con = sqlite3.connect(DB)
    rows = con.execute("SELECT id, name_zh, name_pinyin FROM herbs").fetchall()
    n = 0
    for hid, zh, py in rows:
        if not is_broken_pinyin(py):
            continue
        new_py = proper_pinyin(zh or "")
        if not new_py or new_py == py:
            continue
        con.execute("UPDATE herbs SET name_pinyin = ? WHERE id = ?", (new_py, hid))
        n += 1
    con.commit()
    con.close()
    return n


def fix_bulk_json() -> int:
    if not BULK_JSON.exists():
        return 0
    data = json.loads(BULK_JSON.read_text(encoding="utf-8"))
    n = 0
    items = data if isinstance(data, list) else data.get("herbs") or data.get("items") or []
    for h in items:
        py = h.get("name_pinyin")
        zh = h.get("name_zh") or ""
        if is_broken_pinyin(py):
            h["name_pinyin"] = proper_pinyin(zh)
            n += 1
    if isinstance(data, list):
        BULK_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        BULK_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return n


def main():
    db_n = fix_db()
    json_n = fix_bulk_json()
    print(f"fixed db={db_n} bulk_json={json_n}")
    # verify
    con = sqlite3.connect(DB)
    rows = con.execute("SELECT name_zh, name_pinyin FROM herbs").fetchall()
    broken = sum(1 for _, py in rows if is_broken_pinyin(py))
    print(f"remaining broken={broken} / {len(rows)}")
    # sample former U
    for zh, py in rows:
        if zh in ("两面针", "丹皮", "八月札", "制何首乌", "胡荽"):
            print(zh, "->", py)


if __name__ == "__main__":
    main()
