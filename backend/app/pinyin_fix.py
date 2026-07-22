# -*- coding: utf-8 -*-
"""Normalize broken bulk herb pinyin (unicode codepoint tokens like u4e24)."""
from __future__ import annotations

import re
from functools import lru_cache

_U_TOKEN = re.compile(r"^u[0-9a-f]{4}$", re.I)


def pinyin_is_broken(py: str | None) -> bool:
    if not py or not str(py).strip():
        return True
    return any(_U_TOKEN.match(tok) for tok in str(py).split())


@lru_cache(maxsize=4096)
def proper_pinyin(name_zh: str) -> str:
    try:
        from pypinyin import lazy_pinyin
    except ImportError:
        return ""
    return " ".join(p.capitalize() for p in lazy_pinyin(name_zh or "") if p)


def display_pinyin(name_zh: str | None, name_pinyin: str | None) -> str | None:
    if name_pinyin and not pinyin_is_broken(name_pinyin):
        return name_pinyin
    fixed = proper_pinyin(name_zh or "")
    return fixed or name_pinyin
