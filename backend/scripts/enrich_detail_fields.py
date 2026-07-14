# -*- coding: utf-8 -*-
"""
为药材详情页补全统一格式的说明文字。
- 课程扩充条目：生成较完整的概述、用量说明、炮制、禁忌、安全、药理占位、典籍通识
- 本草典条目：仅补缺（如用量说明、空炮制等），不覆盖已有文献内容
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "herbs.db"
EXTRA_PATH = ROOT / "data" / "herbs_extra.json"

NATURE_ZH = {
    "cold": "寒",
    "slightly_cold": "微寒",
    "very_cold": "大寒",
    "cool": "凉",
    "neutral": "平",
    "slightly_warm": "微温",
    "warm": "温",
    "hot": "热",
}

FLAVOR_ZH = {
    "sour": "酸",
    "bitter": "苦",
    "slightly_bitter": "微苦",
    "sweet": "甘",
    "slightly_sweet": "微甘",
    "pungent": "辛",
    "slightly_pungent": "微辛",
    "acrid": "辛",
    "salty": "咸",
    "bland": "淡",
    "astringent": "涩",
}

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

CAT_CONTRA = {
    "泻下药": "孕妇、体虚及脾胃虚寒者忌用或慎用；峻下逐水、有毒药须严格炮制定量。",
    "峻下逐水药": "孕妇禁用；体虚者忌用；须依法炮制，不可过量。",
    "攻下药": "孕妇及正气不足者慎用。",
    "活血化瘀药": "孕妇慎用或禁用；月经过多、出血倾向者慎用。",
    "破血逐瘀": "孕妇禁用。",
    "温里药": "热证、阴虚火旺者忌用。",
    "辛温解表药": "风热表证及阴虚盗汗者慎用。",
    "辛凉解表药": "风寒表证不宜单用。",
    "清热泻火药": "脾胃虚寒、阳虚者慎用。",
    "清热燥湿药": "脾胃虚寒、津伤者慎用。",
    "清热解毒药": "虚寒证慎用。",
    "清热凉血药": "血虚有寒者慎用。",
    "祛风湿药": "阴虚血燥者慎用辛温燥烈之品。",
    "芳香化湿药": "阴虚津亏者慎用。",
    "利水渗湿药": "阴虚津伤、肾虚遗精者慎用。",
    "理气药": "气虚及阴虚火旺者慎用辛燥之品。",
    "消食药": "脾胃无积滞者不宜久服。",
    "驱虫药": "孕妇慎用；注意毒性与剂量。",
    "止血药": "瘀滞未尽者慎用纯涩之品；凉血止血药虚寒证慎用。",
    "化痰止咳平喘药": "咳嗽无痰或阴虚燥咳者，燥湿化痰药慎用。",
    "安神药": "按虚实选药；矿石类久服宜中病即止。",
    "平肝息风药": "脾虚慢惊及血虚者，寒凉息风药慎用。",
    "开窍药": "脱证忌用；孕妇慎用。",
    "补气药": "实证、热证慎用；湿盛胀满者慎用壅补。",
    "补阳药": "阴虚火旺者忌用。",
    "补血药": "湿浊中阻、脘腹胀满者慎用。",
    "补阴药": "脾胃虚寒、痰湿内盛者慎用。",
    "收涩药": "表邪未解、湿热痢疾初起者慎用。",
    "涌吐药": "体虚、孕妇、失血者忌用；中病即止。",
    "外用药": "严格控制剂量与用法；有毒外用药不可入口。",
}

CAT_PHARM_HINT = {
    "辛温解表药": "解热、发汗、抗炎及对呼吸道病原的体外研究等方向",
    "辛凉解表药": "解热、抗病毒、抗炎及咽喉黏膜保护等方向",
    "清热泻火药": "解热、抗炎、调节免疫等方向",
    "清热燥湿药": "抗菌、抗炎、调节肠道菌群等方向",
    "清热解毒药": "抗菌、抗病毒、抗炎解毒等方向",
    "清热凉血药": "抗炎、止血、微循环调节等方向",
    "清虚热药": "解热、免疫调节等方向",
    "泻下药": "导泻、肠蠕动及电解质代谢等方向",
    "祛风湿药": "抗炎镇痛、免疫调节等方向",
    "芳香化湿药": "胃肠动力、抗炎、芳香精油药理等方向",
    "利水渗湿药": "利尿、护肝利胆、代谢调节等方向",
    "温里药": "强心、扩血管、胃肠温煦样作用等方向",
    "理气药": "胃肠平滑肌双向调节、镇痛等方向",
    "消食药": "助消化酶活性、胃肠动力等方向",
    "驱虫药": "驱虫活性及毒性阈值研究等方向",
    "止血药": "凝血、血管收缩及抗纤溶等方向",
    "活血化瘀药": "抗血小板、改善微循环、抗血栓等方向",
    "化痰止咳平喘药": "祛痰、镇咳、平喘及气道炎症等方向",
    "安神药": "镇静催眠、抗焦虑及神经递质调节等方向",
    "平肝息风药": "抗惊厥、降压、神经保护等方向",
    "开窍药": "中枢兴奋/苏醒、脑循环等方向",
    "补气药": "免疫调节、抗疲劳、代谢支持等方向",
    "补阳药": "内分泌与能量代谢、抗衰老等方向",
    "补血药": "造血、铁代谢及抗贫血等方向",
    "补阴药": "抗氧化、黏膜保护及内分泌调节等方向",
    "收涩药": "收敛、止泻、止血及黏膜保护等方向",
    "涌吐药": "催吐反射及安全性评价等方向",
    "外用药": "局部抗菌、止痒、腐蚀/腐蚀收敛等方向",
}


def join_actions(actions) -> str:
    if not actions:
        return ""
    parts = []
    for a in actions:
        if isinstance(a, dict):
            parts.append(a.get("zh") or a.get("en") or "")
        else:
            parts.append(str(a))
    return "、".join(p for p in parts if p)


def join_inds(inds) -> str:
    return join_actions(inds)


def build_rich_description(name, category, siqi, wuwei, guijing, shengjiang, gongxiao, zhuzhi, source_tag=False) -> str:
    bits = [f"「{name}」"]
    if category:
        bits.append(f"属{category}")
    prop = []
    if siqi:
        prop.append(f"性{siqi}")
    if wuwei:
        prop.append(f"味{wuwei}")
    if guijing:
        prop.append(f"归{guijing}经")
    if shengjiang:
        prop.append(f"药势偏于{shengjiang}")
    if prop:
        bits.append("，".join(prop))
    if gongxiao:
        gx = "、".join(str(gongxiao).split("、")[:6])
        bits.append(f"功效以{gx}为主")
    if zhuzhi:
        zz = "、".join(str(zhuzhi).split("、")[:5])
        bits.append(f"临床多用于{zz}")
    text = "。".join(bits) + "。"
    if source_tag:
        text += "本条为课程可视化扩充数据，属性据中药学通识整理，详细条文见下列各栏；正式诊疗请以现行药典与执业医师意见为准。"
    else:
        text += "下列各栏按统一结构展开性味归经、功效主治、用量炮制与安全信息，便于对照阅读。"
    return text


def default_contra(category: str | None, existing: str | None) -> str:
    if existing and existing.strip():
        return existing.strip()
    if not category:
        return "孕妇、体质虚弱及过敏体质者应在医师指导下使用；本库记载供学习参考。"
    for k, v in CAT_CONTRA.items():
        if k in category:
            return v
    return f"属{category}，使用时须辨证选药；孕妇、小儿及慢性病史者应遵医嘱。"


def default_safety(category: str | None, existing: str | None, contra: str | None) -> str:
    if existing and existing.strip():
        return existing.strip()
    base = default_contra(category, contra)
    return (
        f"{base}"
        " 注意炮制规格与剂量上限，避免与不明来源饮片混用；出现不适立即停用并就医。"
        " 本提示为课程数据整理，不作个体化用药指导。"
    )


def default_dosage_notes(lo, hi, unit, existing) -> str | None:
    if existing and str(existing).strip():
        return str(existing).strip()
    if lo is None and hi is None:
        return "剂量因品种、炮制与病情而异，请以药典及医嘱为准。"
    unit = unit or "g"
    lo_s = "—" if lo is None else str(lo).rstrip("0").rstrip(".") if isinstance(lo, float) else str(lo)
    hi_s = "—" if hi is None else str(hi).rstrip("0").rstrip(".") if isinstance(hi, float) else str(hi)
    # simpler format
    def fmt(x):
        if x is None:
            return "—"
        if isinstance(x, float) and x == int(x):
            return str(int(x))
        return str(x)

    return f"一般煎服 {fmt(lo)}–{fmt(hi)} {unit}；具体用量须结合体质、配伍与炮制调整，有毒药另循专条。"


def default_paozhi(existing_json: str | None) -> str:
    if existing_json and existing_json.strip() not in ("", "null", "[]"):
        return existing_json
    return json.dumps(
        [
            {
                "name": "生用",
                "method": "拣净，洗净，润透切片或段，干燥后入汤剂",
                "effect": "保留本品味气与功效偏性，为常用基础炮制规格",
            },
            {
                "name": "随方炮制",
                "method": "按处方注明炒、炙、煅等法加工",
                "effect": "减毒增效或改变药性趋向，须依法炮制",
            },
        ],
        ensure_ascii=False,
    )


def default_pharmacology(category: str | None, name: str, existing: str | None) -> str:
    if existing and existing.strip() not in ("", "null", "{}", "[]"):
        return existing
    hint = "相关活性与安全性评价"
    if category:
        for k, v in CAT_PHARM_HINT.items():
            if k in category:
                hint = v
                break
    obj = {
        "summary": {
            "zh": (
                f"本库暂未收录「{name}」完整实验药理综述。"
                f"结合其功效分类「{category or '未分类'}」，"
                f"现代研究常见关注点包括：{hint}。"
                "以下为课程占位说明，便于各药详情页栏目对齐，不能替代专业文献。"
            )
        },
        "evidence_notes": "课程扩充/补缺条目的药理栏为分类提示，非系统评价。",
    }
    return json.dumps(obj, ensure_ascii=False)


def default_classical(name: str, gongxiao: str | None, zhuzhi: str | None, existing: str | None) -> str:
    if existing and existing.strip() not in ("", "null", "[]"):
        return existing
    gx = gongxiao or "功用见功效栏"
    zz = zhuzhi or "适应证见主治栏"
    obj = [
        {
            "text_key": "course_tongshi",
            "classification": "课程通识",
            "passage": (
                f"{name}为常用中药。教材通识多强调其{gx}，"
                f"用于{zz}。具体文字以历代本草及现行药典为准；本条为结构化学习摘要。"
            ),
        }
    ]
    return json.dumps(obj, ensure_ascii=False)


def enrich_extra_json():
    if not EXTRA_PATH.exists():
        return 0
    data = json.loads(EXTRA_PATH.read_text(encoding="utf-8"))
    n = 0
    for raw in data:
        name = raw["name_zh"]
        category = raw.get("category")
        siqi = NATURE_ZH.get(raw.get("nature"), raw.get("nature"))
        flavors = raw.get("flavors") or []
        wuwei = "、".join(FLAVOR_ZH.get(f, f) for f in flavors)
        # guijing from description
        desc0 = raw.get("description_zh") or ""
        m = re.search(r"归([^。；;]{1,40}?)经", desc0)
        guijing = m.group(1) if m else ""
        shengjiang = SHENGJIANG_BY_CATEGORY.get(category or "")
        gongxiao = join_actions(raw.get("actions"))
        zhuzhi = join_inds(raw.get("indications"))

        raw["description_zh"] = build_rich_description(
            name, category, siqi, wuwei, guijing, shengjiang, gongxiao, zhuzhi, source_tag=True
        )
        contra = default_contra(category, raw.get("contraindications_zh"))
        raw["contraindications_zh"] = contra
        raw["safety_notes_zh"] = default_safety(category, raw.get("safety_notes_zh"), contra)

        dr = raw.get("dosage_range") or {}
        notes = default_dosage_notes(dr.get("min"), dr.get("max"), dr.get("unit"), dr.get("notes"))
        if notes:
            dr["notes"] = notes
            raw["dosage_range"] = dr

        if not raw.get("processing_methods"):
            raw["processing_methods"] = json.loads(default_paozhi(None))

        if not raw.get("pharmacology"):
            raw["pharmacology"] = json.loads(default_pharmacology(category, name, None))

        if not raw.get("classical_references"):
            raw["classical_references"] = json.loads(
                default_classical(name, gongxiao, zhuzhi, None)
            )

        n += 1
    EXTRA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return n


def enrich_db():
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM herbs").fetchall()
    updated = 0
    for r in rows:
        d = dict(r)
        is_extra = "课程扩充" in (d.get("source") or "")
        name = d["name_zh"]
        category = d.get("category")
        desc = (d.get("description") or "").strip()

        if is_extra:
            d["description"] = build_rich_description(
                name,
                category,
                d.get("siqi"),
                d.get("wuwei"),
                d.get("guijing"),
                d.get("shengjiang"),
                d.get("gongxiao"),
                d.get("zhuzhi"),
                source_tag=True,
            )
        # 本草典原文概述一律保留，不做模板覆盖

        if not d.get("shengjiang") and category:
            d["shengjiang"] = SHENGJIANG_BY_CATEGORY.get(category)

        contra = default_contra(category, d.get("peiwu_jinji"))
        if is_extra or not (d.get("peiwu_jinji") or "").strip():
            d["peiwu_jinji"] = contra
        if is_extra or not (d.get("jinjizheng") or "").strip():
            d["jinjizheng"] = d.get("peiwu_jinji") or contra

        d["anquan"] = default_safety(category, d.get("anquan"), d.get("peiwu_jinji"))
        d["dosage_notes"] = default_dosage_notes(
            d.get("dosage_min"), d.get("dosage_max"), d.get("dosage_unit"), d.get("dosage_notes")
        )
        d["paozhi"] = default_paozhi(d.get("paozhi"))
        d["pharmacology"] = default_pharmacology(category, name, d.get("pharmacology"))
        d["classical_refs"] = default_classical(
            name, d.get("gongxiao"), d.get("zhuzhi"), d.get("classical_refs")
        )

        cur.execute(
            """
            UPDATE herbs SET
              description=?, shengjiang=?, peiwu_jinji=?, jinjizheng=?, anquan=?,
              dosage_notes=?, paozhi=?, pharmacology=?, classical_refs=?
            WHERE id=?
            """,
            (
                d["description"],
                d.get("shengjiang"),
                d.get("peiwu_jinji"),
                d.get("jinjizheng"),
                d.get("anquan"),
                d.get("dosage_notes"),
                d.get("paozhi"),
                d.get("pharmacology"),
                d.get("classical_refs"),
                d["id"],
            ),
        )
        updated += 1
    conn.commit()
    conn.close()
    return updated


def main():
    n1 = enrich_extra_json()
    print(f"已更新 herbs_extra.json：{n1} 条")
    n2 = enrich_db()
    print(f"已更新 herbs.db：{n2} 条")


if __name__ == "__main__":
    main()
