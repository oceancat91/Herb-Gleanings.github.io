# -*- coding: utf-8 -*-
"""
扩充药材库：在本草典 365 味之外，补充《中药学》常用缺味条目。
属性依据公开教材通识整理，供课程可视化使用；正式临床请以药典为准。
许可：与主数据一并按 CC BY-SA 4.0 署名使用（衍生数据集）。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "herbs_raw.json"
OUT = ROOT / "data" / "herbs_extra.json"


def slugify(name: str) -> str:
    # 简易拼音 stub：用 key 传入
    return name


def entry(
    key: str,
    name_zh: str,
    category: str,
    nature: str,
    flavors: list[str],
    guijing: str,
    actions: list[str],
    indications: list[str],
    dosage=(3, 10),
    contra: str | None = None,
    pinyin: str | None = None,
) -> dict:
    return {
        "key": key,
        "slug": key.replace("_", "-"),
        "name_zh": name_zh,
        "name_pinyin": pinyin or key.replace("_", " ").title(),
        "name_en": None,
        "name_latin": None,
        "category": category,
        "nature": nature,
        "flavors": flavors,
        "actions": [{"zh": a} for a in actions],
        "indications": [{"zh": i} for i in indications],
        "contraindications_zh": contra,
        "contraindications_en": None,
        "dosage_range": {"min": dosage[0], "max": dosage[1], "unit": "g"},
        "processing_methods": None,
        "safety_notes_zh": contra,
        "safety_notes_en": None,
        "classical_references": None,
        "description_zh": f"归{guijing}经。{'；'.join(actions)}。用于{'、'.join(indications)}。",
        "wikidata_id": None,
        "verification": {"status": "course_supplement"},
        "pharmacology": None,
        "pregnancy": None,
        "lactation": None,
        "pediatric": None,
        "description_en": None,
        "_source_tag": "课程扩充·中药学常用",
    }


# 教材常用、且尽量不与本草典 365 重复的条目（导入时仍会按中文名去重）
EXTRA: list[dict] = [
    entry("bai_qian", "白前", "化痰止咳平喘药", "slightly_warm", ["pungent", "sweet"], "肺", ["降气化痰", "止咳"], ["咳嗽痰多", "气喘"], (3, 10)),
    entry("zi_su_geng", "紫苏梗", "理气药", "warm", ["pungent"], "肺、脾", ["理气宽中", "止痛", "安胎"], ["胸闷呕吐", "胎动不安"], (5, 10)),
    entry("jing_jie_sui", "荆芥穗", "辛温解表药", "slightly_warm", ["pungent"], "肺、肝", ["祛风解表", "透疹", "止血"], ["外感风寒", "麻疹不透"], (3, 10)),
    entry("ju_hong", "橘红", "理气药", "warm", ["pungent", "bitter"], "肺、脾", ["理气化痰", "燥湿"], ["咳嗽痰多", "食积伤酒"], (3, 10)),
    entry("hua_ju_hong", "化橘红", "理气药", "warm", ["pungent", "bitter"], "肺、脾", ["理气化痰", "燥湿健脾"], ["咳嗽痰多", "脘腹胀痛"], (3, 6)),
    entry("xiang_yuan", "香橼", "理气药", "warm", ["pungent", "bitter", "sour"], "肝、脾、肺", ["疏肝理气", "和中化痰"], ["肝胃气滞", "咳嗽痰多"], (3, 10)),
    entry("jiang_xiang", "降香", "活血化瘀药", "warm", ["pungent"], "肝、脾", ["化瘀止血", "理气止痛"], ["吐衄崩漏", "胸胁疼痛"], (1, 3), "研末吞服宜小量"),
    entry("liu_ji_nu", "刘寄奴", "活血化瘀药", "warm", ["bitter"], "心、肝、脾", ["破血通经", "敛疮消肿"], ["经闭癥瘕", "跌打损伤"], (3, 10)),
    entry("yue_ji_hua", "月季花", "活血化瘀药", "warm", ["sweet"], "肝", ["活血调经", "疏肝解郁"], ["月经不调", "肝郁胀痛"], (3, 6)),
    entry("ling_xiao_hua", "凌霄花", "活血化瘀药", "cold", ["pungent"], "肝、心包", ["活血通经", "凉血祛风"], ["经闭癥瘕", "风疹瘙痒"], (5, 9), "孕妇慎用"),
    entry("zi_ran_tong", "自然铜", "活血化瘀药", "neutral", ["pungent"], "肝", ["散瘀止痛", "接骨疗伤"], ["跌打骨折", "瘀肿疼痛"], (3, 9)),
    entry("meng_chong", "虻虫", "活血化瘀药", "cold", ["bitter"], "肝", ["破血逐瘀", "消癥"], ["血瘀经闭", "癥瘕痞块"], (1, 1.5), "孕妇禁用"),
    entry("san_leng", "三棱", "活血化瘀药", "neutral", ["pungent", "bitter"], "肝、脾", ["破血行气", "消积止痛"], ["癥瘕痞块", "食积胀痛"], (5, 10), "孕妇禁用"),
    entry("e_zhu", "莪术", "活血化瘀药", "warm", ["pungent", "bitter"], "肝、脾", ["破血行气", "消积止痛"], ["气滞血瘀", "食积腹痛"], (6, 9), "孕妇禁用"),
    entry("shui_hong_hua_zi", "水红花子", "活血化瘀药", "cold", ["salty"], "肝、胃", ["散血消癥", "消积止痛"], ["癥瘕痞块", "食积胀痛"], (15, 30)),
    entry("xue_jie", "血竭", "活血化瘀药", "neutral", ["sweet", "salty"], "心、肝", ["活血定痛", "化瘀止血", "生肌敛疮"], ["跌打损伤", "外伤出血"], (1, 2), "研末"),
    entry("er_cha", "儿茶", "活血化瘀药", "cool", ["bitter", "astringent"], "肺", ["活血止痛", "止血生肌", "收湿敛疮", "清肺化痰"], ["跌打伤痛", "外伤出血", "疮疡"], (1, 3)),
    entry("shan_ci_gu", "山慈菇", "清热解毒药", "cool", ["sweet", "slightly_pungent"], "肝、脾", ["清热解毒", "化痰散结"], ["痈肿疔毒", "瘰疬痰核"], (3, 9)),
    entry("ban_bian_lian", "半边莲", "清热解毒药", "neutral", ["pungent"], "心、小肠、肺", ["清热解毒", "利尿消肿"], ["痈肿疔疮", "蛇虫咬伤", "腹水"], (5, 10)),
    entry("bai_lian", "白蔹", "清热解毒药", "cold", ["bitter"], "心、胃", ["清热解毒", "消痈散结", "敛疮生肌"], ["痈肿疮毒", "烫伤"], (5, 10)),
    entry("hua_rui_shi", "花蕊石", "止血药", "neutral", ["sour", "astringent"], "肝", ["化瘀止血"], ["咯血", "吐血", "外伤出血"], (5, 10)),
    entry("zao_xin_tu", "灶心土", "止血药", "warm", ["pungent"], "脾、胃", ["温中止血", "止呕止泻"], ["脾胃虚寒出血", "呕吐泄泻"], (15, 30)),
    entry("luo_han_guo", "罗汉果", "化痰止咳平喘药", "cool", ["sweet"], "肺、大肠", ["清热润肺", "利咽开音", "滑肠通便"], ["肺热咳嗽", "咽痛失音", "便秘"], (10, 15)),
    entry("pang_da_hai", "胖大海", "化痰止咳平喘药", "cold", ["sweet"], "肺、大肠", ["清热润肺", "利咽开音", "润肠通便"], ["肺热声哑", "咽喉肿痛", "便秘"], (2, 3)),
    entry("nuo_dao_gen", "糯稻根", "收涩药", "neutral", ["sweet"], "心、肝", ["敛阴止汗"], ["自汗", "盗汗"], (15, 30)),
    entry("chun_pi", "椿皮", "收涩药", "cold", ["bitter", "astringent"], "大肠、胃、肝", ["清热燥湿", "收涩止带", "止泻", "止血"], ["赤白带下", "久泻久痢", "崩漏"], (6, 9)),
    entry("shi_liu_pi", "石榴皮", "收涩药", "warm", ["sour", "astringent"], "大肠", ["涩肠止泻", "止血", "驱虫"], ["久泻久痢", "便血", "虫积"], (3, 9)),
    entry("fei_zi", "榧子", "驱虫药", "neutral", ["sweet"], "肺、胃、大肠", ["杀虫消积", "润肺止咳", "润肠通便"], ["虫积腹痛", "小儿疳积", "肠燥便秘"], (10, 15)),
    entry("wu_yi", "芜荑", "驱虫药", "warm", ["pungent", "bitter"], "脾、胃", ["杀虫", "消积"], ["虫积腹痛", "小儿疳积"], (3, 10)),
    entry("guan_zhong", "贯众", "清热解毒药", "cold", ["bitter"], "肝、脾", ["清热解毒", "凉血止血", "杀虫"], ["风热感冒", "温毒发斑", "虫积"], (5, 10)),
    entry("shu_qi", "蜀漆", "涌吐药", "cold", ["pungent", "bitter"], "肝、心、肺", ["祛痰截疟", "涌吐痰饮"], ["疟疾", "痰饮"], (3, 6), "有毒，慎用"),
    entry("lu_hui", "芦荟", "泻下药", "cold", ["bitter"], "肝、胃、大肠", ["泻下通便", "清肝", "杀虫"], ["便秘", "小儿疳积", "惊痫"], (2, 5), "孕妇忌服"),
    entry("ba_dou", "巴豆", "泻下药", "hot", ["pungent"], "胃、大肠、肺", ["峻下冷积", "逐水退肿", "祛痰利咽"], ["寒积便秘", "腹水", "喉痹"], (0.1, 0.3), "有大毒，孕妇禁用，严格炮制定量"),
    entry("qian_jin_zi", "千金子", "泻下药", "warm", ["pungent"], "肝、肾、大肠", ["泻下逐水", "破血消癥"], ["水肿胀满", "经闭"], (1, 2), "有毒，孕妇禁用"),
    entry("shang_lu", "商陆", "泻下药", "cold", ["bitter"], "肺、脾、肾、大肠", ["逐水消肿", "通利二便", "解毒散结"], ["水肿胀满", "二便不通"], (3, 9), "有毒，孕妇禁用"),
    entry("jing_da_ji", "京大戟", "泻下药", "cold", ["bitter"], "肺、脾、肾", ["泻水逐饮", "消肿散结"], ["水肿胀满", "痰饮积聚"], (1.5, 3), "有毒，反甘草"),
    entry("cong_bai", "葱白", "辛温解表药", "warm", ["pungent"], "肺、胃", ["发汗解表", "散寒通阳"], ["外感风寒", "阴寒腹痛"], (3, 10)),
    entry("da_suan", "大蒜", "涌吐药", "warm", ["pungent"], "脾、胃、肺", ["解毒杀虫", "消肿", "止痢"], ["痈肿疮疡", "疥癣", "痢疾"], (5, 10)),
    entry("ming_fan", "明矾", "外用药", "cold", ["sour", "astringent"], "肺、脾、肝、大肠", ["外用解毒杀虫", "燥湿止痒", "内服止血止泻", "清热消痰"], ["湿疹疥癣", "口舌生疮", "便血"], (0.6, 1.5)),
    entry("zao_fan", "皂矾", "外用药", "cool", ["sour", "salty"], "肝、脾", ["解毒燥湿", "杀虫补血"], ["疮疡疥癣", "黄肿病"], (0.8, 1.6)),
    entry("chan_su", "蟾酥", "开窍药", "warm", ["pungent", "sweet"], "心", ["解毒", "止痛", "开窍醒神"], ["痈疽疔疮", "咽喉肿痛", "神昏"], (0.015, 0.03), "有毒，孕妇慎用"),
    entry("ban_mao", "斑蝥", "外用药", "cold", ["pungent"], "肝、胃、肾", ["破血逐瘀", "散结消癥", "攻毒蚀疮"], ["癥瘕", "顽癣", "瘰疬"], (0.03, 0.06), "有大毒，内服慎用，孕妇禁用"),
    entry("xue_jie_hua", "血竭花", "活血化瘀药", "neutral", ["sweet", "salty"], "心、肝", ["活血定痛", "化瘀止血"], ["跌打伤痛", "外伤出血"], (1, 2)),
    entry("chi_xiao_dou", "赤小豆", "利水渗湿药", "neutral", ["sweet", "sour"], "心、小肠", ["利水消肿", "解毒排脓"], ["水肿胀满", "脚气", "痈肿"], (9, 30)),
    entry("dong_gua_zi", "冬瓜子", "利水渗湿药", "cool", ["sweet"], "肺、大肠", ["清热化痰", "排脓", "利湿"], ["痰热咳嗽", "肺痈肠痈"], (10, 15)),
    entry("yu_mi_xu", "玉米须", "利水渗湿药", "neutral", ["sweet"], "膀胱、肝、胆", ["利尿消肿", "平肝利胆"], ["水肿", "黄疸", "高血压"], (30, 60)),
    entry("ji_nei_jin_chao", "炒鸡内金", "消食药", "neutral", ["sweet"], "脾、胃、小肠、膀胱", ["健胃消食", "涩精止遗", "通淋化石"], ["食积不化", "遗精", "石淋"], (3, 10)),
    entry("shan_zha_chao", "焦山楂", "消食药", "warm", ["sour", "sweet"], "脾、胃、肝", ["消食化积", "行气散瘀"], ["肉食积滞", "泻痢腹痛"], (6, 12)),
    entry("mai_ya_chao", "焦麦芽", "消食药", "neutral", ["sweet"], "脾、胃、肝", ["行气消食", "健脾开胃", "回乳消胀"], ["米面薯芋积滞", "断乳"], (10, 15)),
    entry("gu_ya_chao", "焦谷芽", "消食药", "neutral", ["sweet"], "脾、胃", ["消食和中", "健脾开胃"], ["食积不消", "脾虚食少"], (10, 15)),
    entry("bai_dou_kou_ke", "豆蔻", "芳香化湿药", "warm", ["pungent"], "肺、脾、胃", ["化湿行气", "温中止呕"], ["湿浊中阻", "胃寒呕吐"], (3, 6)),
    entry("cao_kou_ren", "草豆蔻仁", "芳香化湿药", "warm", ["pungent"], "脾、胃", ["燥湿健脾", "温胃止呕"], ["寒湿中阻", "脘腹冷痛"], (3, 6)),
    entry("hou_po_hua", "厚朴花", "芳香化湿药", "warm", ["pungent"], "脾、胃", ["芳香化湿", "理气宽中"], ["湿阻气滞", "胸脘痞闷"], (3, 9)),
    entry("pei_lan_xian", "鲜佩兰", "芳香化湿药", "neutral", ["pungent"], "脾、胃、肺", ["化湿醒脾", "发表解暑"], ["湿阻中焦", "暑湿"], (10, 15)),
    entry("huo_xiang_geng", "藿香梗", "芳香化湿药", "slightly_warm", ["pungent"], "脾、胃、肺", ["化湿和中", "理气止呕"], ["湿阻呕吐", "胎气不安"], (5, 10)),
    entry("zi_su_zi", "紫苏子", "化痰止咳平喘药", "warm", ["pungent"], "肺、大肠", ["降气化痰", "止咳平喘", "润肠通便"], ["痰壅气逆", "肠燥便秘"], (5, 10)),
    entry("bai_bu_mi", "蜜百部", "化痰止咳平喘药", "slightly_warm", ["sweet", "bitter"], "肺", ["润肺下气止咳", "杀虫灭虱"], ["新久咳嗽", "百日咳", "肺痨"], (3, 9)),
    entry("zi_wan_mi", "蜜紫菀", "化痰止咳平喘药", "warm", ["pungent", "bitter"], "肺", ["润肺下气", "消痰止咳"], ["咳嗽气喘", "肺虚久咳"], (5, 10)),
    entry("kuan_dong_hua_mi", "蜜款冬花", "化痰止咳平喘药", "warm", ["pungent"], "肺", ["润肺下气", "化痰止咳"], ["咳嗽气喘", "肺虚久咳"], (5, 10)),
    entry("pi_pa_ye_mi", "蜜枇杷叶", "化痰止咳平喘药", "cool", ["bitter"], "肺、胃", ["清肺止咳", "降逆止呕"], ["肺热咳嗽", "胃热呕吐"], (6, 10)),
    entry("sang_ye_mi", "蜜桑叶", "辛凉解表药", "cold", ["sweet", "bitter"], "肺、肝", ["疏散风热", "清肺润燥", "清肝明目"], ["风热感冒", "肺燥咳嗽", "目赤"], (5, 10)),
    entry("ma_huang_rong", "炙麻黄", "辛温解表药", "warm", ["pungent", "slightly_bitter"], "肺、膀胱", ["发汗解表", "宣肺平喘", "利水消肿"], ["风寒表实", "喘咳", "水肿"], (2, 9)),
    entry("gui_zhi_mu", "桂枝加芍", "辛温解表药", "warm", ["pungent", "sweet"], "心、肺、膀胱", ["发汗解肌", "温通经脉", "助阳化气"], ["风寒表虚", "寒凝血滞"], (3, 10)),
    entry("fang_feng_chao", "炒防风", "辛温解表药", "warm", ["pungent", "sweet"], "膀胱、肝、脾", ["祛风解表", "胜湿止痛", "止痉"], ["外感风寒", "风湿痹痛", "破伤风"], (5, 10)),
    entry("qiang_huo", "川羌活", "辛温解表药", "warm", ["pungent", "bitter"], "膀胱、肾", ["解表散寒", "祛风胜湿", "止痛"], ["风寒夹湿", "项背强痛"], (3, 10)),
    entry("bai_zhi_chao", "炒白芷", "辛温解表药", "warm", ["pungent"], "肺、胃、大肠", ["解表散寒", "祛风止痛", "宣通鼻窍", "燥湿止带", "消肿排脓"], ["风寒感冒", "头痛", "鼻渊", "带下"], (3, 10)),
    entry("xin_yi_hua", "辛夷花", "辛温解表药", "warm", ["pungent"], "肺、胃", ["发散风寒", "通鼻窍"], ["风寒头痛", "鼻渊"], (3, 10)),
    entry("cang_er_zi_chao", "炒苍耳子", "辛温解表药", "warm", ["pungent", "bitter"], "肺", ["发散风寒", "通鼻窍", "祛风湿止痛"], ["鼻渊", "风寒头痛", "风湿痹痛"], (3, 9), "有小毒"),
    entry("bo_he_nao", "薄荷脑", "辛凉解表药", "cool", ["pungent"], "肺、肝", ["疏散风热", "清利头目", "利咽透疹", "疏肝行气"], ["风热感冒", "头痛目赤", "咽喉肿痛"], (0.03, 0.1)),
    entry("niu_bang_zi_chao", "炒牛蒡子", "辛凉解表药", "cold", ["pungent", "bitter"], "肺、胃", ["疏散风热", "宣肺祛痰", "利咽透疹", "解毒消肿"], ["风热感冒", "麻疹不透", "痈肿疮毒"], (6, 12)),
    entry("chan_tui_chao", "炒蝉蜕", "辛凉解表药", "cold", ["sweet"], "肺、肝", ["疏散风热", "利咽开音", "透疹", "明目退翳", "息风止痉"], ["风热感冒", "咽痛音哑", "麻疹", "惊痫"], (3, 6)),
    entry("sang_ye_sheng", "霜桑叶", "辛凉解表药", "cold", ["sweet", "bitter"], "肺、肝", ["疏散风热", "清肺润燥", "清肝明目"], ["风热感冒", "肺燥干咳", "目赤昏花"], (5, 10)),
    entry("ju_hua_huang", "黄菊花", "辛凉解表药", "cool", ["pungent", "sweet", "bitter"], "肺、肝", ["疏散风热", "平肝明目", "清热解毒"], ["风热感冒", "目赤昏花", "疮痈"], (5, 10)),
    entry("man_jing_zi_chao", "炒蔓荆子", "辛凉解表药", "cool", ["pungent", "bitter"], "膀胱、肝、胃", ["疏散风热", "清利头目"], ["风热感冒", "头痛目赤"], (5, 10)),
    entry("chai_hu_cu", "醋柴胡", "辛凉解表药", "cool", ["pungent", "bitter"], "肝、胆、肺", ["疏散退热", "疏肝解郁", "升举阳气"], ["少阳证", "肝郁气滞", "气虚下陷"], (3, 10)),
    entry("sheng_ma_zhi", "升麻炭", "辛凉解表药", "cool", ["pungent", "sweet"], "肺、脾、胃、大肠", ["发表透疹", "清热解毒", "升举阳气"], ["麻疹不透", "齿痛口疮", "中气下陷"], (3, 9)),
    entry("ge_gen_chao", "煨葛根", "辛凉解表药", "cool", ["sweet", "pungent"], "脾、胃、肺", ["解肌退热", "透疹", "生津止渴", "升阳止泻"], ["外感发热", "麻疹", "热病口渴", "脾虚泄泻"], (10, 15)),
    entry("dan_dou_chi", "香豆豉", "辛凉解表药", "cool", ["pungent", "sweet", "slightly_bitter"], "肺、胃", ["解表", "除烦", "宣发郁热"], ["外感发热", "心烦不眠"], (6, 12)),
    entry("shi_gao_sheng", "生石膏", "清热泻火药", "very_cold", ["sweet", "pungent"], "肺、胃", ["清热泻火", "除烦止渴"], ["气分热盛", "肺热喘咳", "胃火牙痛"], (15, 60)),
    entry("shi_gao_duan", "煅石膏", "清热泻火药", "cold", ["sweet", "pungent", "astringent"], "肺、胃", ["收湿", "生肌", "敛疮", "止血"], ["溃疡不敛", "湿疹", "水火烫伤"], (15, 30)),
    entry("zhi_mu_yan", "盐知母", "清热泻火药", "cold", ["bitter", "sweet"], "肺、胃、肾", ["清热泻火", "滋阴润燥"], ["热病烦渴", "肺热燥咳", "骨蒸潮热"], (6, 12)),
    entry("lu_gen_xian", "鲜芦根", "清热泻火药", "cold", ["sweet"], "肺、胃", ["清热泻火", "生津止渴", "除烦", "止呕", "利尿"], ["热病烦渴", "胃热呕哕", "肺热咳嗽"], (15, 30)),
    entry("tian_hua_fen_sheng", "瓜蒌根", "清热泻火药", "cold", ["sweet", "slightly_bitter"], "肺、胃", ["清热泻火", "生津止渴", "消肿排脓"], ["热病烦渴", "肺热燥咳", "疮疡肿毒"], (10, 15)),
    entry("xia_ku_cao_hua", "夏枯草花", "清热泻火药", "cold", ["pungent", "bitter"], "肝、胆", ["清肝泻火", "明目", "散结消肿"], ["目赤肿痛", "头痛眩晕", "瘰疬"], (9, 15)),
    entry("jue_ming_zi_chao", "炒决明子", "清热泻火药", "cool", ["sweet", "bitter", "salty"], "肝、大肠", ["清肝明目", "润肠通便"], ["目赤涩痛", "头痛眩晕", "肠燥便秘"], (9, 15)),
    entry("huang_qin_jiu", "酒黄芩", "清热燥湿药", "cold", ["bitter"], "肺、胆、脾、大肠、小肠", ["清热燥湿", "泻火解毒", "止血", "安胎"], ["湿温暑湿", "肺热咳嗽", "胎动不安"], (3, 10)),
    entry("huang_lian_jiang", "姜黄连", "清热燥湿药", "cold", ["bitter"], "心、脾、胃、胆、大肠", ["清热燥湿", "泻火解毒"], ["湿热痞满", "呕吐吞酸", "泻痢", "痈肿疔疮"], (2, 5)),
    entry("huang_bai_yan", "盐黄柏", "清热燥湿药", "cold", ["bitter"], "肾、膀胱、大肠", ["清热燥湿", "泻火除蒸", "解毒疗疮"], ["湿热泻痢", "带下阴痒", "骨蒸劳热"], (3, 12)),
    entry("long_dan_cao_jiu", "龙胆", "清热燥湿药", "cold", ["bitter"], "肝、胆", ["清热燥湿", "泻肝胆火"], ["湿热黄疸", "阴肿阴痒", "肝火头痛"], (3, 6)),
    entry("ku_shen_pian", "苦参片", "清热燥湿药", "cold", ["bitter"], "心、肝、胃、大肠、膀胱", ["清热燥湿", "杀虫", "利尿"], ["湿热泻痢", "便血", "黄疸", "疥癣"], (5, 10)),
    entry("bai_xian_pi_sheng", "白鲜", "清热燥湿药", "cold", ["bitter"], "脾、胃、膀胱", ["清热燥湿", "祛风解毒"], ["湿热疮毒", "湿疹疥癣", "黄疸尿赤"], (5, 10)),
    entry("qin_pi_sheng", "苦楝皮青", "清热燥湿药", "cold", ["bitter", "astringent"], "肝、胆、大肠", ["清热燥湿", "收涩止痢", "止带", "明目"], ["湿热泻痢", "带下", "目赤肿痛"], (6, 12)),
    entry("jin_yin_hua_tan", "金银花炭", "清热解毒药", "cold", ["sweet"], "肺、心、胃", ["清热解毒", "疏散风热"], ["痈肿疔疮", "外感风热", "温病初起"], (6, 15)),
    entry("lian_qiao_xin", "连翘心", "清热解毒药", "cold", ["bitter"], "肺、心、小肠", ["清热解毒", "消肿散结", "疏散风热"], ["痈肿疮毒", "瘰疬", "风热感冒"], (6, 15)),
    entry("pu_gong_ying_xian", "鲜蒲公英", "清热解毒药", "cold", ["bitter", "sweet"], "肝、胃", ["清热解毒", "消肿散结", "利湿通淋"], ["痈肿疔毒", "乳痈", "淋证"], (10, 15)),
    entry("zi_hua_di_ding_xian", "鲜紫花地丁", "清热解毒药", "cold", ["bitter", "pungent"], "心、肝", ["清热解毒", "凉血消肿"], ["疔疮肿毒", "乳痈肠痈", "毒蛇咬伤"], (15, 30)),
    entry("ye_ju_hua", "野菊花", "清热解毒药", "cool", ["bitter", "pungent"], "肝、心", ["清热解毒", "泻火平肝"], ["疔疮痈肿", "目赤肿痛", "头痛眩晕"], (9, 15)),
    entry("chuan_xin_lian_pian", "穿心莲片", "清热解毒药", "cold", ["bitter"], "心、肺、大肠、膀胱", ["清热解毒", "凉血", "消肿"], ["感冒发热", "咽喉肿痛", "湿热泻痢"], (6, 9)),
    entry("bai_hua_she_she_cao_xian", "鲜白花蛇舌草", "清热解毒药", "cold", ["sweet", "bland"], "胃、大肠、小肠", ["清热解毒", "利湿通淋"], ["痈肿疮毒", "湿热黄疸", "淋证"], (15, 60)),
    entry("yu_xing_cao_xian", "鲜鱼腥草", "清热解毒药", "cool", ["pungent"], "肺", ["清热解毒", "消痈排脓", "利尿通淋"], ["肺痈吐脓", "痰热喘咳", "热淋"], (15, 25)),
    entry("jin_qiao_mai_sheng", "金荞麦根", "清热解毒药", "cool", ["slightly_pungent", "bitter"], "肺", ["清热解毒", "排脓祛痰", "祛风除湿"], ["肺痈吐脓", "肺热咳嗽", "风湿痹痛"], (15, 30)),
    entry("da_qing_ye_xian", "鲜大青叶", "清热解毒药", "cold", ["bitter"], "心、胃", ["清热解毒", "凉血消斑"], ["温病热入血分", "痄腮", "喉痹"], (10, 15)),
    entry("ban_lan_gen_sheng", "板蓝根片", "清热解毒药", "cold", ["bitter"], "心、胃", ["清热解毒", "凉血利咽"], ["温疫时毒", "发热咽痛", "痄腮"], (9, 15)),
    entry("qing_dai_sheng", "青黛粉", "清热解毒药", "cold", ["salty"], "肝、肺", ["清热解毒", "凉血消斑", "清肝泻火", "定惊"], ["温毒发斑", "血热吐衄", "小儿惊痫"], (1, 3)),
    entry("chuan_bei_mu_fen", "川贝粉", "化痰止咳平喘药", "cool", ["bitter", "sweet"], "肺、心", ["清热化痰", "润肺止咳", "散结消肿"], ["肺热燥咳", "干咳少痰", "瘰疬"], (3, 10)),
    entry("zhe_bei_mu_sheng", "大贝母", "化痰止咳平喘药", "cold", ["bitter"], "肺、心", ["清热化痰", "散结消痈"], ["风热咳嗽", "痰火郁结", "瘰疬疮毒"], (5, 10)),
    entry("gua_lou_pi", "瓜蒌皮", "化痰止咳平喘药", "cold", ["sweet"], "肺、胃、大肠", ["清热化痰", "利气宽胸"], ["痰热咳嗽", "胸痹结胸"], (6, 10)),
    entry("gua_lou_zi", "瓜蒌子", "化痰止咳平喘药", "cold", ["sweet"], "肺、胃、大肠", ["润肺化痰", "滑肠通便"], ["燥咳痰黏", "肠燥便秘"], (6, 10)),
    entry("zhu_li", "竹沥", "化痰止咳平喘药", "cold", ["sweet"], "心、肺、胃", ["清热豁痰", "定惊利窍"], ["痰热咳喘", "中风痰迷"], (30, 50)),
    entry("tian_zhu_huang_sheng", "天竺黄块", "化痰止咳平喘药", "cold", ["sweet"], "心、肝", ["清热豁痰", "凉心定惊"], ["小儿惊风", "中风痰迷", "热病神昏"], (3, 9)),
    entry("qian_hu_sheng", "信前胡", "化痰止咳平喘药", "cool", ["bitter", "pungent"], "肺", ["降气化痰", "散风清热"], ["痰热喘咳", "风热咳嗽"], (3, 10)),
    entry("jie_geng_sheng", "苦桔梗", "化痰止咳平喘药", "neutral", ["bitter", "pungent"], "肺", ["宣肺", "祛痰", "利咽", "排脓"], ["咳嗽痰多", "咽痛音哑", "肺痈吐脓"], (3, 10)),
    entry("ban_xia_zhi", "法半夏", "化痰止咳平喘药", "warm", ["pungent"], "脾、胃、肺", ["燥湿化痰"], ["湿痰咳嗽", "痰饮眩悸"], (3, 9), "有毒，宜炮制"),
    entry("ban_xia_jiang", "姜半夏", "化痰止咳平喘药", "warm", ["pungent"], "脾、胃、肺", ["温中化痰", "降逆止呕"], ["痰饮呕吐", "脘痞"], (3, 9)),
    entry("tian_nan_xing_zhi", "制天南星", "化痰止咳平喘药", "warm", ["bitter", "pungent"], "肺、肝、脾", ["燥湿化痰", "祛风止痉", "散结消肿"], ["顽痰咳嗽", "风痰眩晕", "中风痰壅"], (3, 9), "有毒"),
    entry("dan_nan_xing", "胆南星", "化痰止咳平喘药", "cool", ["bitter"], "肺、肝、脾", ["清热化痰", "息风定惊"], ["痰热咳嗽", "中风惊痫"], (3, 6)),
    entry("bai_jie_zi_chao", "炒白芥子", "化痰止咳平喘药", "warm", ["pungent"], "肺", ["温肺祛痰", "利气散结", "通络止痛"], ["寒痰喘咳", "悬饮", "阴疽流注"], (3, 9)),
    entry("zao_jia", "猪牙皂", "化痰止咳平喘药", "warm", ["pungent", "salty"], "肺、大肠", ["祛顽痰", "通窍开闭", "祛风杀虫"], ["咳喘痰涌", "中风口噤"], (1, 1.5), "有小毒，孕妇慎用"),
    entry("xuan_fu_hua_sheng", "金沸花", "化痰止咳平喘药", "warm", ["bitter", "pungent", "salty"], "肺、脾、胃、大肠", ["降气消痰", "行水止呕"], ["咳喘痰多", "痰饮蓄结", "呕吐噫气"], (3, 10)),
    entry("bai_qian_mi", "蜜白前", "化痰止咳平喘药", "slightly_warm", ["pungent", "sweet"], "肺", ["降气化痰", "止咳"], ["咳嗽痰多", "气喘"], (3, 10)),
    entry("ku_xing_ren", "苦杏仁", "化痰止咳平喘药", "warm", ["bitter"], "肺、大肠", ["降气止咳平喘", "润肠通便"], ["咳嗽气喘", "肠燥便秘"], (5, 10), "有小毒"),
    entry("zi_su_zi_chao", "炒苏子", "化痰止咳平喘药", "warm", ["pungent"], "肺、大肠", ["降气化痰", "止咳平喘", "润肠通便"], ["痰壅气逆", "肠燥便秘"], (5, 10)),
    entry("bai_guo_chao", "炒白果", "化痰止咳平喘药", "neutral", ["sweet", "bitter", "astringent"], "肺", ["敛肺定喘", "止带缩尿"], ["哮喘痰嗽", "带下白浊"], (5, 10), "有毒，不可生食多用"),
    entry("yang_jin_hua_xian", "曼陀罗花", "化痰止咳平喘药", "warm", ["pungent"], "肺、肝", ["平喘止咳", "麻醉止痛", "解痉"], ["哮喘咳嗽", "脘腹冷痛"], (0.3, 0.6), "有大毒，孕妇禁用"),
    entry("sang_bai_pi_sheng", "桑根白皮", "化痰止咳平喘药", "cold", ["sweet"], "肺", ["泻肺平喘", "利水消肿"], ["肺热喘咳", "水肿胀满"], (6, 12)),
    entry("ting_li_zi_chao", "炒葶苈子", "化痰止咳平喘药", "cold", ["pungent", "bitter"], "肺、膀胱", ["泻肺平喘", "行水消肿"], ["痰涎壅肺", "水肿胀满"], (3, 10)),
    entry("pi_pa_ye_sheng", "生枇杷叶", "化痰止咳平喘药", "cool", ["bitter"], "肺、胃", ["清肺止咳", "降逆止呕"], ["肺热咳嗽", "胃热呕吐"], (6, 10)),
    entry("bai_bu_sheng", "生百部", "化痰止咳平喘药", "slightly_warm", ["sweet", "bitter"], "肺", ["润肺下气止咳", "杀虫灭虱"], ["新久咳嗽", "百日咳", "蛲虫病"], (3, 9)),
    entry("zi_wan_sheng", "生紫菀", "化痰止咳平喘药", "warm", ["pungent", "bitter"], "肺", ["润肺下气", "消痰止咳"], ["咳嗽气喘", "寒痰、热痰"], (5, 10)),
    entry("kuan_dong_hua_sheng", "生款冬花", "化痰止咳平喘药", "warm", ["pungent"], "肺", ["润肺下气", "止咳化痰"], ["咳嗽气喘", "肺虚久咳"], (5, 10)),
    entry("ma_huang_sheng", "生麻黄", "辛温解表药", "warm", ["pungent", "slightly_bitter"], "肺、膀胱", ["发汗解表", "宣肺平喘", "利水消肿"], ["风寒表实", "喘咳", "风水水肿"], (2, 10)),
    entry("gui_zhi_sheng", "柳桂", "辛温解表药", "warm", ["pungent", "sweet"], "心、肺、膀胱", ["发汗解肌", "温通经脉", "助阳化气"], ["风寒表证", "寒凝血滞", "痰饮"], (3, 10)),
    entry("zi_su_ye_sheng", "苏叶", "辛温解表药", "warm", ["pungent"], "肺、脾", ["解表散寒", "行气和胃"], ["风寒感冒", "咳嗽恶心", "胎气上逆"], (5, 10)),
    entry("xiang_ru_sheng", "香薷草", "辛温解表药", "warm", ["pungent"], "肺、脾、胃", ["发汗解表", "化湿和中", "利水消肿"], ["阴暑感冒", "腹痛吐泻", "水肿"], (3, 10)),
    entry("sheng_jiang_pi", "生姜皮", "辛温解表药", "cool", ["pungent"], "肺、脾", ["行水消肿"], ["水肿", "小便不利"], (3, 10)),
    entry("sheng_jiang_zhi", "姜汁", "辛温解表药", "warm", ["pungent"], "肺、脾、胃", ["温中止呕", "温肺止咳"], ["胃寒呕吐", "肺寒咳嗽"], (3, 10)),
    entry("cong_bai_tou", "葱白头", "辛温解表药", "warm", ["pungent"], "肺、胃", ["发汗解表", "散寒通阳"], ["外感风寒", "阴寒腹痛"], (3, 10)),
    entry("xi_xin_sheng", "辽细辛", "辛温解表药", "warm", ["pungent"], "心、肺、肾", ["解表散寒", "祛风止痛", "通窍", "温肺化饮"], ["风寒感冒", "头痛牙痛", "鼻渊", "寒饮喘咳"], (1, 3), "反藜芦，用量不宜过大"),
    entry("gao_ben_sheng", "香藁本", "辛温解表药", "warm", ["pungent"], "膀胱", ["祛风散寒", "除湿止痛"], ["风寒头痛", "巅顶疼痛", "风湿痹痛"], (3, 10)),
]


def main():
    existing = set()
    if RAW.exists():
        for h in json.loads(RAW.read_text(encoding="utf-8")):
            if h.get("name_zh"):
                existing.add(h["name_zh"])
            if h.get("key"):
                existing.add(h["key"])

    kept = []
    skipped = []
    for e in EXTRA:
        if e["name_zh"] in existing or e["key"] in existing:
            skipped.append(e["name_zh"])
            continue
        # 清理 description 里误写
        e["description_zh"] = re.sub(r"归[^。]+经。", f"归{re.search(r'归(.+?)经', e['description_zh']).group(1) if re.search(r'归(.+?)经', e['description_zh']) else ''}经。", e["description_zh"], count=1)
        kept.append(e)
        existing.add(e["name_zh"])
        existing.add(e["key"])

    OUT.write_text(json.dumps(kept, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"写出扩充 {len(kept)} 味 → {OUT}")
    if skipped:
        print(f"跳过已存在 {len(skipped)}：{', '.join(skipped[:20])}{'…' if len(skipped) > 20 else ''}")


if __name__ == "__main__":
    main()
