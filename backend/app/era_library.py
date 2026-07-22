# -*- coding: utf-8 -*-
"""朝代典籍 / 方剂索引：基于 era_library.json + formulas_*.json。"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from .analysis import CLASSICAL_TITLE_ZH, _classical_zh_name, _load_formulas

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ERA_LIBRARY_PATH = DATA_DIR / "era_library.json"

# 功效粗分类（用于首页图表）
_CATEGORY_TO_EFFECT = {
    "解表剂": "解表",
    "清热剂": "清热",
    "泻下剂": "清热",
    "祛湿剂": "清热",
    "温里剂": "温里",
    "补益剂": "补益",
    "补气剂": "补益",
    "补血剂": "补益",
    "补阴剂": "滋阴",
    "滋阴剂": "滋阴",
    "和解剂": "疏肝",
    "理气剂": "疏肝",
    "安神剂": "安神",
    "止血剂": "止血",
    "治燥剂": "治燥",
    "祛痰剂": "祛痰",
    "固涩剂": "固涩",
    "消食剂": "消食",
    "开窍剂": "开窍",
    "治风剂": "治风",
    "活血剂": "活血",
    "理血剂": "活血",
    "驱虫剂": "其他",
    "温病": "温病",
}


@lru_cache(maxsize=1)
def _load_era_library() -> dict[str, Any]:
    if not ERA_LIBRARY_PATH.exists():
        return {"eras": []}
    try:
        data = json.loads(ERA_LIBRARY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"eras": []}
    return data if isinstance(data, dict) else {"eras": []}


def _formula_effect(f: dict[str, Any]) -> str:
    cat = str(f.get("category") or "")
    for k, v in _CATEGORY_TO_EFFECT.items():
        if k in cat:
            return v
    # 温病条辨等
    src = str(f.get("source_text_key") or "")
    if "wen_bing" in src or "wen_re" in src:
        return "温病"
    return cat.replace("剂", "")[:4] or "其他"


def _formula_brief(f: dict[str, Any], name_map: dict[str, str] | None = None) -> dict[str, Any]:
    herbs = []
    for item in f.get("composition") or []:
        if not isinstance(item, dict):
            continue
        hk = item.get("herb_key")
        if not hk:
            continue
        name = (name_map or {}).get(hk) or hk
        herbs.append([hk, name])
    principle = f.get("treatment_principle") or {}
    principle_zh = principle.get("zh") if isinstance(principle, dict) else principle
    src = f.get("source_text_key")
    return {
        "key": f.get("key"),
        "name_zh": f.get("name_zh"),
        "category": f.get("category"),
        "effect": _formula_effect(f),
        "tip": principle_zh or f.get("description_zh") or "",
        "source_text_key": src,
        "source_title": _classical_zh_name(src) if src else None,
        "herbs": herbs[:8],
    }


def build_era_index(name_map: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """返回各朝典籍 + 归入该朝的方剂列表。"""
    lib = _load_era_library()
    formulas = _load_formulas()
    by_src: dict[str, list[dict[str, Any]]] = {}
    for f in formulas:
        src = f.get("source_text_key")
        if not src:
            continue
        by_src.setdefault(str(src), []).append(f)

    assigned: set[str] = set()
    eras_out: list[dict[str, Any]] = []

    for era in lib.get("eras") or []:
        if not isinstance(era, dict):
            continue
        keys = [str(k) for k in (era.get("source_text_keys") or [])]
        flist: list[dict[str, Any]] = []
        for sk in keys:
            for f in by_src.get(sk, []):
                fk = f.get("key")
                if not fk or fk in assigned:
                    continue
                assigned.add(fk)
                flist.append(_formula_brief(f, name_map))
        flist.sort(key=lambda x: (x.get("category") or "", x.get("name_zh") or ""))

        classics = []
        for c in era.get("classics") or []:
            if not isinstance(c, dict):
                continue
            classics.append(
                {
                    "key": c.get("key"),
                    "title": c.get("title"),
                    "year": c.get("year"),
                    "kind": c.get("kind"),
                    "blurb": c.get("blurb"),
                }
            )

        eras_out.append(
            {
                "id": era.get("id"),
                "dynasty": era.get("dynasty"),
                "classics": classics,
                "classic_count": len(classics),
                "formulas": flist,
                "formula_count": len(flist),
                "source_text_keys": keys,
            }
        )

    # 未归入任何朝代的方剂：挂到「明」作为兜底（杂方书多承元明）
    orphan = []
    for f in formulas:
        fk = f.get("key")
        if fk and fk not in assigned:
            orphan.append(_formula_brief(f, name_map))
            assigned.add(fk)
    if orphan:
        for e in eras_out:
            if e.get("id") == "ming":
                e["formulas"].extend(orphan)
                e["formulas"].sort(key=lambda x: (x.get("category") or "", x.get("name_zh") or ""))
                e["formula_count"] = len(e["formulas"])
                break

    return eras_out


def get_era_by_id(era_id: str, name_map: dict[str, str] | None = None) -> dict[str, Any] | None:
    for e in build_era_index(name_map):
        if e.get("id") == era_id or e.get("dynasty") == era_id:
            return e
    return None


def list_all_classical_titles() -> dict[str, str]:
    """合并静态映射 + 库中出现过的出处。"""
    out = dict(CLASSICAL_TITLE_ZH)
    for f in _load_formulas():
        src = f.get("source_text_key")
        if src and src not in out:
            zh = _classical_zh_name(src)
            if zh:
                out[str(src)] = zh
    lib = _load_era_library()
    for era in lib.get("eras") or []:
        for c in era.get("classics") or []:
            k = c.get("key")
            t = c.get("title")
            if k and t:
                out[str(k)] = str(t)
    return out
