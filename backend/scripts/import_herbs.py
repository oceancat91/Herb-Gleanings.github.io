"""
将本草典开源 herbs.json 规范化后导入 SQLite。

数据来源：本草典 Bencaodian Editorial（CC BY-SA 4.0）
说明：正式出版物《中华本草》受版权保护，不可直接爬取全文。
本脚本使用同体系的开源本草数据集，字段覆盖四气、五味、归经、功效、主治、用量、炮制、禁忌等。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from sqlalchemy import delete

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Herb  # noqa: E402

RAW_PATH = ROOT / "data" / "herbs_raw.json"
EXTRA_PATH = ROOT / "data" / "herbs_extra.json"

NATURE_MAP = {
    "cold": "寒",
    "slightly_cold": "微寒",
    "very_cold": "大寒",
    "cool": "凉",
    "neutral": "平",
    "slightly_warm": "微温",
    "warm": "温",
    "hot": "热",
}

FLAVOR_MAP = {
    "sour": "酸",
    "bitter": "苦",
    "slightly_bitter": "微苦",
    "slightly bitter": "微苦",
    "sweet": "甘",
    "slightly_sweet": "微甘",
    "pungent": "辛",
    "slightly_pungent": "微辛",
    "acrid": "辛",
    "salty": "咸",
    "bland": "淡",
    "astringent": "涩",
}

# 按功效类别粗略推断升降沉浮（教材常见归类，非绝对）
SHENGJIANG_BY_CATEGORY = {
    "辛温解表药": "升",
    "辛凉解表药": "升",
    "清热泻火药": "沉",
    "清热燥湿药": "沉",
    "清热解毒药": "沉",
    "清热凉血药": "沉",
    "清虚热药": "沉",
    "泻下药": "沉",
    "攻下药": "沉",
    "润下药": "沉",
    "峻下逐水药": "沉",
    "祛风湿药": "升",
    "芳香化湿药": "升",
    "利水渗湿药": "沉",
    "温里药": "升",
    "理气药": "降",
    "消食药": "降",
    "驱虫药": "沉",
    "止血药": "沉",
    "活血化瘀药": "升",
    "化痰药": "降",
    "止咳平喘药": "降",
    "化痰止咳平喘药": "降",
    "安神药": "沉",
    "平肝息风药": "沉",
    "开窍药": "升",
    "补气药": "升",
    "补阳药": "升",
    "补血药": "升",
    "补阴药": "沉",
    "收涩药": "沉",
    "涌吐药": "升",
    "外用药": "浮",
}


def extract_guijing(description: str | None) -> str | None:
    if not description:
        return None
    m = re.search(r"归([^。；;，,\n]{1,40}?)经", description)
    if not m:
        return None
    raw = m.group(1)
    raw = raw.replace("与", "、").replace("和", "、").replace("及", "、")
    parts = re.split(r"[、，,/\s]+", raw)
    organs = []
    for p in parts:
        p = p.strip().replace("经", "")
        if not p:
            continue
        # 处理「心肺」「脾胃」连写
        if len(p) >= 2 and all(ch in "心肝脾肺肾胃胆膀胱小肠大肠心包三焦" for ch in p):
            known = ["膀胱", "小肠", "大肠", "心包", "三焦", "心", "肝", "脾", "肺", "肾", "胃", "胆"]
            rest = p
            while rest:
                matched = False
                for k in known:
                    if rest.startswith(k):
                        organs.append(k)
                        rest = rest[len(k) :]
                        matched = True
                        break
                if not matched:
                    organs.append(rest[0])
                    rest = rest[1:]
        else:
            organs.append(p)
    # 去重保序
    seen = set()
    ordered = []
    for o in organs:
        if o and o not in seen:
            seen.add(o)
            ordered.append(o)
    return "、".join(ordered) if ordered else None


def join_zh_list(items, key="zh") -> str | None:
    if not items:
        return None
    vals = []
    for it in items:
        if isinstance(it, dict) and it.get(key):
            vals.append(it[key])
        elif isinstance(it, str):
            vals.append(it)
    return "、".join(vals) if vals else None


def dumps(obj) -> str | None:
    if obj is None:
        return None
    return json.dumps(obj, ensure_ascii=False)


def normalize(raw: dict) -> dict:
    siqi_en = raw.get("nature")
    flavors_en = raw.get("flavors") or []

    wuwei_zh = [FLAVOR_MAP.get(f, f) for f in flavors_en]
    description = raw.get("description_zh") or raw.get("description_en")
    guijing = extract_guijing(description)
    category = raw.get("category")

    dosage = raw.get("dosage_range") or {}
    actions = raw.get("actions") or []
    indications = raw.get("indications") or []

    dosage_notes = dosage.get("notes")
    if not dosage_notes and (dosage.get("min") is not None or dosage.get("max") is not None):
        lo = dosage.get("min")
        hi = dosage.get("max")
        unit = dosage.get("unit") or "g"
        dosage_notes = f"一般煎服 {lo}–{hi} {unit}；具体用量须结合体质、配伍与炮制调整，有毒药另循专条。"

    return {
        "key": raw["key"],
        "slug": raw.get("slug") or raw["key"].replace("_", "-"),
        "name_zh": raw["name_zh"],
        "name_pinyin": raw.get("name_pinyin"),
        "name_en": raw.get("name_en"),
        "name_latin": raw.get("name_latin"),
        "category": category,
        "siqi": NATURE_MAP.get(siqi_en, siqi_en),
        "siqi_en": siqi_en,
        "wuwei": "、".join(wuwei_zh) if wuwei_zh else None,
        "wuwei_en": "、".join(flavors_en) if flavors_en else None,
        "guijing": guijing,
        "shengjiang": SHENGJIANG_BY_CATEGORY.get(category) if category else None,
        "gongxiao": join_zh_list(actions),
        "gongxiao_detail": dumps(actions),
        "zhuzhi": join_zh_list(indications),
        "zhuzhi_detail": dumps(indications),
        "peiwu_jinji": raw.get("contraindications_zh"),
        "dosage_min": dosage.get("min"),
        "dosage_max": dosage.get("max"),
        "dosage_unit": dosage.get("unit"),
        "dosage_notes": dosage_notes,
        "paozhi": dumps(raw.get("processing_methods")),
        "jinjizheng": raw.get("contraindications_zh"),
        "anquan": raw.get("safety_notes_zh"),
        "description": description,
        "pharmacology": dumps(raw.get("pharmacology")),
        "classical_refs": dumps(raw.get("classical_references")),
        "extra": dumps(
            {
                "pregnancy": raw.get("pregnancy"),
                "lactation": raw.get("lactation"),
                "pediatric": raw.get("pediatric"),
                "verification": raw.get("verification"),
                "description_en": raw.get("description_en"),
            }
        ),
        "wikidata_id": raw.get("wikidata_id"),
        "source": raw.get("_source_tag")
        or "本草典 Bencaodian Editorial / CC BY-SA 4.0",
    }


def main():
    if not RAW_PATH.exists():
        raise SystemExit(f"未找到原始数据：{RAW_PATH}\n请先运行 download_data.py")

    with RAW_PATH.open(encoding="utf-8") as f:
        rows = json.load(f)

    extra_path = ROOT / "data" / "herbs_extra.json"
    if extra_path.exists():
        extra = json.loads(extra_path.read_text(encoding="utf-8"))
        print(f"合并扩充数据：{len(extra)} 味 ← {extra_path.name}")
        rows = list(rows) + list(extra)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.execute(delete(Herb))
        db.commit()

        imported = 0
        seen_keys = set()
        seen_names = set()
        for raw in rows:
            if not raw.get("name_zh") or not raw.get("key"):
                continue
            if raw["key"] in seen_keys or raw["name_zh"] in seen_names:
                continue
            data = normalize(raw)
            db.add(Herb(**data))
            seen_keys.add(raw["key"])
            seen_names.add(raw["name_zh"])
            imported += 1

        db.commit()
        print(f"导入完成：{imported} 味药材 → {ROOT / 'data' / 'herbs.db'}")

        # 快速统计
        from collections import Counter
        from sqlalchemy import select

        herbs = db.scalars(select(Herb)).all()
        print("四气分布:", Counter(h.siqi for h in herbs if h.siqi))
        print("有归经记录:", sum(1 for h in herbs if h.guijing))
        print("有升降沉浮推断:", sum(1 for h in herbs if h.shengjiang))
        print("来源分布:", Counter(h.source for h in herbs))
    finally:
        db.close()


if __name__ == "__main__":
    main()
