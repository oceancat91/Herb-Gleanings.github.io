import json
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .analysis import build_analysis
from .config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from .database import Base, engine, get_db
from .models import Herb
from .schemas import (
    CategoryItem,
    HerbBrief,
    HerbDetail,
    HerbListResponse,
    StatsResponse,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_INDEX = PROJECT_ROOT / "index.html"

app = FastAPI(
    title="本草拾珍 API",
    description=(
        "中医药材属性数据库接口。"
        "数据来源：本草典 Bencaodian Editorial（CC BY-SA 4.0），"
        "覆盖四气、五味、归经、功效、主治、用量、炮制、禁忌等。"
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def private_network_cors(request, call_next):
    """允许 GitHub Pages (HTTPS) 探测本机后端（Chrome Private Network Access）。"""
    if request.method == "OPTIONS" and request.headers.get(
        "access-control-request-private-network"
    ):
        from fastapi.responses import Response

        return Response(
            status_code=204,
            headers={
                "Access-Control-Allow-Origin": request.headers.get("origin") or "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Private-Network": "true",
                "Access-Control-Allow-Credentials": "true",
            },
        )
    response = await call_next(request)
    if request.headers.get("origin"):
        response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response


def _loads(text: str | None):
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def to_detail(herb: Herb) -> HerbDetail:
    data = HerbDetail.model_validate(herb)
    data.gongxiao_detail = _loads(herb.gongxiao_detail)
    data.zhuzhi_detail = _loads(herb.zhuzhi_detail)
    data.paozhi = _loads(herb.paozhi)
    data.pharmacology = _loads(herb.pharmacology)
    data.classical_refs = _loads(herb.classical_refs)
    data.extra = _loads(herb.extra)
    return data


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def index():
    """托管前端页面；API 说明见 /api"""
    if FRONTEND_INDEX.is_file():
        return FileResponse(FRONTEND_INDEX, media_type="text/html; charset=utf-8")
    return {
        "name": "本草拾珍 API",
        "docs": "/docs",
        "message": "未找到前端 index.html",
    }


@app.get("/api")
def api_root():
    return {
        "name": "本草拾珍 API",
        "docs": "/docs",
        "endpoints": [
            "/api/herbs",
            "/api/herbs/{id_or_key}",
            "/api/herbs/{id_or_key}/story",
            "/api/formulas/{id_or_key}",
            "/api/stats",
            "/api/analysis",
            "/api/assistant/consult",
            "/api/categories",
            "/api/geo/density",
            "/api/geo/province/{name}",
            "/api/geo/china",
            "/api/workshop/check",
            "/api/alchemy/place",
            "/api/alchemy/refine",
            "/api/filter/siqi/{value}",
            "/api/filter/wuwei/{value}",
            "/api/filter/guijing/{value}",
        ],
        "attribution": "Bencaodian Editorial / 本草典编辑部 · CC BY-SA 4.0",
    }


def _geo_density_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "herb_geo_density.json"


def _load_geo_density() -> dict:
    path = _geo_density_path()
    if not path.is_file():
        raise HTTPException(status_code=404, detail="缺少 herb_geo_density.json")
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_province_name(name: str) -> str:
    import re

    return re.sub(
        r"壮族自治区$|回族自治区$|维吾尔自治区$|自治区$|特别行政区$|省$|市$",
        "",
        str(name or "").strip(),
    )


@app.get("/api/geo/density")
def geo_density():
    """中国大陆道地/主产区疏密示意（课程通识，非产量实测）。"""
    data = _load_geo_density()
    return {
        "unit": data.get("unit"),
        "note": data.get("_comment"),
        "provinces": data.get("provinces") or [],
    }


@app.get("/api/geo/province/{name}")
def geo_province(name: str, db: Session = Depends(get_db)):
    """按省份返回道地/主产关联药材（课程通识映射）。"""
    data = _load_geo_density()
    short = _normalize_province_name(name)
    row = None
    for p in data.get("provinces") or []:
        pn = _normalize_province_name(p.get("name") or "")
        if pn == short or (p.get("name") or "") == name:
            row = p
            break
    if not row:
        raise HTTPException(status_code=404, detail=f"未找到产区：{name}")

    herb_names = row.get("herbs") or row.get("samples") or []
    items: list[HerbBrief] = []
    seen: set[str] = set()
    for hn in herb_names:
        if not hn or hn in seen:
            continue
        herb = db.scalar(select(Herb).where(Herb.name_zh == hn))
        if herb:
            items.append(HerbBrief.model_validate(herb))
            seen.add(hn)

    return {
        "name": row.get("name") or short,
        "value": len(items),
        "unit": data.get("unit"),
        "note": data.get("_comment"),
        "samples": row.get("samples") or [],
        "herbs": items,
    }


@app.get("/api/geo/china")
def geo_china():
    """本机托管的中国地图 GeoJSON（避免浏览器跨域加载失败）。"""
    path = Path(__file__).resolve().parent.parent / "data" / "china.json"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="缺少 china.json")
    return FileResponse(path, media_type="application/json; charset=utf-8")


@app.get("/china-geo-embed.js")
def china_geo_embed():
    """前端内嵌地图脚本（API 未更新或 CDN 不可用时的兜底）。"""
    path = PROJECT_ROOT / "china-geo-embed.js"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="缺少 china-geo-embed.js")
    return FileResponse(path, media_type="application/javascript; charset=utf-8")


@app.get("/api/herbs", response_model=HerbListResponse)
def list_herbs(
    q: str | None = Query(None, description="按中文名/拼音/拉丁名搜索"),
    siqi: str | None = Query(None, description="四气，如 寒/凉/平/温/热"),
    wuwei: str | None = Query(None, description="五味关键字，如 甘/苦/辛"),
    guijing: str | None = Query(None, description="归经关键字，如 心/肝/脾"),
    shengjiang: str | None = Query(None, description="升降沉浮：升/降/沉/浮"),
    category: str | None = Query(None, description="功效分类"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    stmt = select(Herb)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Herb.name_zh.like(like),
                Herb.name_pinyin.like(like),
                Herb.name_latin.like(like),
                Herb.name_en.like(like),
                Herb.key.like(like),
            )
        )
    if siqi:
        stmt = stmt.where(Herb.siqi == siqi)
    if wuwei:
        stmt = stmt.where(Herb.wuwei.like(f"%{wuwei}%"))
    if guijing:
        stmt = stmt.where(Herb.guijing.like(f"%{guijing}%"))
    if shengjiang:
        stmt = stmt.where(Herb.shengjiang == shengjiang)
    if category:
        stmt = stmt.where(Herb.category == category)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(Herb.name_zh).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return HerbListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[HerbBrief.model_validate(h) for h in items],
    )


