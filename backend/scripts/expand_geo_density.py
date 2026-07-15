# -*- coding: utf-8 -*-
"""扩充 herb_geo_density：尽量把库内药材关联到道地/主产省份（课程通识示意）。"""
from __future__ import annotations

import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "herbs.db"
OUT = ROOT / "data" / "herb_geo_density.json"

# 炮制/规格前缀，剥离后对齐基原药名
_PREFIXES = (
    "生", "炙", "蜜", "酒", "醋", "盐", "姜", "炒", "焦", "炭", "煅", "漂",
    "清炒", "麸炒", "土炒", "砂炒", "酒炒", "醋炒", "盐炒", "姜汁", "蜜炙",
    "酒炙", "醋炙", "盐炙", "姜炙", "制", "炮", "烫", "煨", "蒸", "煮",
    "鲜", "干", "净", "选", "去油", "去心",
)
_SUFFIXES = (
    "炭", "霜", "粉", "片", "丝", "仁", "肉", "皮", "根", "叶", "花", "子",
    "头", "尾", "身", "节", "梢", "须", "绒", "胶", "露", "油", "汁",
)

# 药名地理前缀 → 主产省
_NAME_PREFIX_PROV = [
    (re.compile(r"^川"), "四川"),
    (re.compile(r"^云"), "云南"),
    (re.compile(r"^滇"), "云南"),
    (re.compile(r"^黔"), "贵州"),
    (re.compile(r"^贵"), "贵州"),
    (re.compile(r"^广"), "广东"),
    (re.compile(r"^粤"), "广东"),
    (re.compile(r"^桂"), "广西"),
    (re.compile(r"^浙"), "浙江"),
    (re.compile(r"^杭"), "浙江"),
    (re.compile(r"^温"), "浙江"),
    (re.compile(r"^怀"), "河南"),
    (re.compile(r"^淮"), "河南"),
    (re.compile(r"^亳"), "安徽"),
    (re.compile(r"^宣"), "安徽"),
    (re.compile(r"^祁"), "河北"),
    (re.compile(r"^北"), "河北"),
    (re.compile(r"^关"), "吉林"),
    (re.compile(r"^辽"), "辽宁"),
    (re.compile(r"^东"), "吉林"),
    (re.compile(r"^西"), "陕西"),
    (re.compile(r"^秦"), "陕西"),
    (re.compile(r"^甘"), "甘肃"),
    (re.compile(r"^宁"), "宁夏"),
    (re.compile(r"^藏"), "西藏"),
    (re.compile(r"^台"), "台湾"),
    (re.compile(r"^建"), "福建"),
    (re.compile(r"^闽"), "福建"),
    (re.compile(r"^湘"), "湖南"),
    (re.compile(r"^鄂"), "湖北"),
    (re.compile(r"^苏"), "江苏"),
    (re.compile(r"^江"), "江苏"),
    (re.compile(r"^鲁"), "山东"),
    (re.compile(r"^晋"), "山西"),
    (re.compile(r"^蒙"), "内蒙古"),
    (re.compile(r"^新"), "新疆"),
    (re.compile(r"^海"), "海南"),
]

# 描述中省份关键词
_PROV_IN_TEXT = [
    "云南", "四川", "贵州", "广西", "广东", "吉林", "辽宁", "黑龙江",
    "内蒙古", "宁夏", "甘肃", "青海", "西藏", "新疆", "陕西", "山西",
    "河北", "河南", "山东", "安徽", "浙江", "江苏", "江西", "福建",
    "湖南", "湖北", "重庆", "上海", "北京", "天津", "海南", "台湾",
    "香港", "澳门",
]

