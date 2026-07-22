# -*- coding: utf-8 -*-
"""校验并打印各朝典籍/方剂索引（不联网爬取，基于本地 formulas + era_library）。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.era_library import build_era_index, _load_era_library  # noqa: E402


def main() -> None:
    _load_era_library.cache_clear()
    eras = build_era_index()
    total = 0
    print("朝代典籍 / 方剂索引")
    print("-" * 48)
    for e in eras:
        n = e.get("formula_count") or 0
        total += n
        print(
            f"{e.get('dynasty'):<4}  典籍 {e.get('classic_count') or 0:>2}  "
            f"方剂 {n:>3}  · {[c.get('title') for c in (e.get('classics') or [])[:2]]}"
        )
    print("-" * 48)
    print(f"合计方剂 {total}")
    print("API: GET /api/eras  GET /api/eras/{id}")


if __name__ == "__main__":
    main()