_FORMULA_SOURCE_ZH = {
    "shang_han_lun": "《伤寒论》",
    "jin_gui_yao_lue": "《金匮要略》",
    "tai_ping_hui_min_he_ji_ju_fang": "《太平惠民和剂局方》",
    "yi_fang_ji_jie": "《医方集解》",
    "wen_bing_tiao_bian": "《温病条辨》",
    "pi_wei_lun": "《脾胃论》",
    "yi_lin_gai_cuo": "《医林改错》",
    "jing_yue_quan_shu": "《景岳全书》",
    "dan_xi_xin_fa": "《丹溪心法》",
    "xiao_er_yao_zheng_zhi_jue": "《小儿药证直诀》",
    "bei_ji_qian_jin_yao_fang": "《备急千金要方》",
    "su_wen_bing_ji_qi_yi_bao_ming_ji": "《素问病机气宜保命集》",
    "nei_ke_zhai_yao": "《内科摘要》",
    "wen_re_jing_wei": "《温热经纬》",
    "ji_sheng_fang": "《济生方》",
    "wai_ke_zheng_zhi_quan_sheng_ji": "《外科证治全生集》",
    "fu_ren_da_quan_liang_fang": "《妇人大全良方》",
    "pu_ji_ben_shi_fang": "《普济本事方》",
    "wai_ke_zheng_zong": "《外科正宗》",
    "yi_xue_zhong_zhong_can_xi_lu": "《医学衷中参西录》",
    "fu_qing_zhu_nv_ke": "《傅青主女科》",
    "yi_fang_kao": "《医方考》",
    "lan_shi_mi_cang": "《兰室秘藏》",
    "jiao_zhu_fu_ren_liang_fang": "《校注妇人良方》",
    "chong_ding_tong_su_shang_han_lun": "《重订通俗伤寒论》",
    "tong_su_shang_han_lun": "《通俗伤寒论》",
    "ben_cao_yan_yi": "《本草衍义》",
    "xu_ming_yi_lei_an": "《续名医类案》",
    "she_sheng_zhong_miao_fang": "《摄生众妙方》",
    "za_bing_zheng_zhi_xin_yi": "《杂病证治新义》",
    "shang_han_liu_shu": "《伤寒六书》",
    "ci_shi_nan_zhi": "《此事难知》",
}


