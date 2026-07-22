# -*- coding: utf-8 -*-
"""
爬取本草典开放数据中与「金元」「民国」相关的方剂页，并补入本地库。

数据源：https://bencaodian.org/data/v1/ （CC BY-SA 4.0，署名为 Bencaodian Editorial）
入库：
  - formulas_extra.json（方剂主库，与 formulas_raw 合并使用）
  - era_library.json（朝代索引）
  - herbs.db classical_refs（相关药材的典籍线索，若库可用）

说明：开放数据集共 112 首方，金元/民国相关条目有限；
对课程常用而开放集未收录的名方，以 course-sketch 形式补录（示意组成）。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT_DIR = DATA / "era_crawl"
EXTRA_PATH = DATA / "formulas_extra.json"
RAW_PATH = DATA / "formulas_raw.json"
ERA_LIBRARY_PATH = DATA / "era_library.json"

UA = (
    "BencaoShizhen-CourseProject/1.0 "
    "(JinYuan-Minguo formula crawl; CC BY-SA 4.0 attribution: Bencaodian Editorial)"
)

# 金元相关出处
JINYUAN_SOURCES = {
    "pi_wei_lun",
    "dan_xi_xin_fa",
    "lan_shi_mi_cang",
    "nei_wai_shang_bian_huo_lun",
    "su_wen_bing_ji_qi_yi_bao_ming_ji",
    "ru_men_shi_qin",
    "dong_yuan_shi_xiao_fang",
    "yi_xue_qi_yuan",
    "ci_shi_nan_zhi",
}

# 民国 / 清末民初 / 近代承接
MINGUO_SOURCES = {
    "yi_xue_zhong_zhong_can_xi_lu",
    "xian_dai_jing_yan_fang",
    "chong_ding_tong_su_shang_han_lun",
    "za_bing_zheng_zhi_xin_yi",  # 1956，近代验方，挂民国承接
}

ROLE = {"jun": "jun", "chen": "chen", "zuo": "zuo", "shi": "shi",
        "君": "jun", "臣": "chen", "佐": "zuo", "使": "shi"}


def fetch_json(url: str):
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_html(url: str) -> str:
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    with urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def existing_keys() -> set[str]:
    keys: set[str] = set()
    for path in (RAW_PATH, EXTRA_PATH):
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, list):
            for f in data:
                if isinstance(f, dict) and f.get("key"):
                    keys.add(f["key"])
    return keys


def normalize_remote_formula(f: dict) -> dict:
    """把本草典方剂记录压成项目本地 schema。"""
    comps = []
    for item in f.get("composition") or []:
        if not isinstance(item, dict):
            continue
        hk = item.get("herb_key")
        if not hk:
            continue
        role = str(item.get("role") or "zuo").lower()
        role = ROLE.get(role, role if role in ("jun", "chen", "zuo", "shi") else "zuo")
        dosage = item.get("dosage") or item.get("dosage_zh") or ""
        if isinstance(dosage, dict):
            dosage = dosage.get("zh") or dosage.get("en") or ""
        comps.append(
            {
                "herb_key": hk,
                "role": role,
                "dosage": str(dosage),
                "explanation_zh": item.get("explanation_zh") or "",
            }
        )
    principle = f.get("treatment_principle") or {}
    if isinstance(principle, dict):
        principle_zh = principle.get("zh") or ""
    else:
        principle_zh = str(principle or "")
    return {
        "key": f.get("key"),
        "slug": f.get("slug") or str(f.get("key") or "").replace("_", "-"),
        "name_zh": f.get("name_zh"),
        "name_pinyin": f.get("name_pinyin"),
        "name_en": f.get("name_en"),
        "category": f.get("category") or "未分类",
        "subcategory": f.get("subcategory"),
        "source_text_key": f.get("source_text_key"),
        "source_chapter": f.get("source_chapter"),
        "treatment_principle": {"zh": principle_zh, "en": ""},
        "composition": comps,
        "preparation_zh": f.get("preparation_zh") or "水煎服。",
        "description_zh": f.get("description_zh") or "",
        "verification": {
            "status": "bencaodian-opendata",
            "license": "CC BY-SA 4.0",
            "attribution": "Bencaodian Editorial",
            "source_url": f"https://bencaodian.org/zh/formulas/{(f.get('slug') or str(f.get('key') or '').replace('_', '-'))}",
        },
    }


def sketch(key, name, cat, principle, source, comps, desc=""):
    composition = []
    for herb_key, role_zh, dosage in comps:
        composition.append(
            {
                "herb_key": herb_key,
                "role": ROLE.get(role_zh, "zuo"),
                "dosage": dosage,
                "explanation_zh": f"{role_zh}药",
            }
        )
    return {
        "key": key,
        "slug": key.replace("_", "-"),
        "name_zh": name,
        "category": cat,
        "source_text_key": source,
        "treatment_principle": {"zh": principle, "en": ""},
        "composition": composition,
        "preparation_zh": "水煎服。",
        "description_zh": desc or f"{name}：{principle}。",
        "verification": {"status": "course-sketch", "era": "jinyuan-minguo-expand"},
    }


# 开放集未收录、课程常用的金元 / 民国名方（示意组成）
SKETCH_FORMULAS = [
    # —— 金元 ——
    (
        "fang_feng_tong_sheng_san", "防风通圣散", "解表剂",
        "疏风解表，清热通便", "su_wen_bing_ji_qi_yi_bao_ming_ji",
        [
            ("fang_feng", "君", "15g"), ("ma_huang", "君", "15g"), ("jing_jie", "臣", "15g"),
            ("bo_he", "臣", "15g"), ("lian_qiao", "臣", "15g"), ("jie_geng", "佐", "30g"),
            ("chuan_xiong", "佐", "15g"), ("dang_gui", "佐", "15g"), ("bai_shao", "佐", "15g"),
            ("bai_zhu", "佐", "15g"), ("zhi_zi", "佐", "15g"), ("da_huang", "佐", "15g"),
            ("mang_xiao", "佐", "15g"), ("shi_gao", "佐", "30g"), ("huang_qin", "佐", "30g"),
            ("gan_cao", "使", "60g"), ("hua_shi", "使", "90g"),
        ],
        "刘完素表里双解代表方，金元寒凉派常用。",
    ),
    (
        "sheng_yang_yi_wei_tang", "升阳益胃汤", "补益剂",
        "益气升阳，清热祛湿", "pi_wei_lun",
        [
            ("huang_qi", "君", "60g"), ("ban_xia", "臣", "30g"), ("ren_shen", "臣", "30g"),
            ("gan_cao", "臣", "30g"), ("du_huo", "佐", "15g"), ("fang_feng", "佐", "15g"),
            ("bai_shao", "佐", "15g"), ("qiang_huo", "佐", "15g"), ("chen_pi", "佐", "12g"),
            ("fu_ling", "佐", "9g"), ("chai_hu", "佐", "9g"), ("ze_xie", "佐", "9g"),
            ("bai_zhu", "佐", "9g"), ("huang_lian", "使", "6g"),
        ],
        "李东垣治脾胃虚弱兼湿盛之方。",
    ),
    (
        "qing_shu_yi_qi_tang", "清暑益气汤", "补益剂",
        "清暑益气，除湿健脾", "pi_wei_lun",
        [
            ("huang_qi", "君", "30g"), ("cang_zhu", "臣", "9g"), ("sheng_ma", "臣", "9g"),
            ("ren_shen", "臣", "9g"), ("ze_xie", "佐", "9g"), ("shen_qu", "佐", "9g"),
            ("chen_pi", "佐", "6g"), ("bai_zhu", "佐", "9g"), ("mai_dong", "佐", "9g"),
            ("dang_gui", "佐", "6g"), ("gan_cao", "使", "3g"), ("qing_pi", "使", "3g"),
            ("huang_bai", "使", "6g"), ("ge_gen", "使", "6g"), ("wu_wei_zi", "使", "3g"),
        ],
        "东垣清暑益气法，异于后世温病之同名方。",
    ),
    (
        "hu_qian_wan", "虎潜丸", "补益剂",
        "滋阴降火，强壮筋骨", "dan_xi_xin_fa",
        [
            ("huang_bai", "君", "150g"), ("zhi_mu", "臣", "60g"), ("shu_di_huang", "臣", "60g"),
            ("gui_jia", "臣", "120g"), ("bai_shao", "佐", "60g"), ("suo_yang", "佐", "45g"),
            ("chen_pi", "佐", "60g"),
        ],
        "丹溪滋阴派治痿名方（原方虎骨今多略或以它药代，课程示意从略）。",
    ),
    # —— 民国 · 张锡纯等 ——
    (
        "sheng_xian_tang", "升陷汤", "补益剂",
        "益气升陷", "yi_xue_zhong_zhong_can_xi_lu",
        [
            ("huang_qi", "君", "18g"), ("zhi_mu", "臣", "9g"), ("chai_hu", "佐", "4.5g"),
            ("jie_geng", "佐", "4.5g"), ("sheng_ma", "使", "3g"),
        ],
        "张锡纯治大气下陷代表方。",
    ),
    (
        "jian_ling_tang", "建瓴汤", "治风剂",
        "镇肝熄风，滋阴安神", "yi_xue_zhong_zhong_can_xi_lu",
        [
            ("niu_xi", "君", "30g"), ("dai_zhe_shi", "臣", "24g"), ("long_gu", "臣", "18g"),
            ("mu_li", "臣", "18g"), ("sheng_di_huang", "佐", "18g"), ("bai_shao", "佐", "12g"),
            ("bai_zi_ren", "佐", "12g"), ("shan_yao", "使", "30g"),
        ],
        "张锡纯治脑充血、肝阳上亢之方，与镇肝熄风汤并称。",
    ),
    (
        "huo_luo_xiao_ling_dan", "活络效灵丹", "活血剂",
        "活血祛瘀，通络止痛", "yi_xue_zhong_zhong_can_xi_lu",
        [
            ("dang_gui", "君", "15g"), ("dan_shen", "君", "15g"),
            ("ru_xiang", "臣", "15g"), ("mo_yao", "臣", "15g"),
        ],
        "张锡纯活血通络验方，组成精简。",
    ),
    (
        "yu_ye_tang", "玉液汤", "补益剂",
        "益气生津，润燥止渴", "yi_xue_zhong_zhong_can_xi_lu",
        [
            ("shan_yao", "君", "30g"), ("huang_qi", "君", "15g"), ("zhi_mu", "臣", "18g"),
            ("ji_nei_jin", "佐", "6g"), ("ge_gen", "佐", "4.5g"), ("wu_wei_zi", "佐", "9g"),
            ("tian_hua_fen", "使", "9g"),
        ],
        "张锡纯治消渴气阴两虚方。",
    ),
    (
        "li_chong_tang", "理冲汤", "补益剂",
        "益气活血，消癥散结", "yi_xue_zhong_zhong_can_xi_lu",
        [
            ("huang_qi", "君", "30g"), ("dang_shen", "臣", "12g"), ("bai_zhu", "臣", "9g"),
            ("shan_yao", "佐", "15g"), ("tian_dong", "佐", "12g"), ("san_leng", "佐", "9g"),
            ("e_zhu", "佐", "9g"), ("ji_nei_jin", "使", "9g"),
        ],
        "张锡纯治妇女癥瘕、气虚血瘀方。",
    ),
]


def merge_into_extra(new_items: list[dict]) -> tuple[int, int]:
    extra: list[dict] = []
    if EXTRA_PATH.exists():
        try:
            extra = json.loads(EXTRA_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            extra = []
    if not isinstance(extra, list):
        extra = []
    by_key = {f.get("key"): i for i, f in enumerate(extra) if isinstance(f, dict) and f.get("key")}
    added = updated = 0
    for item in new_items:
        k = item.get("key")
        if not k:
            continue
        if k in by_key:
            # 仅当原记录是 sketch / 空组成时用爬取结果覆盖 enrichment
            old = extra[by_key[k]]
            old_ver = (old.get("verification") or {}).get("status") if isinstance(old.get("verification"), dict) else ""
            if old_ver == "bencaodian-opendata":
                continue
            if item.get("verification", {}).get("status") == "bencaodian-opendata" or not (old.get("composition") or []):
                extra[by_key[k]] = item
                updated += 1
            continue
        # 若已在 raw 中则跳过
        extra.append(item)
        by_key[k] = len(extra) - 1
        added += 1
    EXTRA_PATH.write_text(json.dumps(extra, ensure_ascii=False, indent=2), encoding="utf-8")
    return added, updated


def update_era_library(texts_meta: list[dict]) -> None:
    if not ERA_LIBRARY_PATH.exists():
        return
    lib = json.loads(ERA_LIBRARY_PATH.read_text(encoding="utf-8"))
    eras = lib.get("eras") or []
    by_id = {e.get("id"): e for e in eras if isinstance(e, dict)}

    def ensure_sources(era_id: str, keys: set[str], classic_defs: list[dict]):
        era = by_id.get(era_id)
        if not era:
            return
        src = list(era.get("source_text_keys") or [])
        for k in keys:
            if k not in src:
                src.append(k)
        era["source_text_keys"] = src
        classics = list(era.get("classics") or [])
        have = {c.get("key") for c in classics if isinstance(c, dict)}
        for c in classic_defs:
            if c["key"] not in have:
                classics.append(c)
        era["classics"] = classics

    text_by_key = {t.get("key"): t for t in texts_meta if isinstance(t, dict)}

    def C(key: str, title: str, year: str, kind: str, blurb: str) -> dict:
        t = text_by_key.get(key) or {}
        zh = t.get("title_zh") or title
        zh = str(zh).strip()
        if not zh.startswith("《"):
            zh = f"《{zh}》"
        return {"key": key, "title": zh, "year": year, "kind": kind, "blurb": blurb}

    ensure_sources(
        "jinyuan",
        JINYUAN_SOURCES,
        [
            C("ci_shi_nan_zhi", "此事难知", "约1308", "方书", "王好古易水学派，九味羌活等方见其用药思路。"),
            C("lan_shi_mi_cang", "兰室秘藏", "约1276", "方书", "李东垣晚年方论，清胃散等方出于此。"),
        ],
    )
    ensure_sources(
        "minguo",
        MINGUO_SOURCES,
        [
            C("chong_ding_tong_su_shang_han_lun", "重订通俗伤寒论", "1916", "方书", "清末民初伤寒通俗读本，蒿芩清胆汤等方通行。"),
            C("za_bing_zheng_zhi_xin_yi", "杂病证治新义", "1956", "方书", "近代验方汇编，天麻钩藤饮等在本项目挂民国承接。"),
        ],
    )
    ERA_LIBRARY_PATH.write_text(json.dumps(lib, ensure_ascii=False, indent=2), encoding="utf-8")


def sync_herb_classical_refs(formulas: list[dict]) -> int:
    """把新方涉及药材的 classical_refs 补一条出处线索。"""
    sys.path.insert(0, str(ROOT))
    try:
        from app.database import SessionLocal
        from app.models import Herb
    except Exception as e:
        print("跳过 herbs.db 同步：", e)
        return 0

    # herb_key -> set of source titles
    refs: dict[str, set[str]] = {}
    title_map = {
        "pi_wei_lun": "《脾胃论》",
        "dan_xi_xin_fa": "《丹溪心法》",
        "su_wen_bing_ji_qi_yi_bao_ming_ji": "《素问病机气宜保命集》",
        "yi_xue_zhong_zhong_can_xi_lu": "《医学衷中参西录》",
        "chong_ding_tong_su_shang_han_lun": "《重订通俗伤寒论》",
        "za_bing_zheng_zhi_xin_yi": "《杂病证治新义》",
        "lan_shi_mi_cang": "《兰室秘藏》",
        "ci_shi_nan_zhi": "《此事难知》",
        "nei_wai_shang_bian_huo_lun": "《内外伤辨惑论》",
        "xian_dai_jing_yan_fang": "近代经验方",
    }
    for f in formulas:
        src = f.get("source_text_key")
        title = title_map.get(src) or src
        for c in f.get("composition") or []:
            hk = c.get("herb_key") if isinstance(c, dict) else None
            if hk:
                refs.setdefault(hk, set()).add(title)

    db = SessionLocal()
    updated = 0
    try:
        for hk, titles in refs.items():
            herb = db.query(Herb).filter(Herb.key == hk).first()
            if not herb:
                continue
            raw = herb.classical_refs
            try:
                cur = json.loads(raw) if raw else []
            except (TypeError, json.JSONDecodeError):
                cur = []
            if not isinstance(cur, list):
                cur = []
            have = set()
            for item in cur:
                if isinstance(item, dict):
                    have.add(item.get("name") or item.get("title") or "")
                elif isinstance(item, str):
                    have.add(item)
            changed = False
            for t in sorted(titles):
                if t and t not in have:
                    cur.append({"name": t, "value": 1})
                    have.add(t)
                    changed = True
            if changed:
                herb.classical_refs = json.dumps(cur, ensure_ascii=False)
                updated += 1
        db.commit()
    finally:
        db.close()
    return updated


def enrich_from_html(formulas: list[dict]) -> int:
    """尝试抓取方剂页，补 description（若 JSON 描述为空）。"""
    filled = 0
    for f in formulas:
        if f.get("description_zh"):
            continue
        slug = f.get("slug") or str(f.get("key") or "").replace("_", "-")
        url = f"https://bencaodian.org/zh/formulas/{slug}"
        try:
            html = fetch_html(url)
        except Exception:
            continue
        # 粗取首段中文说明
        m = re.search(r"<p[^>]*>([^<]{20,200})</p>", html)
        if m:
            text = re.sub(r"\s+", "", m.group(1))
            if text and "方剂" not in text[:4]:
                f["description_zh"] = text[:280]
                filled += 1
    return filled


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("拉取本草典开放数据…")
    texts = fetch_json("https://bencaodian.org/data/v1/classical_texts.json")
    formulas = fetch_json("https://bencaodian.org/data/v1/formulas.json")
    (OUT_DIR / "classical_texts_remote.json").write_text(
        json.dumps(texts, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT_DIR / "formulas_remote.json").write_text(
        json.dumps(formulas, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  典籍 {len(texts)} · 方剂 {len(formulas)}")

    jy_texts = [t for t in texts if t.get("key") in JINYUAN_SOURCES]
    mg_texts = [t for t in texts if t.get("key") in MINGUO_SOURCES]
    jy_forms = [f for f in formulas if f.get("source_text_key") in JINYUAN_SOURCES]
    mg_forms = [f for f in formulas if f.get("source_text_key") in MINGUO_SOURCES]
    print(f"  金元典籍 {len(jy_texts)} · 方剂 {len(jy_forms)}")
    print(f"  民国典籍 {len(mg_texts)} · 方剂 {len(mg_forms)}")

    remote_norm = [normalize_remote_formula(f) for f in (jy_forms + mg_forms)]
    html_filled = enrich_from_html(remote_norm)
    print(f"  方剂页补充说明 {html_filled} 条")

    have = existing_keys()
    # raw 已有的不算新增；仍把 remote 规范化结果写入 crawl 缓存
    (OUT_DIR / "jinyuan_minguo_formulas.json").write_text(
        json.dumps(remote_norm, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    to_merge: list[dict] = []
    remote_new = 0
    for item in remote_norm:
        if item["key"] not in have:
            to_merge.append(item)
            remote_new += 1

    sketch_new = 0
    for row in SKETCH_FORMULAS:
        item = sketch(*row)
        if item["key"] in have:
            continue
        to_merge.append(item)
        sketch_new += 1

    added, updated = merge_into_extra(to_merge)
    print(f"  写入 formulas_extra：新增 {added}（开放数据新方 {remote_new} + 补录 {sketch_new}），更新 {updated}")

    update_era_library(texts)
    print("  已更新 era_library.json 金元/民国索引")

    herb_n = sync_herb_classical_refs(remote_norm + [sketch(*r) for r in SKETCH_FORMULAS])
    print(f"  herbs.db classical_refs 更新 {herb_n} 味药")

    # 汇总当前库内归属
    sys.path.insert(0, str(ROOT))
    from app.era_library import _load_era_library, build_era_index

    _load_era_library.cache_clear()
    print("-" * 40)
    for e in build_era_index():
        if e.get("id") in ("jinyuan", "minguo"):
            names = "、".join(f.get("name_zh") or "" for f in (e.get("formulas") or [])[:8])
            print(f"{e['dynasty']} 方剂 {e['formula_count']}  · {names}…")
    print("完成。重启后端后首页环形图会加载新方。")


if __name__ == "__main__":
    main()
