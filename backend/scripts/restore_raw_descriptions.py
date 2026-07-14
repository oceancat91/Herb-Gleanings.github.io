# -*- coding: utf-8 -*-
"""从 herbs_raw.json 恢复本草典条目的原始 description（不被课程模板覆盖）。"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "herbs.db"
RAW = ROOT / "data" / "herbs_raw.json"


def main():
    raw_rows = json.loads(RAW.read_text(encoding="utf-8"))
    by_key = {r["key"]: r for r in raw_rows if r.get("key")}

    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    restored = 0
    for r in cur.execute("SELECT id, key, source, description FROM herbs").fetchall():
        if "课程扩充" in (r["source"] or ""):
            continue
        raw = by_key.get(r["key"])
        if not raw:
            continue
        desc = raw.get("description_zh") or raw.get("description_en")
        if not desc:
            continue
        if (r["description"] or "") != desc:
            cur.execute("UPDATE herbs SET description=? WHERE id=?", (desc, r["id"]))
            restored += 1
    conn.commit()
    conn.close()
    print(f"已恢复本草典概述：{restored} 条")


if __name__ == "__main__":
    main()