def _build_formula_full_text(found: dict, composition: list, mods: list, principle_zh: str | None) -> str:
    """将库内治法、组成释义、煎服、加减拼成可读的药方全文。"""
    lines: list[str] = []
    name = found.get("name_zh") or found.get("key") or "未名方"
    lines.append(f"【方名】{name}")

    src = _FORMULA_SOURCE_ZH.get(found.get("source_text_key") or "", found.get("source_text_key") or "")
    chapter = (found.get("source_chapter") or "").strip()
    if src or chapter:
        lines.append("【出处】" + " · ".join(x for x in [src, chapter] if x))

    cat = " · ".join(
        x for x in [found.get("category"), found.get("subcategory")] if x
    )
    if cat:
        lines.append(f"【类别】{cat}")

    if principle_zh:
        lines.append(f"【治法】{principle_zh}")

    if composition:
        lines.append("【组成】")
        for c in composition:
            role = c.get("role") or ""
            nm = c.get("name_zh") or c.get("herb_key") or ""
            dose = c.get("dosage") or ""
            head = f"{nm}"
            if dose:
                head += f" {dose}"
            if role:
                head += f"（{role}）"
            lines.append(f"　{head}")

    desc = (found.get("description_zh") or "").strip()
    fangjie_parts = []
    if desc:
        fangjie_parts.append(desc)
    herb_notes = []
    for c in composition:
        note = (c.get("explanation_zh") or "").strip()
        nm = c.get("name_zh") or ""
        if note:
            herb_notes.append(f"{nm}：{note}" if nm else note)
    if herb_notes:
        fangjie_parts.append("配伍释义：" + "；".join(herb_notes) + "。")
    if fangjie_parts:
        lines.append("【方解】")
        lines.append("　" + "".join(fangjie_parts))

    prep = (found.get("preparation_zh") or "").strip()
    if prep:
        lines.append(f"【煎服】{prep}")

    if mods:
        lines.append("【加减】")
        for m in mods:
            cond = (m.get("condition") or "随证").strip()
            rationale = (m.get("rationale") or "").strip()
            add = "、".join(str(x) for x in (m.get("add") or []) if x)
            rem = "、".join(str(x) for x in (m.get("remove") or []) if x)
            bits = []
            if add:
                bits.append(f"加{add}")
            if rem:
                bits.append(f"去{rem}")
            body = "；".join(bits) if bits else ""
            line = f"　{cond}"
            if rationale:
                line += f"（{rationale}）"
            if body:
                line += f"：{body}"
            lines.append(line)

    return "\n".join(lines)


@app.get("/api/formulas/{id_or_key}")
def get_formula(id_or_key: str, db: Session = Depends(get_db)):
    """方剂全文：治法、组成释义、煎服与加减。"""
    from .analysis import ROLE_ZH, _load_formulas

    q = (id_or_key or "").strip()
    found = None
    for f in _load_formulas():
        if not isinstance(f, dict):
            continue
        if f.get("key") == q or f.get("slug") == q or f.get("name_zh") == q:
            found = f
            break
    if found is None:
        raise HTTPException(status_code=404, detail="未找到该方剂")

    name_map = {h.key: h.name_zh for h in db.scalars(select(Herb)).all()}

    composition = []
    for item in found.get("composition") or []:
        if not isinstance(item, dict):
            continue
        hk = item.get("herb_key")
        role = (item.get("role") or "").strip().lower()
        composition.append(
            {
                "herb_key": hk,
                "name_zh": name_map.get(hk) or hk,
                "role": ROLE_ZH.get(role) or item.get("role"),
                "dosage": item.get("dosage"),
                "explanation_zh": item.get("explanation_zh"),
            }
        )

    mods = []
    for m in found.get("modifications") or []:
        if not isinstance(m, dict):
            continue
        mods.append(
            {
                "condition": m.get("condition"),
                "rationale": m.get("rationale"),
                "add": m.get("add") or [],
                "remove": m.get("remove") or [],
            }
        )

    principle = found.get("treatment_principle") or {}
    principle_zh = principle.get("zh") if isinstance(principle, dict) else principle
    full_text = _build_formula_full_text(found, composition, mods, principle_zh)

    return {
        "key": found.get("key"),
        "slug": found.get("slug"),
        "name_zh": found.get("name_zh"),
        "name_pinyin": found.get("name_pinyin"),
        "category": found.get("category"),
        "subcategory": found.get("subcategory"),
        "source_text_key": found.get("source_text_key"),
        "source_chapter": found.get("source_chapter"),
        "principle": principle_zh,
        "description_zh": found.get("description_zh"),
        "preparation_zh": found.get("preparation_zh"),
        "composition": composition,
        "modifications": mods,
        "full_text_zh": full_text,
    }