# 道地/主产通识：省 → 药名列表（尽量覆盖库内常见名）
CURATED: dict[str, list[str]] = {
    "云南": [
        "三七", "天麻", "云木香", "木香", "黄连", "云连", "石斛", "铁皮石斛",
        "茯苓", "白及", "草果", "龙胆", "秦艽", "何首乌", "防己", "红花",
        "当归", "党参", "白术", "半夏", "重楼", "珠子参", "灯盏细辛", "灯盏花",
        "滇黄精", "黄精", "草血竭", "鸡血藤", "昆明山海棠", "雪上一枝蒿",
        "阳春砂", "砂仁", "益智", "胡椒", "儿茶", "诃子", "余甘子",
        "草蔻", "草豆蔻", "高良姜", "丁香", "肉豆蔻", "槟榔",
    ],
    "四川": [
        "川芎", "黄连", "附子", "川乌", "草乌", "川贝母", "贝母", "麦冬",
        "白芷", "白芍", "丹参", "姜黄", "郁金", "川牛膝", "牛膝", "续断",
        "川楝子", "厚朴", "黄柏", "杜仲", "独活", "天麻", "半夏", "白术",
        "泽泻", "枳壳", "枳实", "川木通", "木通", "川木香", "川椒", "花椒",
        "黄芩", "柴胡", "羌活", "藁本", "前胡", "桔梗", "紫菀", "款冬花",
        "冬虫夏草", "虫草", "川明参", "银耳", "天花粉", "瓜蒌", "瓜蒌皮",
        "瓜蒌子", "射干", "川楝皮", "乌梅", "使君子", "使君子仁",
        "大戟", "京大戟", "红大戟", "芫花", "续随子", "巴豆", "巴豆霜", "松子仁",
    ],
    "贵州": [
        "天麻", "杜仲", "吴茱萸", "石斛", "何首乌", "黄精", "白及", "淫羊藿",
        "仙灵脾", "天冬", "茯苓", "半夏", "续断", "天南星", "南星", "白附子",
        "天葵子", "金荞麦", "头花蓼", "吉祥草",
    ],
    "广西": [
        "肉桂", "桂枝", "八角", "八角茴香", "罗汉果", "鸡骨草", "山豆根",
        "两面针", "广金钱草", "金钱草", "葛根", "钩藤", "天花粉", "郁金",
        "莪术", "田七", "三七", "蛤蚧", "穿山甲", "水牛角", "珍珠",
        "石决明", "牡蛎", "海螵蛸", "乌贼骨", "瓦楞子",
    ],
    "广东": [
        "陈皮", "橘皮", "广陈皮", "砂仁", "阳春砂", "广藿香", "藿香",
        "化橘红", "橘红", "巴戟天", "金钱草", "佛手", "佛手柑", "益智",
        "高良姜", "草豆蔻", "胡椒", "丁香", "沉香", "伽南香", "降香",
        "檀香", "佩兰", "香薷", "紫苏", "紫苏叶", "苏梗", "苏子",
        "岗梅", "布渣叶", "溪黄草", "救必应", "五指毛桃",
    ],
    "吉林": [
        "人参", "红参", "生晒参", "鹿茸", "细辛", "五味子", "北五味子",
        "平贝母", "黄芪", "刺五加", "苍术", "龙胆", "防风", "桔梗",
        "升麻", "柴胡", "黄芩", "关黄柏", "黄柏",
    ],
    "辽宁": [
        "细辛", "五味子", "龙胆", "苍术", "升麻", "防风", "黄芩", "苦参",
        "白鲜皮", "地肤子", "蒺藜", "威灵仙", "秦艽",
    ],
    "黑龙江": [
        "刺五加", "防风", "黄芩", "龙胆", "苍术", "黄芪", "桔梗", "赤芍",
        "白芍", "柴胡", "秦艽", "升麻",
    ],
    "内蒙古": [
        "甘草", "黄芪", "麻黄", "锁阳", "肉苁蓉", "防风", "黄芩", "赤芍",
        "银柴胡", "柴胡", "枸杞子", "地骨皮", "冬虫夏草", "雪莲花",
        "苦豆子", "沙棘",
    ],
    "宁夏": [
        "枸杞子", "宁夏枸杞", "银柴胡", "甘草", "黄芪", "锁阳", "肉苁蓉",
        "地骨皮", "黄芩",
    ],
    "甘肃": [
        "当归", "党参", "黄芪", "大黄", "甘草", "秦艽", "羌活", "防风",
        "黄芩", "锁阳", "肉苁蓉", "岷当归", "纹党", "冬虫夏草", "红芪",
        "独活", "藁本", "升麻",
    ],
    "青海": [
        "大黄", "冬虫夏草", "秦艽", "羌活", "红景天", "雪莲花", "藏茵陈",
        "川贝母", "黄芪", "甘草",
    ],
    "西藏": [
        "冬虫夏草", "红景天", "藏红花", "西红花", "雪莲花", "诃子", "余甘子",
        "藏菖蒲", "藏木香", "川贝母", "胡黄连",
    ],
    "新疆": [
        "红花", "甘草", "肉苁蓉", "紫草", "枸杞子", "阿魏", "雪莲花",
        "罗布麻", "一枝蒿", "骆驼蓬", "天山雪莲",
    ],
    "陕西": [
        "丹参", "连翘", "黄芩", "杜仲", "山茱萸", "天麻", "猪苓", "茵陈",
        "柴胡", "防风", "秦艽", "羌活", "独活", "远志", "酸枣仁",
        "五味子", "淫羊藿", "仙灵脾",
    ],
    "山西": [
        "党参", "黄芪", "远志", "柴胡", "黄芩", "连翘", "酸枣仁", "槐花",
        "槐角", "地榆", "白芍", "防风", "秦艽",
    ],
    "河北": [
        "酸枣仁", "板蓝根", "大青叶", "青黛", "白芷", "知母", "黄芩",
        "柴胡", "蔓荆子", "紫菀", "祁白芷", "祁艾", "艾叶", "苍术",
        "北沙参", "防风", "槐米", "槐花",
    ],
    "河南": [
        "生地黄", "熟地黄", "地黄", "山药", "怀山药", "牛膝", "怀牛膝",
        "菊花", "怀菊", "金银花", "山茱萸", "白芷", "辛夷", "禹白附",
        "白附子", "天花粉", "瓜蒌", "连翘", "板蓝根", "艾叶", "牡丹皮",
        "丹皮", "白芍", "牵牛子", "黑丑", "白丑", "二丑", "番泻叶",
        "火麻仁", "大麻仁", "郁李仁", "郁李", "蜂蜜",
    ],
    "山东": [
        "金银花", "丹参", "全蝎", "北沙参", "瓜蒌", "白芍", "酸枣仁",
        "桔梗", "防风", "黄芩", "柴胡", "苍术", "半夏", "远志",
        "阿胶", "龟甲", "鳖甲", "海浮石", "牡蛎",
    ],
    "安徽": [
        "白芍", "牡丹皮", "丹皮", "木瓜", "宣木瓜", "菊花", "亳菊",
        "茯苓", "白术", "蕲蛇", "乌梢蛇", "蜈蚣", "僵蚕", "蝉蜕",
        "桔梗", "半夏", "天南星", "南沙参", "太子参",
    ],
    "浙江": [
        "浙贝母", "白芍", "菊花", "杭菊", "玄参", "麦冬", "白术", "郁金",
        "温郁金", "延胡索", "元胡", "乌药", "山茱萸", "白芷", "杭白芷",
        "前胡", "信前胡", "玄明粉", "芒硝", "海藻", "昆布", "瓦楞子",
    ],
    "江苏": [
        "薄荷", "苍术", "太子参", "泽泻", "荆芥", "白术", "芦根", "茅根",
        "白茅根", "藕节", "莲子", "荷叶", "芡实", "薏苡仁", "车前子",
    ],
    "江西": [
        "栀子", "枳壳", "枳实", "防己", "香薷", "车前子", "钩藤", "陈皮",
        "吴茱萸", "黄柏", "黄连", "白花蛇舌草", "半枝莲", "鱼腥草",
    ],
    "福建": [
        "泽泻", "薏苡仁", "厚朴", "乌梅", "莲子", "建莲", "青皮", "陈皮",
        "佛手", "砂仁", "草豆蔻", "海金沙", "石韦",
    ],
    "湖南": [
        "厚朴", "黄精", "吴茱萸", "玉竹", "前胡", "白术", "杜仲", "黄连",
        "黄柏", "栀子", "百合", "湘莲", "莲子", "金银花",
    ],
    "湖北": [
        "苍术", "半夏", "茯苓", "独活", "厚朴", "黄连", "续断", "射干",
        "贝母", "湖北贝母", "玄参", "麦冬", "白及",
    ],
    "重庆": [
        "黄连", "厚朴", "吴茱萸", "天麻", "杜仲", "川芎", "白芷", "半夏",
        "黄柏", "续断",
    ],
    "上海": ["薄荷", "藿香", "佩兰", "丝瓜络", "丝瓜"],
    "北京": ["黄芩", "柴胡", "金银花", "菊花", "益母草"],
    "天津": ["酸枣仁", "板蓝根", "大青叶", "柴胡"],
    "海南": [
        "槟榔", "益智", "砂仁", "胡椒", "高良姜", "沉香", "丁香", "肉豆蔻",
        "草豆蔻", "降香", "芦荟", "胖大海",
    ],
    "台湾": ["槟榔", "益智", "砂仁", "丁香", "胡椒"],
    "香港": [],
    "澳门": [],
}


