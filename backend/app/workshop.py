# -*- coding: utf-8 -*-
"""配伍工坊：禁忌校核、属性对照、共现方剂与教学结论（课程通识，非诊疗）。"""
from __future__ import annotations

from collections import Counter
from typing import Any

from .analysis import ROLE_ZH, _load_formulas, _split_multi
from .models import Herb
from .pinyin_fix import display_pinyin

# 十八反（课程通识常用表述，按药名集合匹配）
_SHIBA_FAN: list[tuple[set[str], set[str], str]] = [
    (
        {"甘草"},
        {"甘遂", "大戟", "海藻", "芫花"},
        "十八反：甘草反甘遂、大戟、海藻、芫花",
    ),
    (
        {"川乌", "草乌", "附子", "乌头"},
        {"川贝母", "浙贝母", "平贝母", "伊贝母", "贝母", "瓜蒌", "瓜蒌皮", "瓜蒌子", "天花粉", "半夏", "白蔹", "白及"},
        "十八反：乌头（附子/川乌/草乌）反贝母、瓜蒌、半夏、白蔹、白及",
    ),
    (
        {"藜芦"},
        {
            "人参",
            "西洋参",
            "党参",
            "丹参",
            "玄参",
            "苦参",
            "沙参",
            "北沙参",
            "南沙参",
            "细辛",
            "白芍",
            "赤芍",
            "芍药",
        },
        "十八反：藜芦反诸参、细辛、芍药",
    ),
]

# 十九畏（课程通识）
_SHIJIU_WEI: list[tuple[set[str], set[str], str]] = [
    ({"硫黄"}, {"芒硝", "朴硝"}, "十九畏：硫黄畏朴硝"),
    ({"水银"}, {"砒霜", "信石"}, "十九畏：水银畏砒霜"),
    ({"狼毒"}, {"密陀僧"}, "十九畏：狼毒畏密陀僧"),
    ({"巴豆", "巴豆霜"}, {"牵牛子", "黑丑", "白丑"}, "十九畏：巴豆畏牵牛"),
    ({"丁香", "母丁香"}, {"郁金"}, "十九畏：丁香畏郁金"),
    ({"川乌", "草乌"}, {"犀角"}, "十九畏：川乌、草乌畏犀角"),
    ({"人参"}, {"五灵脂"}, "十九畏：人参畏五灵脂"),
    ({"肉桂", "官桂", "桂枝"}, {"赤石脂", "石脂"}, "十九畏：官桂畏石脂"),
    ({"芒硝", "牙硝", "朴硝"}, {"三棱"}, "十九畏：牙硝畏三棱"),
]

_COOL = {"大寒", "寒", "微寒", "凉"}
_WARM = {"热", "温", "微温"}


def _brief(h: Herb) -> dict[str, Any]:
    return {
        "id": h.id,
        "key": h.key,
        "name_zh": h.name_zh,
        "name_pinyin": display_pinyin(h.name_zh, h.name_pinyin),
        "category": h.category,
        "siqi": h.siqi,
        "wuwei": h.wuwei,
        "guijing": h.guijing,
        "shengjiang": h.shengjiang,
        "gongxiao": (h.gongxiao or "")[:120] or None,
        "peiwu_jinji": h.peiwu_jinji,
        "jinjizheng": h.jinjizheng,
        "anquan": h.anquan,
        "dosage_min": h.dosage_min,
        "dosage_max": h.dosage_max,
        "dosage_unit": h.dosage_unit,
    }


def _pair_in_sets(a: str, b: str, left: set[str], right: set[str]) -> bool:
    return (a in left and b in right) or (b in left and a in right)