@app.get("/api/herbs/{id_or_key}/story")
def get_herb_story(id_or_key: str, db: Session = Depends(get_db)):
    """首页「穿越药」历史名片：典籍线索 + 入方角色。"""
    from .analysis import ROLE_ZH, _load_formulas

    herb = None
    if id_or_key.isdigit():
        herb = db.get(Herb, int(id_or_key))
    if herb is None:
        herb = db.scalar(
            select(Herb).where(or_(Herb.key == id_or_key, Herb.slug == id_or_key))
        )
    if herb is None:
        raise HTTPException(status_code=404, detail="未找到该药材")

    formulas = []
    for f in _load_formulas():
        role_zh = None
        for item in f.get("composition") or []:
            if not isinstance(item, dict):
                continue
            if item.get("herb_key") != herb.key:
                continue
            role = (item.get("role") or "").strip().lower()
            role_zh = ROLE_ZH.get(role) or item.get("role")
            break
        else:
            continue
        formulas.append(
            {
                "key": f.get("key"),
                "name_zh": f.get("name_zh"),
                "category": f.get("category"),
                "subcategory": f.get("subcategory"),
                "role": role_zh,
                "principle": (f.get("treatment_principle") or {}).get("zh"),
            }
        )

    # 君药方优先，再按名称
    role_rank = {"君": 0, "臣": 1, "佐": 2, "使": 3}
    formulas.sort(key=lambda x: (role_rank.get(x.get("role") or "", 9), x.get("name_zh") or ""))

    return {
        "key": herb.key,
        "name_zh": herb.name_zh,
        "name_pinyin": herb.name_pinyin,
        "category": herb.category,
        "siqi": herb.siqi,
        "wuwei": herb.wuwei,
        "guijing": herb.guijing,
        "description": herb.description,
        "classical_refs": _loads(herb.classical_refs),
        "formulas": formulas[:24],
        "formula_count": len(formulas),
        "source": herb.source,
    }


@app.get("/api/herbs/{id_or_key}", response_model=HerbDetail)
def get_herb(id_or_key: str, db: Session = Depends(get_db)):
    herb = None
    if id_or_key.isdigit():
        herb = db.get(Herb, int(id_or_key))
    if herb is None:
        herb = db.scalar(
            select(Herb).where(or_(Herb.key == id_or_key, Herb.slug == id_or_key))
        )
    if herb is None:
        raise HTTPException(status_code=404, detail="未找到该药材")
    return to_detail(herb)


@app.get("/api/stats", response_model=StatsResponse)
def stats(db: Session = Depends(get_db)):
    herbs = db.scalars(select(Herb)).all()
    by_siqi = Counter(h.siqi for h in herbs if h.siqi)
    by_category = Counter(h.category for h in herbs if h.category)
    by_shengjiang = Counter(h.shengjiang for h in herbs if h.shengjiang)

    by_wuwei: Counter[str] = Counter()
    by_guijing: Counter[str] = Counter()
    for h in herbs:
        if h.wuwei:
            for w in h.wuwei.replace(",", "、").split("、"):
                w = w.strip()
                if w:
                    by_wuwei[w] += 1
        if h.guijing:
            for g in h.guijing.replace(",", "、").split("、"):
                g = g.strip()
                if g:
                    by_guijing[g] += 1

    return StatsResponse(
        total_herbs=len(herbs),
        by_siqi=dict(by_siqi),
        by_wuwei=dict(by_wuwei),
        by_guijing=dict(by_guijing),
        by_category=dict(by_category),
        by_shengjiang=dict(by_shengjiang),
    )


@app.get("/api/analysis")
def analysis(db: Session = Depends(get_db)):
    """交叉关系、用量安全、词频、配伍网络与数据质量等可视分析数据。"""
    herbs = db.scalars(select(Herb)).all()
    return build_analysis(herbs)


@app.get("/api/categories", response_model=list[CategoryItem])
def categories(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Herb.category, func.count(Herb.id))
        .where(Herb.category.is_not(None))
        .group_by(Herb.category)
        .order_by(func.count(Herb.id).desc())
    ).all()
    return [CategoryItem(name=r[0], count=r[1]) for r in rows if r[0]]