def strip_paozhi(name: str) -> str:
    n = name.strip()
    changed = True
    while changed and len(n) >= 2:
        changed = False
        for p in _PREFIXES:
            if n.startswith(p) and len(n) - len(p) >= 1:
                n2 = n[len(p) :]
                if n2:
                    n = n2
                    changed = True
                    break
    # 常见「某某炭」保留基干
    for s in ("炭", "霜"):
        if n.endswith(s) and len(n) > len(s) + 0:
            base = n[: -len(s)]
            if len(base) >= 2:
                return base
    return n


def load_herbs() -> list[tuple[str, str | None]]:
    conn = sqlite3.connect(DB)
    rows = list(conn.execute("select name_zh, description from herbs"))
    conn.close()
    return [(r[0], r[1]) for r in rows]


def resolve_name(cand: str, name_set: set[str], by_base: dict[str, list[str]]) -> list[str]:
    """把通识名解析成库内实际药名（可一对多：含炮制品）。"""
    out: list[str] = []
    if cand in name_set:
        out.append(cand)
    # 同基干炮制品
    for full in by_base.get(cand, []):
        if full not in out:
            out.append(full)
    # 基干匹配：库内名剥离后等于 cand
    for full, bases in ((f, strip_paozhi(f)) for f in name_set):
        if bases == cand and full not in out:
            out.append(full)
        if full.startswith(cand) and len(full) <= len(cand) + 2 and full not in out:
            out.append(full)
    return out


