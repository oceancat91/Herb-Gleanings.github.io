# -*- coding: utf-8 -*-
"""补录新中国当代代表方剂到 formulas_extra.json。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTRA = ROOT / "data" / "formulas_extra.json"
RAW = ROOT / "data" / "formulas_raw.json"

ROLE = {"君": "jun", "臣": "chen", "佐": "zuo", "使": "shi"}


def F(key, name, cat, principle, source, comps, desc=""):
    composition = [
        {
            "herb_key": hk,
            "role": ROLE.get(role_zh, "zuo"),
            "dosage": dosage,
            "explanation_zh": f"{role_zh}药",
        }
        for hk, role_zh, dosage in comps
    ]
    return {
        "key": key,
        "slug": key.replace("_", "-"),
        "name_zh": name,
        "category": cat,
        "source_text_key": source,
        "treatment_principle": {"zh": principle, "en": ""},
        "composition": composition,
        "preparation_zh": "水煎服或按成药说明服用。",
        "description_zh": desc or f"{name}：{principle}。",
        "verification": {"status": "course-sketch", "era": "dangdai"},
    }


NEW = [
    (
        "guan_xin_er_hao_fang", "冠心Ⅱ号方", "活血剂",
        "活血化瘀，行气止痛", "xin_zhongguo_yan_fang",
        [
            ("chuan_xiong", "君", "15g"), ("chi_shao", "臣", "15g"), ("hong_hua", "臣", "15g"),
            ("jiang_xiang", "佐", "15g"), ("dan_shen", "使", "30g"),
        ],
        "中国中医研究院西苑医院等研制，面向冠心病心绞痛的活血化瘀代表方，推动中药专科成方研究。",
    ),
    (
        "gong_wai_yun_er_hao_fang", "宫外孕Ⅱ号方", "活血剂",
        "活血化瘀，消癥杀胚", "xin_zhongguo_yan_fang",
        [
            ("dan_shen", "君", "15g"), ("chi_shao", "君", "15g"), ("tao_ren", "臣", "9g"),
            ("san_leng", "佐", "6g"), ("e_zhu", "佐", "6g"),
        ],
        "山西等地中西医结合治疗宫外孕的经验方，体现当代急症专科中的中药应用。",
    ),
    (
        "fu_fang_dan_shen_fang", "复方丹参方", "活血剂",
        "活血化瘀，理气止痛", "xin_zhongguo_yan_fang",
        [
            ("dan_shen", "君", "30g"), ("san_qi", "臣", "9g"), ("bing_pian", "使", "0.3g"),
        ],
        "当代心脑血管成药（滴丸、片剂等）的基础组方思路，丹参、三七配伍广泛应用。",
    ),
    (
        "shuang_huang_lian_fang", "双黄连方", "清热剂",
        "辛凉解表，清热解毒", "xin_zhongguo_yan_fang",
        [
            ("jin_yin_hua", "君", "15g"), ("huang_qin", "臣", "15g"), ("lian_qiao", "佐", "15g"),
        ],
        "金银花、黄芩、连翘配伍，当代清热解毒成药与外感热病临床常用骨架。",
    ),
    (
        "ban_lan_gen_chong_ji_fang", "板蓝根方", "清热剂",
        "清热解毒，凉血利咽", "xin_zhongguo_yan_fang",
        [("ban_lan_gen", "君", "30g")],
        "以板蓝根为主的当代常用清热解毒应用，广泛见于颗粒剂与家庭备药。",
    ),
]


def main():
    have = set()
    for path in (RAW, EXTRA):
        if path.exists():
            for f in json.loads(path.read_text(encoding="utf-8")):
                if isinstance(f, dict) and f.get("key"):
                    have.add(f["key"])
    extra = json.loads(EXTRA.read_text(encoding="utf-8")) if EXTRA.exists() else []
    if not isinstance(extra, list):
        extra = []
    # 把二仙汤出处保持为现代经验方（已在当代索引）
    added = 0
    for row in NEW:
        item = F(*row)
        if item["key"] in have:
            continue
        extra.append(item)
        have.add(item["key"])
        added += 1
        print("added", item["name_zh"])
    EXTRA.write_text(json.dumps(extra, ensure_ascii=False, indent=2), encoding="utf-8")
    print("done, added", added)


if __name__ == "__main__":
    main()