@app.get("/api/filter/siqi/{value}", response_model=list[HerbBrief])
def filter_siqi(value: str, db: Session = Depends(get_db)):
    items = db.scalars(
        select(Herb).where(Herb.siqi == value).order_by(Herb.name_zh)
    ).all()
    return [HerbBrief.model_validate(h) for h in items]


@app.get("/api/filter/wuwei/{value}", response_model=list[HerbBrief])
def filter_wuwei(value: str, db: Session = Depends(get_db)):
    items = db.scalars(
        select(Herb).where(Herb.wuwei.like(f"%{value}%")).order_by(Herb.name_zh)
    ).all()
    return [HerbBrief.model_validate(h) for h in items]


@app.get("/api/filter/guijing/{value}", response_model=list[HerbBrief])
def filter_guijing(value: str, db: Session = Depends(get_db)):
    items = db.scalars(
        select(Herb).where(Herb.guijing.like(f"%{value}%")).order_by(Herb.name_zh)
    ).all()
    return [HerbBrief.model_validate(h) for h in items]


# ---------------- AI 辨症助手（DeepSeek 代理） ----------------

_ASSISTANT_DISCLAIMER = (
    "以下内容由 AI 依据公开中医药常识生成，仅供学习与参考，"
    "不构成诊断或处方；病情请以线下正规医院医师面诊为准。"
)

_ASSISTANT_SYSTEM_PROMPT = (
    "你是「本草拾珍」图谱的中医药辨症助手。用户会用日常语言描述身体不适或病情，"
    "你的任务是：\n"
    "1. 先把病情归纳为若干「症状标签」（如：风寒感冒、脾胃虚弱、失眠、咳嗽痰多等）。\n"
    "2. 结合中医药常识，给出可能对应的常用中药材（尽量使用规范中药名，便于在图谱中检索），"
    "并简述每味药的作用方向。\n"
    "3. 试探性地拟一个「参考方剂」：列出组成药材及大致克数（成人常规参考量），"
    "并注明煎服/服用方法（如煎法、每日剂次、温服/饭后等）。可优先化裁经典名方（并注明方名来源），"
    "剂量取教材常规范围的中间值即可。\n"
    "4. 安全底线：涉及有毒或药性峻猛之品（如附子、乌头、麻黄、细辛、半夏、大黄等）必须标注需在医师指导下使用"
    "并给出偏保守剂量；孕妇、儿童、老人、慢性病患者一律提示需就医后再用；绝不建议超量或长期自行服用。\n"
    "5. 必须明确声明：该方为「试探性参考」，非个体化处方，不能替代医师面诊；如有需要请到医院就诊。\n"
    "请用简体中文，条理清晰，用简短小标题分段（症状标签 / 可能对应的中药 / 参考方剂（试拟）/ 服用方法 / 就医提示）。"
    "参考方剂建议用「药材 克数」逐行列出。语气温和、克制；遇到危重或急症描述"
    "（如剧烈胸痛、大出血、呼吸困难、高热不退、意识不清等）时，应只建议立即就医，不再给出方剂。"
)


class WorkshopIn(BaseModel):
    keys: list[str]


class AlchemyIn(BaseModel):
    keys: list[str]
    place_key: str | None = None


@app.post("/api/workshop/check")
def workshop_check_api(body: WorkshopIn, db: Session = Depends(get_db)):
    """配伍工坊：禁忌校核、属性对照、共现方与教学结论（学习示意）。"""
    from .workshop import workshop_check

    raw_keys = [str(k).strip() for k in (body.keys or []) if str(k).strip()]
    # 去重保序，最多 3 味
    keys: list[str] = []
    for k in raw_keys:
        if k not in keys:
            keys.append(k)
        if len(keys) >= 3:
            break
    if not keys:
        raise HTTPException(status_code=400, detail="请至少选择 1 味药材")

    herbs: list[Herb] = []
    missing: list[str] = []
    for k in keys:
        h = db.scalar(select(Herb).where(or_(Herb.key == k, Herb.slug == k, Herb.name_zh == k)))
        if h:
            herbs.append(h)
        else:
            missing.append(k)
    if not herbs:
        raise HTTPException(status_code=404, detail="未找到所选药材")

    result = workshop_check(herbs)
    if missing:
        result["missing_keys"] = missing
    return result


