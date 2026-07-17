# -*- coding: utf-8 -*-
"""炼药：君臣佐使搭配、七情文案、方剂覆盖匹配（课程通识，非诊疗）。"""
from __future__ import annotations

from collections import Counter
from typing import Any

from .analysis import ROLE_ZH, _load_formulas
from .models import Herb
from .workshop import (
    _brief,
    _classic_conflicts,
    _level_from_conflicts,
    _text_mentions,
)

# 相须 / 相使：课程通识增效药对（示意）
_XIANGXU: list[tuple[set[str], set[str], str]] = [
    ({"人参"}, {"黄芪"}, "相须：人参与黄芪皆补气，同用可增强益气之力"),
    ({"石膏"}, {"知母"}, "相须：石膏、知母同清气分大热，清热生津相得"),
    ({"黄柏"}, {"知母"}, "相须：黄柏、知母同清下焦虚火，滋阴降火相须"),
    ({"大黄"}, {"芒硝"}, "相须：大黄泻热通便，芒硝软坚润燥，攻下相须"),
    ({"麻黄"}, {"桂枝"}, "相须：麻黄开表，桂枝解肌，发汗解表相须"),
    ({"柴胡"}, {"黄芩"}, "相须：柴胡透邪，黄芩清里，和解少阳相须"),
    ({"当归"}, {"川芎"}, "相须：当归补血活血，川芎行气活血，养血调经相须"),
    ({"熟地黄"}, {"山茱萸", "山萸肉"}, "相须：熟地滋肾阴，山茱萸补肾固精，补肾相须"),
    ({"半夏"}, {"陈皮"}, "相须：半夏燥湿化痰，陈皮理气化痰，二陈相须"),
    ({"苍术"}, {"厚朴"}, "相须：苍术燥湿健脾，厚朴行气除满，平胃相须"),
]

_XIANGSHI: list[tuple[set[str], set[str], str]] = [
    ({"黄芪"}, {"当归"}, "相使：黄芪补气，当归补血，气旺则血生（当归补血汤意）"),
    ({"人参"}, {"白术"}, "相使：人参大补元气，白术健脾燥湿，补气健脾相使"),
    ({"茯苓"}, {"白术"}, "相使：白术健脾，茯苓渗湿，健脾祛湿相使"),
    ({"桂枝"}, {"白芍", "芍药"}, "相使：桂枝辛温解肌，白芍酸寒敛阴，调和营卫相使"),
    ({"麻黄"}, {"杏仁"}, "相使：麻黄宣肺平喘，杏仁降肺止咳，宣降相使"),
    ({"黄连"}, {"木香"}, "相使：黄连清热燥湿，木香行气止痛，治痢相使"),
    ({"附子"}, {"干姜"}, "相使：附子回阳，干姜温中，回阳救逆相使"),
    ({"甘草"}, {"白芍", "芍药"}, "相使：甘草缓急，白芍养血柔肝，缓急止痛相使"),
]

_XIANGWEI: list[tuple[set[str], set[str], str]] = [
    ({"半夏"}, {"生姜"}, "相畏/相杀：生姜能制半夏毒，半夏畏生姜"),
    ({"生南星", "天南星"}, {"生姜"}, "相畏：南星有毒，生姜可制其毒"),
    ({"甘遂"}, {"大枣"}, "相畏示意：甘遂峻下，大枣护正缓毒"),
]

_XIANGSHA: list[tuple[set[str], set[str], str]] = [
    ({"绿豆"}, {"巴豆", "巴豆霜"}, "相杀：绿豆可解巴豆毒（通识示意）"),
    ({"防风"}, {"砒霜", "信石"}, "相杀：防风可解砒霜毒（通识示意）"),
]

_XIANGWU: list[tuple[set[str], set[str], str]] = [
    ({"人参"}, {"莱菔子"}, "相恶：莱菔子耗气，恶人参补气之力"),
    ({"生姜"}, {"黄芩"}, "相恶：黄芩苦寒，恶生姜辛温之性（通识示意）"),
]

