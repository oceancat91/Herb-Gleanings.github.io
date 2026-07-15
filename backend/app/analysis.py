# -*- coding: utf-8 -*-
"""本草属性交叉与覆盖率等分析聚合。"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .models import Herb

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FORMULAS_PATH = DATA_DIR / "formulas_raw.json"

SIQI_ORDER = ["大寒", "寒", "微寒", "凉", "平", "微温", "温", "热"]
WUWEI_ORDER = ["酸", "苦", "微苦", "甘", "微甘", "辛", "咸", "淡", "涩"]
GUIJING_ORDER = ["心", "肝", "脾", "肺", "肾", "胃", "胆", "膀胱", "大肠", "小肠", "心包", "三焦"]
SHENGJIANG_ORDER = ["升", "降", "沉", "浮"]

TOXIC_RE = re.compile(r"有大毒|大毒|有毒|小毒|剧毒")
PREG_RE = re.compile(
    r"孕妇(?:忌|禁|慎|不可|不宜)|妊娠(?:忌|禁|慎|期忌|期禁)|"
    r"孕期(?:忌|禁|慎)|忌孕|禁孕|堕胎"
)

GONGXIAO_KEYS = [
    "清热", "泻火", "解毒", "凉血", "活血", "化瘀", "补气", "补血", "养阴", "温阳",
    "利水", "祛湿", "化痰", "止咳", "安神", "平肝", "疏风", "解表", "止痛", "止血",
    "消食", "润肠", "收涩", "开窍", "驱虫",
]

ZHUZHI_KEYS = [
    # 表里外感 / 寒热
    "恶寒", "恶风", "发热", "高热", "潮热", "往来寒热", "五心烦热", "骨蒸",
    # 头面五官
    "头痛", "眩晕", "目赤", "目糊", "耳鸣", "牙痛", "口疮", "咽痛", "鼻塞", "流涕",
    # 心肺胸胁
    "咳嗽", "喘息", "哮喘", "痰多", "咯血", "胸闷", "心悸", "气短", "胁痛",
    # 脾胃肠
    "呕吐", "恶心", "呃逆", "嗳气", "纳呆", "腹胀", "腹痛", "腹泻", "泄泻", "便秘",
    "痢疾", "久痢", "便血", "积食", "伤食", "疳积",
    # 肝肾精血 / 二阴
    "黄疸", "水肿", "淋证", "尿频", "尿急", "尿血", "遗尿", "遗精", "阳痿",
    "带下", "痛经", "闭经", "崩漏", "月经不调", "产后", "乳少", "乳痈",
    # 肢体筋骨
    "风湿", "痹痛", "腰痛", "抽搐", "中风", "半身不遂",
    # 神志睡眠
    "失眠", "不寐", "多梦", "健忘", "惊悸", "虚烦", "小儿惊风",
    # 气血津液
    "乏力", "盗汗", "自汗", "口渴", "消渴", "吐血", "衄血",
    # 疮疡皮肤
    "痈肿", "疮疡", "疔疮", "丹毒", "湿疹", "瘙痒", "瘰疬", "瘿瘤", "癥瘕", "积聚",
    # 时疫及其他
    "疟疾", "霍乱",
]


def _split_multi(text: str | None) -> list[str]:
    if not text:
        return []
    parts = re.split(r"[、,，/；;]\s*", str(text))
    return [p.strip() for p in parts if p and p.strip()]


def _matrix(rows: list[str], cols: list[str], counter: dict[tuple[str, str], int]) -> dict[str, Any]:
    data = []
    for i, r in enumerate(rows):
        for j, c in enumerate(cols):
            v = counter.get((r, c), 0)
            if v:
                data.append([j, i, v])
    return {"rows": rows, "cols": cols, "data": data}


def _ordered_present(order: list[str], present: set[str]) -> list[str]:
    return [x for x in order if x in present] or sorted(present)


ROLE_ZH = {"jun": "君", "chen": "臣", "zuo": "佐", "shi": "使"}

# 典籍 text_key → 中文书名（课程通识）
CLASSICAL_TITLE_ZH: dict[str, str] = {
    "shen_nong_ben_cao_jing": "《神农本草经》",
    "ming_yi_bie_lu": "《名医别录》",
    "ben_cao_gang_mu": "《本草纲目》",
    "ben_cao_gang_mu_shi_yi": "《本草纲目拾遗》",
    "zheng_lei_ben_cao": "《证类本草》",
    "yao_xing_lun": "《药性论》",
    "ri_hua_zi_ben_cao": "《日华子本草》",
    "ben_cao_yan_yi": "《本草衍义》",
    "ben_cao_cong_xin": "《本草从新》",
    "ben_cao_zheng_yi": "《本草正义》",
    "ben_cao_shi_yi": "《本草拾遗》",
    "kai_bao_ben_cao": "《开宝本草》",
    "xin_xiu_ben_cao": "《新修本草》",
    "tang_ben_cao": "《唐本草》",
    "hai_yao_ben_cao": "《海药本草》",
    "shang_han_lun": "《伤寒论》",
    "jin_gui_yao_lue": "《金匮要略》",
    "huang_di_nei_jing": "《黄帝内经》",
    "wen_bing_tiao_bian": "《温病条辨》",
    "tai_ping_hui_min_he_ji_ju_fang": "《太平惠民和剂局方》",
    "yi_fang_ji_jie": "《医方集解》",
    "bin_hu_mai_xue": "《濒湖脉学》",
    "si_bu_yi_dian": "《四部医典》",
    "xian_dai_shi_yong_zhong_yao": "《现代实用中药》",
    "course_tongshi": "课程通识摘要",
}


def _classical_zh_name(raw: str | None) -> str | None:
    """把 text_key 或书名统一成中文呈现。"""
    if not raw:
        return None
    s = str(raw).strip()
    if not s:
        return None
    if s in CLASSICAL_TITLE_ZH:
        return CLASSICAL_TITLE_ZH[s]
    # 已是中文书名
    if any("\u4e00" <= ch <= "\u9fff" for ch in s):
        if not (s.startswith("《") and s.endswith("》")) and len(s) <= 20:
            # 短中文书名补书名号；过长条文不加
            if "《" not in s and "》" not in s and len(s) <= 12:
                return f"《{s}》"
        return s[:40]
    # snake_case → 尝试映射；未知则尽量可读
    key = s.lower().replace(" ", "_").replace("-", "_")
    if key in CLASSICAL_TITLE_ZH:
        return CLASSICAL_TITLE_ZH[key]
    return s[:40]


def _load_formulas() -> list[dict[str, Any]]:
    if not FORMULAS_PATH.exists():
        return []
    try:
        data = json.loads(FORMULAS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def build_formula_pairing(herbs: list[Herb]) -> dict[str, Any]:
    """基于经典方剂组成，统计药对共现、枢纽药与君臣佐使。"""
    key_to_zh = {h.key: h.name_zh for h in herbs if h.key and h.name_zh}
    formulas = _load_formulas()
    pair_count: Counter[tuple[str, str]] = Counter()
    herb_freq: Counter[str] = Counter()
    role_count: Counter[str] = Counter()
    formula_cat: Counter[str] = Counter()
    pair_formulas: dict[tuple[str, str], list[str]] = defaultdict(list)
    herb_roles: dict[str, Counter[str]] = defaultdict(Counter)
    # 角色中心配伍：某角色药材与同方其它药的共现
    role_pair: dict[str, Counter[tuple[str, str]]] = {r: Counter() for r in ("君", "臣", "佐", "使")}
    role_pair_formulas: dict[str, dict[tuple[str, str], list[str]]] = {
        r: defaultdict(list) for r in ("君", "臣", "佐", "使")
    }

    used_formulas = 0
    for f in formulas:
        comps = f.get("composition") or []
        present: list[tuple[str, str | None]] = []  # (key, role_zh|None)
        for item in comps:
            if not isinstance(item, dict):
                continue
            hk = item.get("herb_key")
            role = (item.get("role") or "").strip().lower()
            role_zh = ROLE_ZH.get(role)
            if role_zh:
                role_count[role_zh] += 1
            if hk and hk in key_to_zh:
                herb_freq[hk] += 1
                if role_zh:
                    herb_roles[hk][role_zh] += 1
                present.append((hk, role_zh))
        # 去重：同一药多条时合并，保留首次角色
        seen: set[str] = set()
        uniq: list[tuple[str, str | None]] = []
        for hk, role_zh in present:
            if hk in seen:
                continue
            seen.add(hk)
            uniq.append((hk, role_zh))
        if len(uniq) < 2:
            continue
        used_formulas += 1
        cat = f.get("category") or f.get("subcategory") or "未分类"
        formula_cat[str(cat)] += 1
        fname = f.get("name_zh") or f.get("key") or ""
        keys_only = [hk for hk, _ in uniq]

        for i, a in enumerate(keys_only):
            for b in keys_only[i + 1 :]:
                pair = (a, b) if a <= b else (b, a)
                pair_count[pair] += 1
                if fname and len(pair_formulas[pair]) < 5 and fname not in pair_formulas[pair]:
                    pair_formulas[pair].append(fname)

        # 角色中心：该角色药 ↔ 同方其它药
        for hk, role_zh in uniq:
            if not role_zh:
                continue
            for other, _ in uniq:
                if other == hk:
                    continue
                pair = (hk, other) if hk <= other else (other, hk)
                role_pair[role_zh][pair] += 1
                bucket = role_pair_formulas[role_zh][pair]
                if fname and len(bucket) < 4 and fname not in bucket:
                    bucket.append(fname)

    def _primary_role(k: str) -> str:
        ct = herb_roles.get(k)
        if not ct:
            return "未标"
        return ct.most_common(1)[0][0]

    def _build_net(
        edges: list[tuple[tuple[str, str], int]],
        formulas_map: dict[tuple[str, str], list[str]],
        max_edges: int = 70,
        min_v: int = 2,
    ) -> dict[str, Any]:
        picked = [(p, v) for p, v in edges if v >= min_v][:max_edges]
        if not picked and edges:
            picked = edges[: min(40, len(edges))]
        nkeys = sorted({k for (a, b), _ in picked for k in (a, b)})
        max_f = max((herb_freq[k] for k in nkeys), default=1)
        nodes = []
        for k in nkeys:
            if k not in key_to_zh:
                continue
            roles = dict(herb_roles.get(k) or {})
            primary = _primary_role(k)
            nodes.append(
                {
                    "name": key_to_zh[k],
                    "key": k,
                    "value": herb_freq[k],
                    "symbolSize": 10 + int(18 * herb_freq[k] / max_f),
                    "role": primary,
                    "roles": roles,
                    "category": primary,
                }
            )
        links = [
            {
                "source": key_to_zh[a],
                "target": key_to_zh[b],
                "value": v,
                "formulas": formulas_map.get((a, b), []),
            }
            for (a, b), v in picked
            if a in key_to_zh and b in key_to_zh
        ]
        return {"nodes": nodes, "links": links}

    top_pairs_raw = pair_count.most_common(40)
    all_net = _build_net(
        pair_count.most_common(120),
        pair_formulas,
        max_edges=70,
        min_v=2,
    )

    networks_by_role: dict[str, Any] = {"全部": all_net}
    for role in ("君", "臣", "佐", "使"):
        networks_by_role[role] = _build_net(
            role_pair[role].most_common(100),
            role_pair_formulas[role],
            max_edges=60,
            min_v=2,
        )

    top_pairs = [
        {
            "source": key_to_zh[a],
            "target": key_to_zh[b],
            "source_key": a,
            "target_key": b,
            "value": v,
            "formulas": pair_formulas.get((a, b), []),
        }
        for (a, b), v in top_pairs_raw[:15]
        if a in key_to_zh and b in key_to_zh
    ]

    hubs = [
        {
            "name": key_to_zh[k],
            "key": k,
            "value": v,
            "role": _primary_role(k),
        }
        for k, v in herb_freq.most_common(15)
        if k in key_to_zh
    ]

    return {
        "formula_count": len(formulas),
        "used_formulas": used_formulas,
        "network": all_net,
        "networks_by_role": networks_by_role,
        "top_pairs": top_pairs,
        "hubs": hubs,
        "roles": [{"name": k, "value": role_count[k]} for k in ["君", "臣", "佐", "使"] if role_count[k]],
        "formula_categories": [{"name": k, "value": v} for k, v in formula_cat.most_common(12)],
        "role_colors": {
            "君": "#B89082",
            "臣": "#C4B08A",
            "佐": "#8FA99A",
            "使": "#7A9EAF",
            "未标": "#A09888",
        },
    }


def _flag_toxic(h: Herb) -> bool:
    # 不用 dosage_notes：补全模板常含「有毒药另循专条」会造成假阳性
    blob = " ".join(
        filter(
            None,
            [
                h.anquan or "",
                h.peiwu_jinji or "",
                h.jinjizheng or "",
                h.description or "",
            ],
        )
    )
    blob = blob.replace("有毒药另循专条", "").replace("有毒药须严格炮制定量", "")
    return bool(TOXIC_RE.search(blob))


def _flag_pregnancy(h: Herb) -> bool:
    blob = " ".join(
        filter(
            None,
            [
                h.anquan or "",
                h.peiwu_jinji or "",
                h.jinjizheng or "",
                h.description or "",
            ],
        )
    )
    if PREG_RE.search(blob):
        return True
    raw = h.extra
    if not raw:
        return False
    try:
        obj = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        return False
    if not isinstance(obj, dict):
        return False
    preg = obj.get("pregnancy")
    if not preg:
        return False
    if isinstance(preg, str):
        return bool(preg.strip())
    if isinstance(preg, dict):
        cat = str(preg.get("category") or "").lower()
        if cat in ("caution", "contraindicated", "avoid", "forbidden", "慎用", "禁用", "忌用"):
            return True
        note = preg.get("note_zh") or preg.get("note_en") or preg.get("note") or ""
        return bool(str(note).strip())
    return False


def build_analysis(herbs: list[Herb]) -> dict[str, Any]:
    total = len(herbs)
    name_set = {h.name_zh for h in herbs if h.name_zh}
    # longer names first for matching in peiwu text
    names_sorted = sorted(name_set, key=len, reverse=True)

    siqi_wuwei: Counter[tuple[str, str]] = Counter()
    siqi_guijing: Counter[tuple[str, str]] = Counter()
    wuwei_guijing: Counter[tuple[str, str]] = Counter()
    category_siqi: Counter[tuple[str, str]] = Counter()
    category_shengjiang: Counter[tuple[str, str]] = Counter()
    shengjiang_count: Counter[str] = Counter()
    sankey_sw: Counter[tuple[str, str]] = Counter()
    sankey_wg: Counter[tuple[str, str]] = Counter()
    guijing_pair: Counter[tuple[str, str]] = Counter()
    gongxiao_kw = Counter()
    zhuzhi_kw = Counter()
    symptom_herbs: dict[str, list[dict[str, str]]] = defaultdict(list)

    dosage_by_cat: dict[str, list[float]] = defaultdict(list)
    mid_doses: list[float] = []

    missing = Counter()
    safety = Counter()
    peiwu_edge: Counter[tuple[str, str]] = Counter()

    risk_toxic_by_cat: Counter[str] = Counter()
    risk_preg_by_cat: Counter[str] = Counter()
    risk_total_by_cat: Counter[str] = Counter()
    risk_scatter: list[dict[str, Any]] = []
    toxic_total = 0
    preg_total = 0

    for h in herbs:
        if not h.siqi:
            missing["siqi"] += 1
        if not h.wuwei:
            missing["wuwei"] += 1
        if not h.guijing:
            missing["guijing"] += 1
        if not h.shengjiang:
            missing["shengjiang"] += 1
        if not h.category:
            missing["category"] += 1
        if h.dosage_min is None and h.dosage_max is None:
            missing["dosage"] += 1
        if not (h.peiwu_jinji or "").strip():
            missing["peiwu_jinji"] += 1
        if not (h.jinjizheng or "").strip():
            missing["jinjizheng"] += 1
        if not (h.anquan or "").strip():
            missing["anquan"] += 1
        if not (h.gongxiao or "").strip():
            missing["gongxiao"] += 1
        if not (h.zhuzhi or "").strip():
            missing["zhuzhi"] += 1

        if (h.peiwu_jinji or "").strip():
            safety["peiwu_jinji"] += 1
        if (h.jinjizheng or "").strip():
            safety["jinjizheng"] += 1
        if (h.anquan or "").strip():
            safety["anquan"] += 1

        tastes = _split_multi(h.wuwei)
        channels = _split_multi(h.guijing)

        if h.siqi:
            for w in tastes:
                siqi_wuwei[(h.siqi, w)] += 1
            for g in channels:
                siqi_guijing[(h.siqi, g)] += 1
            if h.category:
                category_siqi[(h.category, h.siqi)] += 1

        for w in tastes:
            for g in channels:
                wuwei_guijing[(w, g)] += 1

        if h.shengjiang:
            shengjiang_count[h.shengjiang] += 1
            if h.category:
                category_shengjiang[(h.category, h.shengjiang)] += 1

        # 桑基：四气 → 五味 → 归经（按标注共现计数）
        if h.siqi and tastes and channels:
            for w in tastes:
                sankey_sw[(h.siqi, w)] += 1
                for g in channels:
                    sankey_wg[(w, g)] += 1

        for i, a in enumerate(channels):
            for b in channels[i + 1 :]:
                pair = (a, b) if a <= b else (b, a)
                guijing_pair[pair] += 1

        gx = h.gongxiao or ""
        for k in GONGXIAO_KEYS:
            if k in gx:
                gongxiao_kw[k] += 1

        zz = h.zhuzhi or ""
        for k in ZHUZHI_KEYS:
            if k in zz:
                zhuzhi_kw[k] += 1
                if len(symptom_herbs[k]) < 16:
                    symptom_herbs[k].append({"name_zh": h.name_zh, "key": h.key})

        vals = [v for v in (h.dosage_min, h.dosage_max) if v is not None]
        mid = sum(vals) / len(vals) if vals else None
        if mid is not None:
            mid_doses.append(mid)
            cat = h.category or "未分类"
            dosage_by_cat[cat].append(mid)

        tip = (h.peiwu_jinji or "").strip()
        if tip and h.name_zh:
            for other in names_sorted:
                if other == h.name_zh:
                    continue
                if other in tip:
                    a, b = (h.name_zh, other) if h.name_zh <= other else (other, h.name_zh)
                    peiwu_edge[(a, b)] += 1

        cat = h.category or "未分类"
        toxic = _flag_toxic(h)
        preg = _flag_pregnancy(h)
        risk_total_by_cat[cat] += 1
        if toxic:
            risk_toxic_by_cat[cat] += 1
            toxic_total += 1
        if preg:
            risk_preg_by_cat[cat] += 1
            preg_total += 1
        if mid is not None:
            risk_scatter.append(
                {
                    "name": h.name_zh,
                    "key": h.key,
                    "category": cat,
                    "mid_dose": round(mid, 2),
                    "toxic": toxic,
                    "pregnancy": preg,
                }
            )

    # dosage high vs low by median
    dosage_siqi = {"high": Counter(), "low": Counter(), "median": None}
    if mid_doses:
        sorted_m = sorted(mid_doses)
        median = sorted_m[len(sorted_m) // 2]
        dosage_siqi["median"] = round(median, 2)
        for h in herbs:
            vals = [v for v in (h.dosage_min, h.dosage_max) if v is not None]
            if not vals or not h.siqi:
                continue
            mid = sum(vals) / len(vals)
            bucket = "high" if mid >= median else "low"
            dosage_siqi[bucket][h.siqi] += 1

    # top categories for stacked bar
    cat_counts = Counter(h.category for h in herbs if h.category)
    top_cats = [c for c, _ in cat_counts.most_common(10)]
    top_cats_risk = [c for c, _ in cat_counts.most_common(12)]

    dosage_cat_stats = []
    for cat, arr in sorted(dosage_by_cat.items(), key=lambda x: -len(x[1]))[:12]:
        arr = sorted(arr)
        dosage_cat_stats.append({
            "category": cat,
            "count": len(arr),
            "avg": round(sum(arr) / len(arr), 2),
            "min": round(arr[0], 2),
            "max": round(arr[-1], 2),
            "p25": round(arr[len(arr) // 4], 2),
            "p75": round(arr[(3 * len(arr)) // 4], 2),
        })

    # complete subset: has siqi + wuwei + guijing + category + dosage
    complete = [
        h for h in herbs
        if h.siqi and h.wuwei and h.guijing and h.category
        and (h.dosage_min is not None or h.dosage_max is not None)
    ]
    complete_siqi = Counter(h.siqi for h in complete if h.siqi)

    # peiwu graph top edges
    peiwu_links = [
        {"source": a, "target": b, "value": v}
        for (a, b), v in peiwu_edge.most_common(60)
    ]
    peiwu_nodes = sorted({n for e in peiwu_links for n in (e["source"], e["target"])})

    guijing_links = [
        {"source": a, "target": b, "value": v}
        for (a, b), v in guijing_pair.most_common(40)
    ]

    # classical refs titles if JSON list/dict
    classical = Counter()
    for h in herbs:
        raw = h.classical_refs
        if not raw:
            continue
        try:
            obj = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            continue
        if isinstance(obj, list):
            for item in obj:
                if isinstance(item, str):
                    name = _classical_zh_name(item)
                    if name:
                        classical[name] += 1
                elif isinstance(item, dict):
                    title = (
                        item.get("text_key")
                        or item.get("title")
                        or item.get("zh")
                        or item.get("name")
                        or item.get("book")
                    )
                    name = _classical_zh_name(title if title else None)
                    if name:
                        classical[name] += 1
        elif isinstance(obj, dict):
            for k in obj:
                name = _classical_zh_name(str(k))
                if name:
                    classical[name] += 1

    missing_rate = {
        k: {"missing": missing[k], "rate": round(missing[k] / total, 3) if total else 0}
        for k in [
            "siqi", "wuwei", "guijing", "shengjiang", "category",
            "dosage", "peiwu_jinji", "jinjizheng", "anquan", "gongxiao", "zhuzhi",
        ]
    }

    ww_rows = _ordered_present(WUWEI_ORDER, {r for r, _ in wuwei_guijing})
    ww_cols = _ordered_present(GUIJING_ORDER, {c for _, c in wuwei_guijing})

    sj_present = set(shengjiang_count) | {s for _, s in category_shengjiang}
    sj_axis = _ordered_present(SHENGJIANG_ORDER, sj_present)

    # sankey nodes/links
    sankey_nodes: list[dict[str, str]] = []
    sankey_seen: set[str] = set()

    def _add_node(name: str) -> None:
        if name not in sankey_seen:
            sankey_seen.add(name)
            sankey_nodes.append({"name": name})

    for (a, b), v in sankey_sw.items():
        if v:
            _add_node(a)
            _add_node(b)
    for (a, b), v in sankey_wg.items():
        if v:
            _add_node(a)
            _add_node(b)

    sankey_links = (
        [{"source": a, "target": b, "value": v} for (a, b), v in sankey_sw.most_common(80) if v]
        + [{"source": a, "target": b, "value": v} for (a, b), v in sankey_wg.most_common(100) if v]
    )

    risk_rows = []
    for cat in top_cats_risk:
        n = risk_total_by_cat.get(cat, 0) or 1
        tc = risk_toxic_by_cat.get(cat, 0)
        pc = risk_preg_by_cat.get(cat, 0)
        risk_rows.append(
            {
                "category": cat,
                "total": risk_total_by_cat.get(cat, 0),
                "toxic": tc,
                "pregnancy": pc,
                "toxic_rate": round(tc / n, 3),
                "pregnancy_rate": round(pc / n, 3),
            }
        )

    return {
        "total": total,
        "siqi_wuwei": _matrix(
            [s for s in SIQI_ORDER if any(siqi_wuwei.get((s, w), 0) for w in WUWEI_ORDER)]
            or list({r for r, _ in siqi_wuwei}),
            [w for w in WUWEI_ORDER if any(siqi_wuwei.get((s, w), 0) for s in SIQI_ORDER)]
            or list({c for _, c in siqi_wuwei}),
            siqi_wuwei,
        ),
        "siqi_guijing": _matrix(
            [s for s in SIQI_ORDER if any(siqi_guijing.get((s, g), 0) for g in GUIJING_ORDER)],
            [g for g in GUIJING_ORDER if any(siqi_guijing.get((s, g), 0) for s in SIQI_ORDER)],
            siqi_guijing,
        ),
        "wuwei_guijing": _matrix(ww_rows, ww_cols, wuwei_guijing),
        "category_siqi": {
            "categories": top_cats,
            "siqi": [s for s in SIQI_ORDER if any(category_siqi.get((c, s), 0) for c in top_cats)],
            "series": [
                {
                    "name": s,
                    "data": [category_siqi.get((c, s), 0) for c in top_cats],
                }
                for s in SIQI_ORDER
                if any(category_siqi.get((c, s), 0) for c in top_cats)
            ],
        },
        "category_shengjiang": {
            "categories": top_cats,
            "shengjiang": sj_axis,
            "series": [
                {
                    "name": s,
                    "data": [category_shengjiang.get((c, s), 0) for c in top_cats],
                }
                for s in sj_axis
            ],
            "totals": dict(shengjiang_count),
        },
        "sankey_siqi_wuwei_guijing": {
            "nodes": sankey_nodes,
            "links": sankey_links,
        },
        "risk_by_category": risk_rows,
        "risk_summary": {
            "toxic": toxic_total,
            "pregnancy": preg_total,
            "total": total,
            "toxic_rate": round(toxic_total / total, 3) if total else 0,
            "pregnancy_rate": round(preg_total / total, 3) if total else 0,
        },
        "risk_scatter": risk_scatter,
        "guijing_cooccur": guijing_links,
        "dosage_by_category": dosage_cat_stats,
        "dosage_siqi": {
            "median": dosage_siqi["median"],
            "high": dict(dosage_siqi["high"]),
            "low": dict(dosage_siqi["low"]),
        },
        "safety": {
            "total": total,
            "peiwu_jinji": safety["peiwu_jinji"],
            "jinjizheng": safety["jinjizheng"],
            "anquan": safety["anquan"],
        },
        "gongxiao_keywords": [{"name": k, "value": v} for k, v in gongxiao_kw.most_common(20)],
        "zhuzhi_keywords": [{"name": k, "value": v} for k, v in zhuzhi_kw.most_common(36)],
        "symptom_herbs": {k: symptom_herbs[k] for k, _ in zhuzhi_kw.most_common(28)},
        "classical_refs": [{"name": k, "value": v} for k, v in classical.most_common(15)],
        "peiwu_network": {"nodes": [{"name": n} for n in peiwu_nodes], "links": peiwu_links},
        "formula_pairing": build_formula_pairing(herbs),
        "missing": missing_rate,
        "complete_subset": {
            "count": len(complete),
            "rate": round(len(complete) / total, 3) if total else 0,
            "by_siqi": dict(complete_siqi),
            "all_by_siqi": dict(Counter(h.siqi for h in herbs if h.siqi)),
        },
    }