def _resolve_herbs_by_keys(db: Session, raw_keys: list[str], limit: int = 12) -> tuple[list[Herb], list[str]]:
    keys: list[str] = []
    for k in raw_keys:
        k = str(k).strip()
        if k and k not in keys:
            keys.append(k)
        if len(keys) >= limit:
            break
    herbs: list[Herb] = []
    missing: list[str] = []
    for k in keys:
        h = db.scalar(select(Herb).where(or_(Herb.key == k, Herb.slug == k, Herb.name_zh == k)))
        if h:
            herbs.append(h)
        else:
            missing.append(k)
    return herbs, missing


@app.post("/api/alchemy/place")
def alchemy_place_api(body: AlchemyIn, db: Session = Depends(get_db)):
    """置入一味药：返回君臣佐使身份与七情提醒（不阻止）。"""
    from .alchemy import place_herb_feedback

    place_key = (body.place_key or "").strip()
    if not place_key:
        raise HTTPException(status_code=400, detail="请指定置入药材 place_key")
    herbs, missing = _resolve_herbs_by_keys(db, body.keys or [], limit=12)
    placed = list(herbs)
    new_h = db.scalar(
        select(Herb).where(or_(Herb.key == place_key, Herb.slug == place_key, Herb.name_zh == place_key))
    )
    if not new_h:
        raise HTTPException(status_code=404, detail="未找到置入药材")
    if all(h.key != new_h.key for h in placed):
        placed.append(new_h)
    result = place_herb_feedback(new_h, placed)
    if missing:
        result["missing_keys"] = missing
    return result


@app.post("/api/alchemy/refine")
def alchemy_refine_api(body: AlchemyIn, db: Session = Depends(get_db)):
    """炼药：方剂覆盖匹配、禁忌毒药判定、全方彩蛋。"""
    from .alchemy import refine

    herbs, missing = _resolve_herbs_by_keys(db, body.keys or [], limit=12)
    if not herbs:
        raise HTTPException(status_code=400, detail="请至少置入 1 味药材")
    result = refine(herbs)
    if missing:
        result["missing_keys"] = missing
    return result


class ConsultIn(BaseModel):
    message: str
    history: list[dict] | None = None


def _call_deepseek(messages: list[dict], timeout: float = 90.0) -> str:
    payload = json.dumps(
        {
            "model": DEEPSEEK_MODEL,
            "messages": messages,
            "temperature": 0.4,
            "stream": False,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{DEEPSEEK_BASE_URL}/chat/completions",
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    choices = data.get("choices") or []
    if not choices:
        raise ValueError("DeepSeek 返回为空")
    return (choices[0].get("message") or {}).get("content") or ""


@app.post("/api/assistant/consult")
def assistant_consult(body: ConsultIn, db: Session = Depends(get_db)):
    """把病情描述转成症状标签并给出用药参考建议（DeepSeek 代理）。"""
    text = (body.message or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="请描述你的不适或病情。")
    if not DEEPSEEK_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="AI 助手未配置密钥：请在 backend/.env 设置 DEEPSEEK_API_KEY 后重启后端。",
        )

    # 提供图谱收录的功效分类，帮助模型使用可被检索的规范药名/方向
    cats = db.execute(
        select(Herb.category, func.count(Herb.id))
        .where(Herb.category.is_not(None))
        .group_by(Herb.category)
        .order_by(func.count(Herb.id).desc())
    ).all()
    cat_names = [c[0] for c in cats if c[0]][:24]
    context_note = (
        "参考：本图谱收录约 "
        + str(db.scalar(select(func.count(Herb.id))) or 0)
        + " 味药材，主要功效分类有："
        + "、".join(cat_names)
        + "。请尽量推荐常见且属于上述范畴的药材。"
    )

    messages: list[dict] = [{"role": "system", "content": _ASSISTANT_SYSTEM_PROMPT}]
    messages.append({"role": "system", "content": context_note})
    for turn in (body.history or [])[-6:]:
        role = turn.get("role")
        content = (turn.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": text})

    try:
        reply = _call_deepseek(messages)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:300] if hasattr(e, "read") else str(e)
        raise HTTPException(status_code=502, detail=f"DeepSeek 接口错误（{e.code}）：{detail}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise HTTPException(status_code=504, detail=f"无法连接 DeepSeek：{e}")
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=502, detail=f"DeepSeek 返回解析失败：{e}")

    return {
        "reply": reply.strip(),
        "disclaimer": _ASSISTANT_DISCLAIMER,
        "model": DEEPSEEK_MODEL,
    }