_ROLE_HINT = {
    "君": "常作君药：针对主证起主要治疗作用，为一汤之主帅。",
    "臣": "常作臣药：辅助君药加强疗效，或兼顾兼证。",
    "佐": "常作佐药：佐助、反佐或制毒，使方义更周全。",
    "使": "常作使药：引经报使或调和诸药，使全方协同。",
}

_EASTER = [
    "丹成！方义闭合，君臣佐使各安其位。",
    "药气氤氲——你炼出的正是经典全方。",
    "彩蛋：全方覆盖达成，可对照方解细读君臣配伍。",
]


def _pair_in_sets(a: str, b: str, left: set[str], right: set[str]) -> bool:
    return (a in left and b in right) or (b in left and a in right)


def _copy_for_kind(kind: str, a: str, b: str, rule: str) -> str:
    if kind in ("相须", "相使"):
        return (
            f"「{a}」与「{b}」属{kind}：求增效。{rule}。"
            "君臣佐使中，宜以主证之君为纲，臣佐相助。"
        )
    if kind in ("相畏", "相杀"):
        return (
            f"「{a}」与「{b}」属{kind}：求减毒。{rule}。"
            "置入时可作提醒，炼药时仍须审慎。"
        )
    if kind in ("相反", "相恶", "十八反", "十九畏"):
        return (
            f"「{a}」与「{b}」属{kind}：提示禁忌或减效。{rule}。"
            "可继续置入学习，点击「炼药」将提示炼出禁忌毒药。"
        )
    return rule