def _classic_conflicts(names: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    seen: set[str] = set()
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            for left, right, rule in _SHIBA_FAN:
                if _pair_in_sets(a, b, left, right):
                    key = f"fan|{a}|{b}|{rule}"
                    if key not in seen:
                        seen.add(key)
                        hits.append(
                            {
                                "level": "danger",
                                "kind": "十八反",
                                "pair": [a, b],
                                "rule": rule,
                                "evidence": rule,
                            }
                        )
            for left, right, rule in _SHIJIU_WEI:
                if _pair_in_sets(a, b, left, right):
                    key = f"wei|{a}|{b}|{rule}"
                    if key not in seen:
                        seen.add(key)
                        hits.append(
                            {
                                "level": "warn",
                                "kind": "十九畏",
                                "pair": [a, b],
                                "rule": rule,
                                "evidence": rule,
                            }
                        )
    return hits


def _text_mentions(herbs: list[Herb]) -> list[dict[str, Any]]:
    """若甲药配伍禁忌条文点名乙药，记为库内互指警示。"""
    hits: list[dict[str, Any]] = []
    seen: set[str] = set()
    for i, a in enumerate(herbs):
        tip_a = (a.peiwu_jinji or "").strip()
        for j, b in enumerate(herbs):
            if i == j:
                continue
            tip = tip_a
            other = b.name_zh or ""
            if not tip or not other or other not in tip:
                continue
            key = "|".join(sorted([a.name_zh or "", other]))
            if key in seen:
                continue
            seen.add(key)
            kind = "不宜联用"
            level = "warn"
            if "十八反" in tip:
                kind, level = "十八反", "danger"
            elif "十九畏" in tip:
                kind, level = "十九畏", "warn"
            elif "不宜" in tip or "相反" in tip:
                kind, level = "不宜联用", "warn"
            elif "忌" in tip or "禁" in tip:
                kind, level = "证候/配伍禁忌", "info"
            # 截取含对方药名的短句
            evidence = tip
            for sep in ("。", "；", ";", "\n"):
                for part in tip.split(sep):
                    if other in part:
                        evidence = part.strip()
                        break
            hits.append(
                {
                    "level": level,
                    "kind": kind,
                    "pair": [a.name_zh, b.name_zh],
                    "rule": f"《本库》{a.name_zh}配伍禁忌条文提及{b.name_zh}",
                    "evidence": evidence[:160],
                }
            )
    return hits


def _shared_guijing(herbs: list[Herb]) -> list[str]:
    sets = [set(_split_multi(h.guijing)) for h in herbs if h.guijing]
    if not sets:
        return []
    common = sets[0]
    for s in sets[1:]:
        common &= s
    return sorted(common)


def _contrast_notes(herbs: list[Herb]) -> list[str]:
    notes: list[str] = []
    if len(herbs) < 2:
        if herbs:
            h = herbs[0]
            notes.append(
                f"已选「{h.name_zh}」。可再选 1–2 味，对照寒热、归经并校核十八反/十九畏。"
            )
        return notes

    siqis = [h.siqi for h in herbs if h.siqi]
    cool = [s for s in siqis if s in _COOL]
    warm = [s for s in siqis if s in _WARM]
    if cool and warm:
        notes.append(
            f"寒热对照：存在偏寒凉（{'/'.join(cool)}）与偏温热（{'/'.join(warm)}），"
            "经典中常见于「寒热并用」或制性纠偏，需结合主证理解，不可机械叠加。"
        )
    elif len(set(siqis)) == 1 and siqis:
        notes.append(f"四气相近（均为「{siqis[0]}」），合用时药性方向较一致，宜防偏性叠加。")

    shared = _shared_guijing(herbs)
    if shared:
        notes.append(
            f"共同归经：{'、'.join(shared)}。同经合用往往强化对该脏腑的作用趋向。"
        )
    else:
        notes.append("归经交集不明显，合用时更像多靶协同，宜明确主病所在脏腑。")

    cats = [h.category for h in herbs if h.category]
    if len(set(cats)) >= 2:
        notes.append(
            "功效分类不同（"
            + "；".join(f"{h.name_zh}·{h.category}" for h in herbs if h.category)
            + "），可对照君药主证与臣佐分工来理解配伍意图。"
        )
    return notes


def _find_shared_formulas(keys: list[str], limit: int = 12) -> list[dict[str, Any]]:
    if len(keys) < 1:
        return []
    key_set = set(keys)
    out: list[dict[str, Any]] = []
    for f in _load_formulas():
        comps = f.get("composition") or []
        by_key: dict[str, dict[str, Any]] = {}
        for item in comps:
            if not isinstance(item, dict):
                continue
            hk = item.get("herb_key")
            if not hk or hk not in key_set:
                continue
            role = (item.get("role") or "").strip().lower()
            by_key[hk] = {
                "herb_key": hk,
                "role": ROLE_ZH.get(role),
                "dosage": item.get("dosage"),
            }
        # 单味：出现即可；多味：须全部共现
        if len(keys) == 1:
            if keys[0] not in by_key:
                continue
        elif not key_set.issubset(by_key.keys()):
            continue
        out.append(
            {
                "key": f.get("key"),
                "name_zh": f.get("name_zh") or f.get("key"),
                "source": f.get("source") or f.get("source_zh"),
                "category": f.get("category") or f.get("subcategory"),
                "roles": [by_key[k] for k in keys if k in by_key],
            }
        )
        if len(out) >= limit:
            break
    return out


def _level_from_conflicts(conflicts: list[dict[str, Any]]) -> str:
    if any(c.get("level") == "danger" for c in conflicts):
        return "danger"
    if any(c.get("level") == "warn" for c in conflicts):
        return "warn"
    if any(c.get("level") == "info" for c in conflicts):
        return "info"
    return "ok"


def _teach(
    herbs: list[Herb],
    conflicts: list[dict[str, Any]],
    formulas: list[dict[str, Any]],
    notes: list[str],
) -> str:
    names = "、".join(h.name_zh for h in herbs)
    level = _level_from_conflicts(conflicts)
    parts: list[str] = []

    if level == "danger":
        rules = "；".join(dict.fromkeys(c.get("rule") or "" for c in conflicts if c.get("level") == "danger"))
        parts.append(f"选药「{names}」触发十八反类警示（{rules}）。学习上应记住相反组合，临床组方须回避或遵专门规范，本页仅作示意。")
    elif level == "warn":
        rules = "；".join(dict.fromkeys(c.get("rule") or "" for c in conflicts if c.get("level") in ("warn", "info")))
        parts.append(f"选药「{names}」存在十九畏或不宜联用提示（{rules}）。宜查阅原条文与证候禁忌，理解「畏」与「反」的差别。")
    else:
        parts.append(f"选药「{names}」在本库通识规则与互指条文中，未见十八反/十九畏命中。这不等于可以任意联用，仍须结合证候与用量。")

    parts.extend(notes[:3])

    if formulas:
        sample = "、".join(f.get("name_zh") or "" for f in formulas[:3])
        parts.append(f"经典方中可见共现示例：{sample}。可对照各方君臣角色，体会「为何同用」。")
    elif len(herbs) >= 2:
        parts.append("本库收录方剂中暂未找到同时含上述全部药材的方，可减少选药数或换药再试。")

    parts.append("说明：配伍工坊为课程学习示意，不构成诊疗或处方建议。")
    return "".join(parts)


def workshop_check(herbs: list[Herb]) -> dict[str, Any]:
    """对 1–3 味药做配伍校核。"""
    herbs = [h for h in herbs if h is not None][:3]
    names = [h.name_zh for h in herbs if h.name_zh]
    keys = [h.key for h in herbs if h.key]

    classic = _classic_conflicts(names)
    mentioned = _text_mentions(herbs)
    # 去重：同 pair+kind 保留一条
    conflicts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for c in classic + mentioned:
        pair = tuple(sorted(c.get("pair") or []))
        key = f"{c.get('kind')}|{pair}"
        if key in seen:
            continue
        seen.add(key)
        conflicts.append(c)

    notes = _contrast_notes(herbs)
    formulas = _find_shared_formulas(keys)
    level = _level_from_conflicts(conflicts)

    # 四气计数（供前端小条）
    siqi_counter = Counter(h.siqi for h in herbs if h.siqi)

    return {
        "disclaimer": "学习示意，非诊疗建议。十八反/十九畏按课程通识规则匹配，并辅以本库配伍禁忌互指。",
        "level": level,
        "herbs": [_brief(h) for h in herbs],
        "conflicts": conflicts,
        "contrast_notes": notes,
        "shared_guijing": _shared_guijing(herbs),
        "siqi_mix": dict(siqi_counter),
        "formulas": formulas,
        "teaching": _teach(herbs, conflicts, formulas, notes),
    }