def main() -> None:
    herbs = load_herbs()
    name_set = {n for n, _ in herbs}
    by_base: dict[str, list[str]] = defaultdict(list)
    for n, _ in herbs:
        by_base[strip_paozhi(n)].append(n)
        by_base[n].append(n)

    prov_herbs: dict[str, set[str]] = defaultdict(set)

    # 1) 通识表
    for prov, cands in CURATED.items():
        for cand in cands:
            for hit in resolve_name(cand, name_set, by_base):
                prov_herbs[prov].add(hit)

    # 2) 药名地理前缀
    for n, _ in herbs:
        for rx, prov in _NAME_PREFIX_PROV:
            if rx.search(n):
                # 「广」系列部分更偏广西
                if prov == "广东" and any(k in n for k in ("金钱草", "豆根", "山豆", "两面针", "鸡骨")):
                    prov_herbs["广西"].add(n)
                else:
                    prov_herbs[prov].add(n)
                break

    # 3) 描述中出现省份名
    for n, desc in herbs:
        if not desc:
            continue
        for prov in _PROV_IN_TEXT:
            if prov in desc:
                prov_herbs[prov].add(n)

    # 4) 别名/俗称补链
    ALIAS_LINKS = {
        "丹皮": "牡丹皮",
        "元胡": "延胡索",
        "仙灵脾": "淫羊藿",
        "乌贼骨": "海螵蛸",
        "二丑": "牵牛子",
        "黑丑": "牵牛子",
        "白丑": "牵牛子",
        "枣仁": "酸枣仁",
        "双花": "金银花",
        "银花": "金银花",
        "杭菊": "菊花",
        "亳菊": "菊花",
        "怀山药": "山药",
        "怀牛膝": "牛膝",
        "广陈皮": "陈皮",
        "苏叶": "紫苏叶",
    }
    # 若别名在库且正名已挂省，别名同挂
    name_to_provs: dict[str, set[str]] = defaultdict(set)
    for prov, hs in prov_herbs.items():
        for h in hs:
            name_to_provs[h].add(prov)
    for alias, canon in ALIAS_LINKS.items():
        if alias in name_set:
            for p in name_to_provs.get(canon, set()):
                prov_herbs[p].add(alias)
        if canon in name_set:
            for p in name_to_provs.get(alias, set()):
                prov_herbs[p].add(canon)

    # 5) 仍未入任何省的药：按功效大类给「主产示意」弱关联（避免空白）
    linked = set()
    for hs in prov_herbs.values():
        linked |= hs
    CATEGORY_FALLBACK = {
        # 仅对仍未挂靠者启用；多省弱分布，示意常见主产带
        "解表药": ["河北", "河南", "江苏", "浙江"],
        "清热药": ["河南", "河北", "四川", "云南"],
        "泻下药": ["甘肃", "青海", "四川", "河南"],
        "祛风湿药": ["四川", "陕西", "湖北", "贵州"],
        "化湿药": ["广东", "广西", "海南", "云南"],
        "利水渗湿药": ["云南", "福建", "安徽", "江苏"],
        "温里药": ["四川", "甘肃", "陕西"],
        "理气药": ["广东", "四川", "浙江", "江西"],
        "消食药": ["河南", "山东", "江苏"],
        "驱虫药": ["海南", "广东", "四川"],
        "止血药": ["山东", "河南", "浙江"],
        "活血化瘀药": ["四川", "云南", "河南", "山东"],
        "化痰止咳平喘药": ["四川", "浙江", "湖北", "吉林"],
        "安神药": ["河北", "山西", "陕西"],
        "平肝息风药": ["河南", "山东", "广东"],
        "开窍药": ["海南", "广西", "西藏"],
        "补虚药": ["甘肃", "吉林", "河南", "内蒙古", "宁夏"],
        "收涩药": ["山西", "陕西", "山东"],
        "涌吐药": ["河北", "河南"],
        "外用药": ["云南", "广西", "广东"],
    }
    conn = sqlite3.connect(DB)
    cat_rows = list(conn.execute("select name_zh, category from herbs"))
    conn.close()
    for n, cat in cat_rows:
        if n in linked or not cat:
            continue
        targets = None
        for k, provs in CATEGORY_FALLBACK.items():
            if k in cat or cat == k:
                targets = provs
                break
        if not targets:
            if "补" in cat:
                targets = CATEGORY_FALLBACK["补虚药"]
            elif "清" in cat:
                targets = CATEGORY_FALLBACK["清热药"]
            elif "解表" in cat:
                targets = CATEGORY_FALLBACK["解表药"]
            elif "活血" in cat:
                targets = CATEGORY_FALLBACK["活血化瘀药"]
            elif "化痰" in cat or "止咳" in cat or "平喘" in cat:
                targets = CATEGORY_FALLBACK["化痰止咳平喘药"]
            elif "利水" in cat or "渗湿" in cat:
                targets = CATEGORY_FALLBACK["利水渗湿药"]
            elif "安神" in cat:
                targets = CATEGORY_FALLBACK["安神药"]
            elif "平肝" in cat:
                targets = CATEGORY_FALLBACK["平肝息风药"]
            elif "理气" in cat:
                targets = CATEGORY_FALLBACK["理气药"]
            elif "化湿" in cat or "芳香" in cat:
                targets = CATEGORY_FALLBACK["化湿药"]
            elif "祛风湿" in cat:
                targets = CATEGORY_FALLBACK["祛风湿药"]
            elif "温里" in cat:
                targets = CATEGORY_FALLBACK["温里药"]
            elif "止血" in cat:
                targets = CATEGORY_FALLBACK["止血药"]
            elif "收涩" in cat:
                targets = CATEGORY_FALLBACK["收涩药"]
            elif "开窍" in cat:
                targets = CATEGORY_FALLBACK["开窍药"]
            elif "泻下" in cat:
                targets = CATEGORY_FALLBACK["泻下药"]
            elif "消食" in cat:
                targets = CATEGORY_FALLBACK["消食药"]
            elif "驱虫" in cat:
                targets = CATEGORY_FALLBACK["驱虫药"]
        if targets:
            for p in targets[:2]:
                prov_herbs[p].add(n)

    # 组装输出
    order = [
        "云南", "四川", "贵州", "广西", "广东", "吉林", "辽宁", "黑龙江",
        "内蒙古", "宁夏", "甘肃", "青海", "西藏", "新疆", "陕西", "山西",
        "河北", "河南", "山东", "安徽", "浙江", "江苏", "江西", "福建",
        "湖南", "湖北", "重庆", "上海", "北京", "天津", "海南", "台湾",
        "香港", "澳门",
    ]
    provinces = []
    all_linked: set[str] = set()
    for prov in order:
        herbs_list = sorted(prov_herbs.get(prov, set()), key=lambda x: x)
        all_linked |= set(herbs_list)
        provinces.append({
            "name": prov,
            "value": len(herbs_list),
            "samples": herbs_list[:5],
            "herbs": herbs_list,
        })

    data = {
        "_comment": "课程通识：道地/主产区疏密示意，非精确产量统计；含名称前缀、描述提及与分类弱关联",
        "unit": "关联道地/主产药材条目数（示意）",
        "provinces": provinces,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"herbs in db: {len(name_set)}")
    print(f"unique linked: {len(all_linked)} ({100 * len(all_linked) / max(1, len(name_set)):.1f}%)")
    print("top provinces:", sorted(((p["name"], p["value"]) for p in provinces), key=lambda x: -x[1])[:10])


if __name__ == "__main__":
    main()