def _scan_pairs(
    names: list[str],
    rules: list[tuple[set[str], set[str], str]],
    kind: str,
    level: str,
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    seen: set[str] = set()
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            for left, right, rule in rules:
                if not _pair_in_sets(a, b, left, right):
                    continue
                key = f"{kind}|{a}|{b}|{rule}"
                if key in seen:
                    continue
                seen.add(key)
                hits.append(
                    {
                        "level": level,
                        "kind": kind,
                        "pair": [a, b],
                        "rule": rule,
                        "copy": _copy_for_kind(kind, a, b, rule),
                    }
                )
    return hits


def _relation_hits(names: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    hits += _scan_pairs(names, _XIANGXU, "相须", "boost")
    hits += _scan_pairs(names, _XIANGSHI, "相使", "boost")
    hits += _scan_pairs(names, _XIANGWEI, "相畏", "mitigate")
    hits += _scan_pairs(names, _XIANGSHA, "相杀", "mitigate")
    hits += _scan_pairs(names, _XIANGWU, "相恶", "warn")

    # 十八反 / 十九畏 → 相反类禁忌
    for c in _classic_conflicts(names):
        kind = c.get("kind") or "禁忌"
        mapped = "相反" if kind == "十八反" else ("相恶" if kind == "十九畏" else kind)
        a, b = (c.get("pair") or ["", ""])[:2]
        rule = c.get("rule") or ""
        hits.append(
            {
                "level": c.get("level") or "danger",
                "kind": mapped,
                "pair": [a, b],
                "rule": rule,
                "copy": _copy_for_kind(mapped, a, b, rule),
                "source_kind": kind,
            }
        )
    return hits


def _herb_role_profile(herb_key: str) -> dict[str, Any]:
    """统计一味药在方剂库中最常担任的君臣佐使身份。"""
    roles: Counter[str] = Counter()
    sample_formulas: list[dict[str, str]] = []
    for f in _load_formulas():
        for item in f.get("composition") or []:
            if not isinstance(item, dict):
                continue
            if item.get("herb_key") != herb_key:
                continue
            role = ROLE_ZH.get((item.get("role") or "").strip().lower()) or "未标"
            roles[role] += 1
            if len(sample_formulas) < 3:
                sample_formulas.append(
                    {
                        "key": f.get("key") or "",
                        "name_zh": f.get("name_zh") or f.get("key") or "",
                        "role": role,
                    }
                )
    top = roles.most_common(1)
    top_role = top[0][0] if top else None
    return {
        "role_counts": dict(roles),
        "top_role": top_role,
        "hint": _ROLE_HINT.get(top_role or "", "本库方剂中暂少见其君臣佐使标注，可作佐使或随证配伍理解。"),
        "sample_formulas": sample_formulas,
        "formula_hits": sum(roles.values()),
    }


def _match_formulas(keys: list[str], limit: int = 16) -> list[dict[str, Any]]:
    """按覆盖度匹配方剂：full = 选药完全覆盖方组成；partial = 方含全部选药。"""
    if not keys:
        return []
    key_set = set(keys)
    out: list[dict[str, Any]] = []
    for f in _load_formulas():
        comps = [c for c in (f.get("composition") or []) if isinstance(c, dict) and c.get("herb_key")]
        fkeys = [c["herb_key"] for c in comps]
        fset = set(fkeys)
        if not fset:
            continue
        if not key_set.issubset(fset):
            continue
        covered = len(key_set)
        total = len(fset)
        full = key_set == fset
        roles = []
        for c in comps:
            if c["herb_key"] in key_set:
                roles.append(
                    {
                        "herb_key": c["herb_key"],
                        "role": ROLE_ZH.get((c.get("role") or "").strip().lower()),
                        "dosage": c.get("dosage"),
                    }
                )
        principle = f.get("treatment_principle") or {}
        if isinstance(principle, dict):
            principle_zh = principle.get("zh")
        else:
            principle_zh = str(principle) if principle else None
        out.append(
            {
                "key": f.get("key"),
                "name_zh": f.get("name_zh") or f.get("key"),
                "category": f.get("category"),
                "source_text_key": f.get("source_text_key"),
                "principle": principle_zh,
                "description": (f.get("description_zh") or "")[:160] or None,
                "coverage": "full" if full else "partial",
                "covered": covered,
                "total": total,
                "roles": roles,
                "composition_keys": fkeys,
            }
        )
    out.sort(key=lambda x: (0 if x["coverage"] == "full" else 1, -x["covered"], x["total"]))
    return out[:limit]


def place_herb_feedback(herb: Herb, placed: list[Herb]) -> dict[str, Any]:
    """置入一味药时的即时反馈：角色身份 + 与已置入药的关系提醒（不阻止）。"""
    others = [h for h in placed if h.key != herb.key]
    names = [herb.name_zh] + [h.name_zh for h in others if h.name_zh]
    relations = _relation_hits(names)
    # 只保留涉及新药的关系
    new_name = herb.name_zh
    related = [r for r in relations if new_name in (r.get("pair") or [])]
    taboo = [r for r in related if r.get("level") in ("danger", "warn") or r.get("kind") in ("相反", "相恶", "十八反", "十九畏")]
    boost = [r for r in related if r.get("kind") in ("相须", "相使")]
    mitigate = [r for r in related if r.get("kind") in ("相畏", "相杀")]

    profile = _herb_role_profile(herb.key)
    popup = {
        "title": f"置入「{herb.name_zh}」",
        "role_line": profile["hint"],
        "top_role": profile["top_role"],
        "formula_hits": profile["formula_hits"],
        "sample_formulas": profile["sample_formulas"],
        "reminders": [r.get("copy") or r.get("rule") for r in (boost + mitigate + taboo)[:4]],
        "blocked": False,
        "note": "冲突仅提醒，不阻止继续置入；点击炼药后再判定禁忌结果。",
    }
    return {
        "herb": _brief(herb),
        "role_profile": profile,
        "relations": related,
        "popup": popup,
    }


def refine(herbs: list[Herb]) -> dict[str, Any]:
    """点击炼药：匹配方剂 + 禁忌判定 + 彩蛋。"""
    herbs = [h for h in herbs if h is not None][:12]
    names = [h.name_zh for h in herbs if h.name_zh]
    keys = [h.key for h in herbs if h.key]

    relations = _relation_hits(names)
    for c in _text_mentions(herbs):
        pair = c.get("pair") or []
        if len(pair) >= 2:
            relations.append(
                {
                    "level": c.get("level") or "info",
                    "kind": c.get("kind") or "条文互指",
                    "pair": pair,
                    "rule": c.get("rule") or c.get("evidence") or "",
                    "copy": _copy_for_kind(
                        c.get("kind") or "条文互指",
                        pair[0],
                        pair[1],
                        c.get("rule") or c.get("evidence") or "",
                    ),
                }
            )

    conflicts = [r for r in relations if r.get("level") in ("danger", "warn") or r.get("kind") in ("相反", "相恶")]
    boosts = [r for r in relations if r.get("kind") in ("相须", "相使")]
    mitigates = [r for r in relations if r.get("kind") in ("相畏", "相杀")]

    matches = _match_formulas(keys)
    full = [m for m in matches if m.get("coverage") == "full"]
    partial = [m for m in matches if m.get("coverage") == "partial"]

    taboo_poison = bool(conflicts)
    easter = None
    if full and not taboo_poison:
        idx = sum(ord(c) for c in "".join(keys)) % len(_EASTER)
        easter = {
            "title": "丹成 · 全方覆盖",
            "message": _EASTER[idx],
            "formula": full[0],
        }

    if taboo_poison:
        result_title = "炼出禁忌毒药"
        result_body = (
            "所选药材触发相反 / 相恶或十八反、十九畏类警示。"
            "学习上应记住禁忌组合；本页仅为课程示意，不构成处方建议。"
        )
    elif full:
        f0 = full[0]
        result_title = f"炼成 · {f0.get('name_zh')}"
        result_body = (
            f"完全覆盖「{f0.get('name_zh')}」组成。"
            f"功效：{f0.get('principle') or '见方解'}。"
            f"{(f0.get('description') or '')}"
        )
    elif partial:
        names_f = "、".join(m.get("name_zh") or "" for m in partial[:3])
        result_title = "未全覆盖 · 含药方提示"
        result_body = (
            f"未凑齐任一方完整组成，但下列方剂含有已置入药材：{names_f}。"
            "可继续添药求全覆盖，或点开方名对照君臣佐使。"
        )
    else:
        result_title = "炉火未成"
        result_body = "本库暂未匹配到同时含上述药材的经典方。可减少味数，或以君药为主另选臣佐。"

    # 每味药的身份摘要
    roles_summary = []
    for h in herbs:
        p = _herb_role_profile(h.key)
        roles_summary.append(
            {
                "key": h.key,
                "name_zh": h.name_zh,
                "top_role": p["top_role"],
                "hint": p["hint"],
            }
        )

    level = _level_from_conflicts(
        [{"level": r.get("level")} for r in conflicts]
        if conflicts
        else []
    )

    return {
        "disclaimer": "学习示意，非诊疗建议。七情与十八反/十九畏按课程通识规则；君臣佐使以本库方剂统计为参考。",
        "level": "danger" if taboo_poison else level,
        "taboo_poison": taboo_poison,
        "result_title": result_title,
        "result_body": result_body,
        "herbs": [_brief(h) for h in herbs],
        "roles_summary": roles_summary,
        "relations": {
            "boost": boosts,
            "mitigate": mitigates,
            "taboo": conflicts,
            "all": relations,
        },
        "matches": {"full": full, "partial": partial},
        "easter_egg": easter,
        "core_tip": "炼药核心：以君臣佐使为纲——君主证，臣辅君，佐制偏或兼证，使调和或引经。",
    }
