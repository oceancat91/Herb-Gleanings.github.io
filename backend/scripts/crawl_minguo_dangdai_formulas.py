# -*- coding: utf-8 -*-
"""
扩充民国 / 当代方剂入库。

民国：解析维基文库《医学衷中参西录》医方卷（公有领域；作者张锡纯卒于 1933），
      提取方名与组成，写入 formulas_extra.json。
当代：补录新中国以来教材/专科常用验方与成药骨架方（course-sketch）。

同步：era_library.json、herbs.db classical_refs。
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT_DIR = DATA / "era_crawl"
EXTRA_PATH = DATA / "formulas_extra.json"
RAW_PATH = DATA / "formulas_raw.json"
ERA_LIBRARY_PATH = DATA / "era_library.json"
DB_PATH = DATA / "herbs.db"
WIKI_TXT = OUT_DIR / "zhong_zhong_can_xi_wikitext.txt"

ROLE = {"君": "jun", "臣": "chen", "佐": "zuo", "使": "shi"}

# 药名别称 → 库内 key（解析时优先）
HERB_ALIAS = {
    "生黄芪": "huang_qi", "黄芪": "huang_qi", "生箭芪": "huang_qi", "箭芪": "huang_qi",
    "生箭": "huang_qi", "生黄耆": "huang_qi", "黄耆": "huang_qi", "野台参": "ren_shen", "台参": "ren_shen",
    "人参": "ren_shen", "党参": "dang_shen", "潞党参": "dang_shen",
    "生山药": "shan_yao", "山药": "shan_yao", "薯蓣": "shan_yao",
    "生地黄": "sheng_di_huang", "大生地": "sheng_di_huang", "生地": "sheng_di_huang",
    "熟地黄": "shu_di_huang", "熟地": "shu_di_huang",
    "生龙骨": "long_gu", "龙骨": "long_gu", "生牡蛎": "mu_li", "牡蛎": "mu_li",
    "生赭石": "dai_zhe_shi", "赭石": "dai_zhe_shi", "代赭石": "dai_zhe_shi",
    "怀牛膝": "niu_xi", "牛膝": "niu_xi", "川牛膝": "chuan_niu_xi",
    "生杭芍": "bai_shao", "白芍": "bai_shao", "杭芍": "bai_shao",
    "山萸肉": "shan_zhu_yu", "萸肉": "shan_zhu_yu", "山茱萸": "shan_zhu_yu",
    "知母": "zhi_mu", "柴胡": "chai_hu", "桔梗": "jie_geng", "升麻": "sheng_ma",
    "玄参": "xuan_shen", "丹参": "dan_shen", "三棱": "san_leng", "莪术": "e_zhu",
    "当归": "dang_gui", "白术": "bai_zhu", "茯苓": "fu_ling", "甘草": "gan_cao",
    "天冬": "tian_dong", "麦冬": "mai_dong", "五味子": "wu_wei_zi",
    "牛蒡子": "niu_bang_zi", "连翘": "lian_qiao", "生石膏": "shi_gao", "石膏": "shi_gao",
    "蝉蜕": "chan_tui", "乳香": "ru_xiang", "没药": "mo_yao",
    "鸡内金": "ji_nei_jin", "生鸡内金": "ji_nei_jin", "天花粉": "tian_hua_fen",
    "葛根": "ge_gen", "枸杞": "gou_qi_zi", "枸杞子": "gou_qi_zi",
    "柏子仁": "bai_zi_ren", "酸枣仁": "suan_zao_ren", "远志": "yuan_zhi",
    "半夏": "ban_xia", "陈皮": "chen_pi", "厚朴": "hou_po", "枳实": "zhi_shi",
    "黄连": "huang_lian", "黄芩": "huang_qin", "黄柏": "huang_bai",
    "附子": "fu_zi", "干姜": "gan_jiang", "肉桂": "rou_gui", "桂枝": "gui_zhi",
    "桂枝尖": "gui_zhi", "麻黄": "ma_huang", "杏仁": "xing_ren",
    "桃仁": "tao_ren", "红花": "hong_hua", "赤芍": "chi_shao", "川芎": "chuan_xiong",
    "水蛭": "shui_zhi", "苏子": "zi_su_zi", "紫苏子": "zi_su_zi",
    "芒硝": "mang_xiao", "大黄": "da_huang", "瓜蒌": "gua_lou",
    "三七": "san_qi", "冰片": "bing_pian", "降香": "jiang_xiang",
    "金银花": "jin_yin_hua", "板蓝根": "ban_lan_gen", "青蒿": "qing_hao",
    "天麻": "tian_ma", "钩藤": "gou_teng", "石决明": "shi_jue_ming",
    "杜仲": "du_zhong", "桑寄生": "sang_ji_sheng", "夜交藤": "ye_jiao_teng",
    "茯神": "fu_shen", "益母草": "yi_mu_cao", "仙茅": "xian_mao",
    "淫羊藿": "yin_yang_huo", "巴戟天": "ba_ji_tian", "龟甲": "gui_jia",
    "鳖甲": "bie_jia", "牡蛎": "mu_li", "龙齿": "long_chi",
    "泽泻": "ze_xie", "车前子": "che_qian_zi", "木通": "mu_tong",
    "滑石": "hua_shi", "通草": "tong_cao", "竹叶": "dan_zhu_ye",
    "淡竹叶": "dan_zhu_ye", "芦根": "lu_gen", "白茅根": "bai_mao_gen",
    "藕节": "ou_jie", "侧柏叶": "ce_bai_ye", "小蓟": "xiao_ji",
    "蒲黄": "pu_huang", "五灵脂": "wu_ling_zhi", "延胡索": "yan_hu_suo",
    "香附": "xiang_fu", "乌药": "wu_yao", "沉香": "chen_xiang",
    "砂仁": "sha_ren", "豆蔻": "bai_dou_kou", "白豆蔻": "bai_dou_kou",
    "苍术": "cang_zhu", "独活": "du_huo", "羌活": "qiang_huo",
    "防风": "fang_feng", "白芷": "bai_zhi", "细辛": "xi_xin",
    "吴茱萸": "wu_zhu_yu", "小茴香": "xiao_hui_xiang",
    "肉苁蓉": "rou_cong_rong", "菟丝子": "tu_si_zi", "覆盆子": "fu_pen_zi",
    "金樱子": "jin_ying_zi", "芡实": "qian_shi", "莲子": "lian_zi",
    "薏苡仁": "yi_yi_ren", "冬瓜子": "dong_gua_zi", "桔梗": "jie_geng",
    "前胡": "qian_hu", "紫菀": "zi_wan", "款冬花": "kuan_dong_hua",
    "百部": "bai_bu", "白及": "bai_ji", "三七": "san_qi",
    "阿胶": "e_jiao", "鹿角胶": "lu_jiao_jiao", "龟板": "gui_jia",
    "生牡蛎": "mu_li", "煅龙骨": "long_gu", "煅牡蛎": "mu_li",
    "海螵蛸": "hai_piao_xiao", "茜草": "qian_cao", "棕榈炭": "zong_lv_tan",
    "五倍子": "wu_bei_zi", "诃子": "he_zi", "肉豆蔻": "rou_dou_kou",
    "补骨脂": "bu_gu_zhi", "益智仁": "yi_zhi_ren", "山楂": "shan_zha",
    "神曲": "shen_qu", "麦芽": "mai_ya", "莱菔子": "lai_fu_zi",
    "槟榔": "bing_lang", "使君子": "shi_jun_zi", "雷丸": "lei_wan",
    "茵陈": "yin_chen", "栀子": "zhi_zi", "龙胆": "long_dan_cao",
    "夏枯草": "xia_ku_cao", "决明子": "jue_ming_zi", "菊花": "ju_hua",
    "桑叶": "sang_ye", "薄荷": "bo_he", "荆芥": "jing_jie",
    "淡豆豉": "dan_dou_chi", "葱白": "cong_bai", "生姜": "sheng_jiang",
    "大枣": "da_zao", "粳米": "geng_mi", "饴糖": "yi_tang",
    "珍珠母": "zhen_zhu_mu", "磁石": "ci_shi", "朱砂": "zhu_sha",
    "琥珀": "hu_po", "石菖蒲": "shi_chang_pu", "郁金": "yu_jin",
    "麝香": "she_xiang", "牛黄": "niu_huang", "犀角": "xi_jiao",
    "羚羊角": "ling_yang_jiao", "地龙": "di_long", "全蝎": "quan_xie",
    "蜈蚣": "wu_gong", "僵蚕": "jiang_can", "白花蛇舌草": "bai_hua_she_she_cao",
    "半枝莲": "ban_zhi_lian", "白英": "bai_ying", "蛇莓": "she_mei",
}


def slugify(name: str) -> str:
    # 简单拼音式 key：用已有映射不够，改用哈希+可读前缀
    # 用常见方名手工映射优先，否则用序号
    return ""


KNOWN_KEYS = {
    "升陷汤": "sheng_xian_tang",
    "建瓴汤": "jian_ling_tang",
    "活络效灵丹": "huo_luo_xiao_ling_dan",
    "玉液汤": "yu_ye_tang",
    "理冲汤": "li_chong_tang",
    "固冲汤": "gu_chong_tang",
    "镇肝熄风汤": "zhen_gan_xi_feng_tang",
    "寿胎丸": "shou_tai_wan",
    "资生汤": "zi_sheng_tang",
    "参赭镇气汤": "shen_zhe_zhen_qi_tang",
    "来复汤": "lai_fu_tang",
    "安冲汤": "an_chong_tang",
    "理郁升陷汤": "li_yu_sheng_xian_tang",
    "回阳升陷汤": "hui_yang_sheng_xian_tang",
    "醒脾升陷汤": "xing_pi_sheng_xian_tang",
    "薯蓣纳气汤": "shu_yu_na_qi_tang",
    "滋培汤": "zi_pei_tang",
    "清金益气汤": "qing_jin_yi_qi_tang",
    "清金解毒汤": "qing_jin_jie_du_tang",
    "寒降汤": "han_jiang_tang",
    "温降汤": "wen_jiang_tang",
    "清降汤": "qing_jiang_tang",
    "秘红丹": "mi_hong_dan",
    "补络补管汤": "bu_luo_bu_guan_tang",
    "参麦汤": "shen_mai_tang_zxc",
    "醴泉饮": "li_quan_yin",
    "十全育真汤": "shi_quan_yu_zhen_tang",
    "一味薯蓣饮": "yi_wei_shu_yu_yin",
    "既济汤": "ji_ji_tang",
    "镇摄汤": "zhen_she_tang",
    "理饮汤": "li_yin_tang",
    "理痰汤": "li_tan_tang",
    "健脾化痰丸": "jian_pi_hua_tan_wan",
    "期颐饼": "qi_yi_bing",
    "安肺宁嗽丸": "an_fei_ning_sou_wan",
    "清凉华盖饮": "qing_liang_hua_gai_yin",
    "保元寒降汤": "bao_yuan_han_jiang_tang",
    "保元清降汤": "bao_yuan_qing_jiang_tang",
    "二鲜饮": "er_xian_yin_zxc",
    "三鲜饮": "san_xian_yin",
    "化血丹": "hua_xue_dan",
    "化瘀理膈丹": "hua_yu_li_ge_dan",
    "犹龙汤": "you_long_tang",
    "荡胸汤": "dang_xiong_tang",
    "曲直汤": "qu_zhi_tang",
    "培脾舒肝汤": "pei_pi_shu_gan_tang",
    "息贲汤": "xi_ben_tang",
    "硝菔通结汤": "xiao_fu_tong_jie_tang",
    "惠民丸": "hui_min_wan",
    "健胃汤": "jian_wei_tang_zxc",
    "燮理汤": "xie_li_tang",
    "鸡胵汤": "ji_zhi_tang",
    "一味包金丹": "yi_wei_bao_jin_dan",
    "金铃泻肝汤": "jin_ling_xie_gan_tang",
    "敦复汤": "dun_fu_tang",
    "加味麦门冬汤": "jia_wei_mai_men_dong_tang_zxc",
    "薯蓣半夏汤": "shu_yu_ban_xia_tang",
    "镇吐汤": "zhen_tu_tang",
    "干颓汤": "gan_tui_tang",
    "镇肝熄风汤": "zhen_gan_xi_feng_tang",
}


def load_herb_name_map() -> dict[str, str]:
    m = dict(HERB_ALIAS)
    if DB_PATH.exists():
        con = sqlite3.connect(str(DB_PATH))
        for key, name in con.execute("SELECT key, name_zh FROM herbs"):
            if name:
                m[name] = key
                # 去炮制前缀粗匹配
                for pref in ("生", "熟", "炙", "炒", "酒", "醋", "盐", "蜜"):
                    if name.startswith(pref) and len(name) > 1:
                        m.setdefault(name[1:], key)
        con.close()
    return m


def to_pinyin_key(name: str, idx: int) -> str:
    if name in KNOWN_KEYS:
        return KNOWN_KEYS[name]
    # 用 unicode 码位压缩成可读 slug
    code = "".join(f"{ord(c):x}" for c in name[:6])
    return f"zxc_{idx:03d}_{code}"


def parse_dose(raw: str) -> str:
    s = raw.strip()
    # 钱→约 3g 示意；分→0.3g；两→30g（课程示意）
    m = re.match(r"([一二三四五六七八九十两半]+)?\s*两", s)
    if m:
        return "30g"
    m = re.match(r"([一二三四五六七八九十]+)\s*钱\s*([半])?", s)
    if "钱半" in s or "钱一半" in s:
        return "4.5g"
    m = re.search(r"([一二三四五六七八九十]+)\s*钱", s)
    num_map = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    if m:
        n = num_map.get(m.group(1), 3)
        if "五分" in s or "钱五分" in s or "一钱五分" in s:
            return f"{n * 3 + 1.5:g}g" if n == 1 else f"{n * 3}g"
        return f"{n * 3}g"
    if "一钱五分" in s or "钱五分" in s:
        return "4.5g"
    if re.search(r"\d+\s*g", s, re.I):
        return re.search(r"\d+\s*g", s, re.I).group(0).replace(" ", "")
    return s[:12] or "适量"


def parse_composition_line(line: str, name_map: dict[str, str]) -> list[dict]:
    # 匹配：药名（剂量）
    comps = []
    for m in re.finditer(r"([\u4e00-\u9fff]{1,8})\s*[（(]([^）)]{1,20})[）)]", line):
        herb_zh = m.group(1).strip()
        dose_raw = m.group(2).strip()
        # 去掉括号内“捣细”等说明中的纯药名干扰
        if herb_zh in ("捣细", "去核", "去净核", "轧细", "炒", "捣"):
            continue
        key = name_map.get(herb_zh)
        if not key:
            # 去生/熟前缀再试
            for pref in ("生", "熟", "炙", "炒", "酒", "醋"):
                if herb_zh.startswith(pref) and herb_zh[1:] in name_map:
                    key = name_map[herb_zh[1:]]
                    break
        if not key:
            continue
        comps.append(
            {
                "herb_key": key,
                "role": "zuo",
                "dosage": parse_dose(dose_raw),
                "explanation_zh": herb_zh,
            }
        )
    # 君臣粗分：第一味君，其后前半臣后半佐
    if comps:
        comps[0]["role"] = "jun"
        if len(comps) > 2:
            mid = max(1, len(comps) // 2)
            for i in range(1, mid):
                comps[i]["role"] = "chen"
            comps[-1]["role"] = "shi"
        elif len(comps) == 2:
            comps[1]["role"] = "chen"
    return comps


def extract_zxc_formulas(text: str, name_map: dict[str, str], limit: int = 80) -> list[dict]:
    # 按 === N．方名 === 切块
    blocks = re.split(r"\n===\s*\d+[．.]\s*([^=\n]{1,20}?)\s*===\n", text)
    # blocks[0]=preamble, then name, body, name, body...
    out = []
    seen_names = set()
    idx = 0
    for i in range(1, len(blocks), 2):
        name = blocks[i].strip()
        body = blocks[i + 1] if i + 1 < len(blocks) else ""
        if not name or name in seen_names:
            continue
        # 排除非方剂
        if any(x in name for x in ("法", "论", "跋", "案", "穴", "点")):
            continue
        if not any(name.endswith(x) for x in ("汤", "饮", "丸", "丹", "散", "膏", "饼", "粥")):
            continue
        # 找组成行：含至少 2 个（）药量
        comps = []
        for line in body.splitlines()[:25]:
            line = line.strip()
            if line.count("（") + line.count("(") < 2:
                continue
            if line.startswith("{{") or line.startswith("[["):
                continue
            parsed = parse_composition_line(line, name_map)
            if len(parsed) >= 2:
                comps = parsed
                break
            if len(parsed) == 1 and name.startswith("一味"):
                comps = parsed
                break
        if not comps:
            continue
        seen_names.add(name)
        idx += 1
        key = to_pinyin_key(name, idx)
        # tip from first non-empty paragraph
        tip = ""
        for line in body.splitlines():
            line = line.strip()
            if line.startswith("治") and len(line) > 4:
                tip = line[:80]
                break
        out.append(
            {
                "key": key,
                "slug": key.replace("_", "-"),
                "name_zh": name,
                "category": guess_category(name, tip),
                "source_text_key": "yi_xue_zhong_zhong_can_xi_lu",
                "treatment_principle": {"zh": tip or f"{name}（张锡纯）", "en": ""},
                "composition": comps[:12],
                "preparation_zh": "水煎服。",
                "description_zh": tip or f"《医学衷中参西录》方：{name}。",
                "verification": {
                    "status": "wikisource-parse",
                    "source": "zh.wikisource.org 《医学衷中参西录》",
                    "license": "public-domain (author d.1933)",
                },
            }
        )
        if len(out) >= limit:
            break
    return out


def guess_category(name: str, tip: str) -> str:
    blob = name + tip
    if any(x in blob for x in ("升陷", "补气", "益气", "大气")):
        return "补益剂"
    if any(x in blob for x in ("熄风", "镇肝", "脑充血", "眩晕")):
        return "治风剂"
    if any(x in blob for x in ("活血", "化瘀", "癥", "瘀")):
        return "活血剂"
    if any(x in blob for x in ("止血", "吐血", "衄", "崩")):
        return "止血剂"
    if any(x in blob for x in ("痰", "咳", "喘", "肺")):
        return "祛痰剂"
    if any(x in blob for x in ("消渴", "阴虚", "劳热")):
        return "补益剂"
    if any(x in blob for x in ("解毒", "热")):
        return "清热剂"
    if any(x in blob for x in ("安神", "怔忡")):
        return "安神剂"
    if any(x in blob for x in ("固冲", "安冲", "涩")):
        return "固涩剂"
    return "补益剂"


def dangdai_sketches() -> list[dict]:
    def F(key, name, cat, principle, comps, desc):
        composition = [
            {"herb_key": hk, "role": ROLE.get(r, "zuo"), "dosage": d, "explanation_zh": f"{r}药"}
            for hk, r, d in comps
        ]
        return {
            "key": key,
            "slug": key.replace("_", "-"),
            "name_zh": name,
            "category": cat,
            "source_text_key": "xin_zhongguo_yan_fang",
            "treatment_principle": {"zh": principle, "en": ""},
            "composition": composition,
            "preparation_zh": "水煎服或按成药说明服用。",
            "description_zh": desc,
            "verification": {"status": "course-sketch", "era": "dangdai"},
        }

    rows = [
        ("guan_xin_er_hao_fang", "冠心Ⅱ号方", "活血剂", "活血化瘀，行气止痛",
         [("chuan_xiong", "君", "15g"), ("chi_shao", "臣", "15g"), ("hong_hua", "臣", "15g"),
          ("jiang_xiang", "佐", "15g"), ("dan_shen", "使", "30g")],
         "西苑医院等研制，冠心病心绞痛活血化瘀代表方。"),
        ("gong_wai_yun_er_hao_fang", "宫外孕Ⅱ号方", "活血剂", "活血化瘀，消癥杀胚",
         [("dan_shen", "君", "15g"), ("chi_shao", "君", "15g"), ("tao_ren", "臣", "9g"),
          ("san_leng", "佐", "6g"), ("e_zhu", "佐", "6g")],
         "中西医结合治疗宫外孕经验方。"),
        ("fu_fang_dan_shen_fang", "复方丹参方", "活血剂", "活血化瘀，理气止痛",
         [("dan_shen", "君", "30g"), ("san_qi", "臣", "9g"), ("bing_pian", "使", "0.3g")],
         "当代心脑成药基础组方。"),
        ("shuang_huang_lian_fang", "双黄连方", "清热剂", "辛凉解表，清热解毒",
         [("jin_yin_hua", "君", "15g"), ("huang_qin", "臣", "15g"), ("lian_qiao", "佐", "15g")],
         "当代清热解毒成药骨架。"),
        ("ban_lan_gen_chong_ji_fang", "板蓝根方", "清热剂", "清热解毒，凉血利咽",
         [("ban_lan_gen", "君", "30g")],
         "当代家庭常备清热解毒应用。"),
        ("qing_kai_ling_fang", "清开灵方", "清热剂", "清热解毒，镇静安神",
         [("niu_huang", "君", "0.5g"), ("yu_jin", "臣", "9g"), ("jin_yin_hua", "臣", "15g"),
          ("huang_qin", "佐", "12g"), ("zhi_zi", "佐", "9g"), ("ban_lan_gen", "使", "15g")],
         "安宫牛黄思路的当代改良制剂骨架，广泛用于热病神昏等。"),
        ("sheng_mai_yin_dangdai", "生脉饮（当代制剂）", "补益剂", "益气养阴，复脉固脱",
         [("ren_shen", "君", "9g"), ("mai_dong", "臣", "15g"), ("wu_wei_zi", "佐", "6g")],
         "生脉散成药化，当代气阴两虚、心血管疾病辅助常用。"),
        ("yu_ping_feng_kou_fu_ye", "玉屏风口服液方", "补益剂", "益气固表止汗",
         [("huang_qi", "君", "30g"), ("bai_zhu", "臣", "10g"), ("fang_feng", "佐", "10g")],
         "玉屏风散当代成药，用于表虚易感。"),
        ("liu_wei_di_huang_wan_dangdai", "六味地黄丸（当代成药）", "补益剂", "滋阴补肾",
         [("shu_di_huang", "君", "24g"), ("shan_zhu_yu", "臣", "12g"), ("shan_yao", "臣", "12g"),
          ("ze_xie", "佐", "9g"), ("mu_dan_pi", "佐", "9g"), ("fu_ling", "使", "9g")],
         "经典方成药化，当代肾阴虚调理常用。"),
        ("xiao_chai_hu_keliji", "小柴胡颗粒方", "和解剂", "和解少阳",
         [("chai_hu", "君", "24g"), ("huang_qin", "臣", "9g"), ("ban_xia", "佐", "9g"),
          ("ren_shen", "佐", "9g"), ("gan_cao", "使", "6g"), ("sheng_jiang", "使", "9g"), ("da_zao", "使", "4枚")],
         "经方成药化，当代外感少阳证常用。"),
        ("huo_xiang_zheng_qi_shui", "藿香正气方（当代）", "祛湿剂", "解表化湿，理气和中",
         [("huo_xiang", "君", "15g"), ("zi_su_ye", "臣", "9g"), ("bai_zhi", "臣", "9g"),
          ("ban_xia", "佐", "9g"), ("cang_zhu", "佐", "9g"), ("fu_ling", "使", "9g")],
         "藿香正气散成药（水/胶囊），当代暑湿感冒家庭常备。"),
        ("san_jiu_wei_tai_fang", "三九胃泰方", "消食剂", "消炎止痛，理气健胃",
         [("san_cha_ku", "君", "15g"), ("jiu_li_xiang", "臣", "12g"), ("bai_shao", "佐", "9g"),
          ("sheng_di_huang", "佐", "9g"), ("mu_xiang", "使", "6g")],
         "当代胃病成药代表之一（部分药味以近似药示意入库）。"),
        ("nao_xin_tong_fang", "脑心通方", "活血剂", "益气活血，化瘀通络",
         [("huang_qi", "君", "30g"), ("dang_gui", "臣", "12g"), ("chuan_xiong", "臣", "9g"),
          ("dan_shen", "佐", "15g"), ("di_long", "佐", "9g"), ("quan_xie", "使", "3g")],
         "当代心脑血管通络成药组方思路。"),
        ("xue_sai_tong_fang", "血塞通方", "活血剂", "活血祛瘀，通脉活络",
         [("san_qi", "君", "9g")],
         "三七总皂苷类制剂，当代心脑血管病常用。"),
        ("ge_gen_qin_lian_tang_dangdai", "葛根芩连汤（当代应用）", "清热剂", "解表清里",
         [("ge_gen", "君", "24g"), ("huang_qin", "臣", "9g"), ("huang_lian", "臣", "9g"), ("gan_cao", "使", "6g")],
         "经方在当代感染性腹泻等病中的再应用。"),
        ("yin_qiao_jie_du_pian_fang", "银翘解毒方", "解表剂", "辛凉解表，清热解毒",
         [("jin_yin_hua", "君", "15g"), ("lian_qiao", "君", "15g"), ("bo_he", "臣", "6g"),
          ("niu_bang_zi", "臣", "9g"), ("jing_jie", "佐", "6g"), ("gan_cao", "使", "6g")],
         "银翘散成药化，当代风热感冒常备。"),
        ("ban_xia_xie_xin_dangdai", "半夏泻心汤（当代应用）", "和解剂", "寒热平调，消痞散结",
         [("ban_xia", "君", "9g"), ("huang_qin", "臣", "9g"), ("huang_lian", "臣", "3g"),
          ("gan_jiang", "佐", "9g"), ("ren_shen", "佐", "9g"), ("gan_cao", "使", "9g")],
         "经方当代用于慢性胃炎、痞满等。"),
        ("bu_yang_huan_wu_dangdai", "补阳还五汤（当代应用）", "活血剂", "补气活血通络",
         [("huang_qi", "君", "60g"), ("dang_gui", "臣", "9g"), ("chi_shao", "臣", "9g"),
          ("di_long", "佐", "9g"), ("chuan_xiong", "佐", "6g"), ("tao_ren", "使", "6g"), ("hong_hua", "使", "6g")],
         "王清任方在当代中风康复中的广泛再应用。"),
        ("xue_fu_zhu_yu_dangdai", "血府逐瘀汤（当代应用）", "活血剂", "活血祛瘀，行气止痛",
         [("tao_ren", "君", "12g"), ("hong_hua", "君", "9g"), ("dang_gui", "臣", "9g"),
          ("sheng_di_huang", "臣", "9g"), ("chuan_xiong", "佐", "6g"), ("chai_hu", "使", "6g")],
         "当代胸痹、痛证活血化瘀常用。"),
        ("xiao_qing_long_dangdai", "小青龙汤（当代应用）", "解表剂", "解表散寒，温肺化饮",
         [("ma_huang", "君", "9g"), ("gui_zhi", "臣", "9g"), ("gan_jiang", "臣", "9g"),
          ("xi_xin", "佐", "3g"), ("ban_xia", "佐", "9g"), ("wu_wei_zi", "使", "3g")],
         "经方当代用于过敏性鼻炎、哮喘寒饮证等。"),
        ("ma_xing_shi_gan_dangdai", "麻杏石甘汤（当代应用）", "清热剂", "辛凉宣肺，清热平喘",
         [("ma_huang", "君", "9g"), ("shi_gao", "臣", "18g"), ("xing_ren", "佐", "9g"), ("gan_cao", "使", "6g")],
         "当代肺炎、喘息性支气管炎等热喘证常用。"),
        ("sang_ju_gan_mao_fang", "桑菊感冒方", "解表剂", "疏风清热，宣肺止咳",
         [("sang_ye", "君", "9g"), ("ju_hua", "君", "6g"), ("lian_qiao", "臣", "9g"),
          ("bo_he", "佐", "3g"), ("jie_geng", "佐", "6g"), ("xing_ren", "使", "6g")],
         "桑菊饮成药化，当代风热咳嗽常备。"),
        ("qi_ju_di_huang_dangdai", "杞菊地黄方", "补益剂", "滋肾养肝明目",
         [("gou_qi_zi", "君", "12g"), ("ju_hua", "君", "9g"), ("shu_di_huang", "臣", "24g"),
          ("shan_zhu_yu", "佐", "12g"), ("shan_yao", "佐", "12g"), ("fu_ling", "使", "9g")],
         "当代肝肾阴虚、目眩耳鸣成药常用。"),
        ("zhi_bai_di_huang_dangdai", "知柏地黄方", "清热剂", "滋阴降火",
         [("zhi_mu", "君", "9g"), ("huang_bai", "君", "9g"), ("shu_di_huang", "臣", "24g"),
          ("shan_zhu_yu", "佐", "12g"), ("ze_xie", "佐", "9g"), ("fu_ling", "使", "9g")],
         "当代阴虚火旺成药常用。"),
        ("gui_pi_wan_dangdai", "归脾丸（当代）", "补益剂", "益气补血，健脾养心",
         [("ren_shen", "君", "9g"), ("huang_qi", "君", "15g"), ("bai_zhu", "臣", "12g"),
          ("dang_gui", "臣", "9g"), ("suan_zao_ren", "佐", "12g"), ("long_yan_rou", "使", "12g")],
         "当代心脾两虚、失眠健忘成药常用。"),
        ("tian_wang_bu_xin_dangdai", "天王补心丹（当代）", "安神剂", "滋阴养血，补心安神",
         [("sheng_di_huang", "君", "30g"), ("tian_dong", "臣", "9g"), ("mai_dong", "臣", "9g"),
          ("suan_zao_ren", "佐", "9g"), ("dan_shen", "佐", "9g"), ("dang_gui", "使", "9g")],
         "当代阴虚失眠成药常用。"),
        ("wen_dan_tang_dangdai", "温胆汤（当代应用）", "祛痰剂", "理气化痰，和胃利胆",
         [("ban_xia", "君", "9g"), ("zhu_ru", "臣", "9g"), ("zhi_shi", "臣", "9g"),
          ("chen_pi", "佐", "9g"), ("fu_ling", "佐", "12g"), ("gan_cao", "使", "3g")],
         "当代痰热失眠、焦虑相关证常用。"),
        ("chai_hu_shu_gan_dangdai", "柴胡疏肝散（当代应用）", "理气剂", "疏肝行气，活血止痛",
         [("chai_hu", "君", "9g"), ("xiang_fu", "臣", "9g"), ("chuan_xiong", "臣", "9g"),
          ("chen_pi", "佐", "9g"), ("bai_shao", "佐", "9g"), ("gan_cao", "使", "3g")],
         "当代肝郁气滞、情志病证常用。"),
        ("xiao_yao_wan_dangdai", "逍遥丸（当代）", "和解剂", "疏肝健脾，养血调经",
         [("chai_hu", "君", "9g"), ("dang_gui", "臣", "9g"), ("bai_shao", "臣", "9g"),
          ("bai_zhu", "佐", "9g"), ("fu_ling", "佐", "9g"), ("gan_cao", "使", "6g")],
         "逍遥散成药化，当代妇科与情志病常用。"),
        ("si_jun_zi_dangdai", "四君子丸（当代）", "补益剂", "益气健脾",
         [("ren_shen", "君", "9g"), ("bai_zhu", "臣", "9g"), ("fu_ling", "佐", "9g"), ("gan_cao", "使", "6g")],
         "当代脾胃气虚成药基础方。"),
        ("si_wu_he_ji_dangdai", "四物颗粒方", "补益剂", "补血调血",
         [("shu_di_huang", "君", "15g"), ("dang_gui", "臣", "12g"), ("bai_shao", "佐", "12g"), ("chuan_xiong", "使", "9g")],
         "当代血虚调经成药常用。"),
        ("er_chen_wan_dangdai", "二陈丸（当代）", "祛痰剂", "燥湿化痰，理气和中",
         [("ban_xia", "君", "9g"), ("chen_pi", "臣", "9g"), ("fu_ling", "佐", "12g"), ("gan_cao", "使", "3g")],
         "当代痰湿证成药基础方。"),
        ("ping_wei_wan_dangdai", "平胃丸（当代）", "祛湿剂", "燥湿运脾，行气和胃",
         [("cang_zhu", "君", "12g"), ("hou_po", "臣", "9g"), ("chen_pi", "佐", "9g"), ("gan_cao", "使", "3g")],
         "当代湿滞脾胃成药常用。"),
        ("bao_he_wan_dangdai", "保和丸（当代）", "消食剂", "消食导滞，和胃",
         [("shan_zha", "君", "18g"), ("shen_qu", "臣", "12g"), ("ban_xia", "佐", "9g"),
          ("fu_ling", "佐", "9g"), ("chen_pi", "使", "6g"), ("lai_fu_zi", "使", "6g")],
         "当代食积成药常备。"),
        ("jian_pi_wan_dangdai", "健脾丸（当代）", "消食剂", "健脾和胃，消食止泻",
         [("bai_zhu", "君", "15g"), ("fu_ling", "臣", "12g"), ("ren_shen", "臣", "9g"),
          ("shan_zha", "佐", "9g"), ("shen_qu", "佐", "9g"), ("mai_ya", "使", "9g")],
         "当代脾虚食积成药常用。"),
        ("wu_ling_san_dangdai", "五苓散（当代应用）", "祛湿剂", "利水渗湿，温阳化气",
         [("ze_xie", "君", "15g"), ("fu_ling", "臣", "9g"), ("zhu_ling", "臣", "9g"),
          ("bai_zhu", "佐", "9g"), ("gui_zhi", "使", "6g")],
         "当代水肿、代谢相关水湿证常用。"),
        ("zhen_wu_tang_dangdai", "真武汤（当代应用）", "温里剂", "温阳利水",
         [("fu_zi", "君", "9g"), ("bai_zhu", "臣", "9g"), ("fu_ling", "臣", "12g"),
          ("bai_shao", "佐", "9g"), ("sheng_jiang", "使", "9g")],
         "当代心肾阳虚水肿等证常用。"),
        ("si_ni_tang_dangdai", "四逆汤（当代应用）", "温里剂", "回阳救逆",
         [("fu_zi", "君", "15g"), ("gan_jiang", "臣", "9g"), ("gan_cao", "使", "6g")],
         "当代危重阳虚证急救思路的方药基础。"),
        ("huang_lian_jie_du_dangdai", "黄连解毒汤（当代应用）", "清热剂", "泻火解毒",
         [("huang_lian", "君", "9g"), ("huang_qin", "臣", "6g"), ("huang_bai", "佐", "6g"), ("zhi_zi", "使", "9g")],
         "当代热毒证、部分感染相关证的经典清热骨架。"),
        ("long_dan_xie_gan_dangdai", "龙胆泻肝丸（当代）", "清热剂", "清肝胆，利湿热",
         [("long_dan_cao", "君", "6g"), ("huang_qin", "臣", "9g"), ("zhi_zi", "臣", "9g"),
          ("ze_xie", "佐", "12g"), ("dang_gui", "佐", "6g"), ("chai_hu", "使", "6g")],
         "当代肝胆湿热成药常用。"),
    ]
    # fix san_cha_ku / jiu_li_xiang - may not exist; remap for 三九胃泰
    fixed = []
    for row in rows:
        key, name, cat, prin, comps, desc = row
        # replace unknown herbs
        new_comps = []
        for hk, r, d in comps:
            if hk in ("san_cha_ku", "jiu_li_xiang"):
                continue
            new_comps.append((hk, r, d))
        if key == "san_jiu_wei_tai_fang":
            new_comps = [
                ("bai_shao", "君", "12g"), ("sheng_di_huang", "臣", "12g"),
                ("mu_xiang", "佐", "6g"), ("fu_ling", "佐", "9g"), ("gan_cao", "使", "3g"),
            ]
            desc = "当代胃病成药代表思路（示意组方）。"
        if len(new_comps) < 1:
            continue
        fixed.append(F(key, name, cat, prin, new_comps, desc))
    return fixed


def existing_keys() -> set[str]:
    keys: set[str] = set()
    for path in (RAW_PATH, EXTRA_PATH):
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for f in data if isinstance(data, list) else []:
            if isinstance(f, dict) and f.get("key"):
                keys.add(f["key"])
    return keys


def existing_names() -> set[str]:
    names: set[str] = set()
    for path in (RAW_PATH, EXTRA_PATH):
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for f in data if isinstance(data, list) else []:
            if isinstance(f, dict) and f.get("name_zh"):
                names.add(f["name_zh"])
    return names


def merge_extra(items: list[dict]) -> tuple[int, int]:
    extra = json.loads(EXTRA_PATH.read_text(encoding="utf-8")) if EXTRA_PATH.exists() else []
    if not isinstance(extra, list):
        extra = []
    by_key = {f.get("key"): i for i, f in enumerate(extra) if isinstance(f, dict) and f.get("key")}
    have = existing_keys()
    names = existing_names()
    added = skipped = 0
    for item in items:
        k = item.get("key")
        n = item.get("name_zh")
        if not k:
            continue
        if k in have or (n and n in names and k not in by_key):
            # 同名已存在则跳过（避免重复）
            if n in names:
                skipped += 1
                continue
        if k in by_key:
            skipped += 1
            continue
        extra.append(item)
        have.add(k)
        if n:
            names.add(n)
        added += 1
    EXTRA_PATH.write_text(json.dumps(extra, ensure_ascii=False, indent=2), encoding="utf-8")
    return added, skipped


def sync_herb_refs(formulas: list[dict]) -> int:
    if not DB_PATH.exists():
        return 0
    sys.path.insert(0, str(ROOT))
    try:
        from app.database import SessionLocal
        from app.models import Herb
    except Exception as e:
        print("skip db", e)
        return 0
    title_map = {
        "yi_xue_zhong_zhong_can_xi_lu": "《医学衷中参西录》",
        "xin_zhongguo_yan_fang": "新中国临床验方",
        "xian_dai_jing_yan_fang": "现代经验方",
        "za_bing_zheng_zhi_xin_yi": "《杂病证治新义》",
    }
    refs: dict[str, set[str]] = {}
    for f in formulas:
        title = title_map.get(f.get("source_text_key"), f.get("source_text_key") or "")
        for c in f.get("composition") or []:
            hk = c.get("herb_key")
            if hk and title:
                refs.setdefault(hk, set()).add(title)
    db = SessionLocal()
    n = 0
    try:
        for hk, titles in refs.items():
            herb = db.query(Herb).filter(Herb.key == hk).first()
            if not herb:
                continue
            try:
                cur = json.loads(herb.classical_refs) if herb.classical_refs else []
            except Exception:
                cur = []
            if not isinstance(cur, list):
                cur = []
            have = {i.get("name") for i in cur if isinstance(i, dict)}
            ch = False
            for t in titles:
                if t not in have:
                    cur.append({"name": t, "value": 1})
                    ch = True
            if ch:
                herb.classical_refs = json.dumps(cur, ensure_ascii=False)
                n += 1
        db.commit()
    finally:
        db.close()
    return n


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not WIKI_TXT.exists():
        raise SystemExit(f"缺少 {WIKI_TXT}，请先下载维基文库文本")

    name_map = load_herb_name_map()
    text = WIKI_TXT.read_text(encoding="utf-8")
    print("解析《医学衷中参西录》…")
    zxc = extract_zxc_formulas(text, name_map, limit=90)
    print(f"  解析得到 {len(zxc)} 首（含组成）")
    (OUT_DIR / "minguo_zxc_formulas.json").write_text(
        json.dumps(zxc, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("生成当代验方补录…")
    dangdai = dangdai_sketches()
    print(f"  当代补录 {len(dangdai)} 首")

    added, skipped = merge_extra(zxc + dangdai)
    print(f"写入 formulas_extra：新增 {added}，跳过 {skipped}")

    herb_n = sync_herb_refs(zxc + dangdai)
    print(f"herbs.db classical_refs 更新 {herb_n} 味")

    sys.path.insert(0, str(ROOT))
    from app.era_library import build_era_index, _load_era_library

    _load_era_library.cache_clear()
    for e in build_era_index():
        if e["id"] in ("minguo", "dangdai"):
            print(f"{e['dynasty']} 方剂 {e['formula_count']}")


if __name__ == "__main__":
    main()
