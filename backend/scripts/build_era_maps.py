# -*- coding: utf-8 -*-
"""从 historical-basemaps 提取各时期东亚政权疆域，并叠合现代省级示意界线。"""
from __future__ import annotations

import json
import math
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "backend" / "data" / "era_maps"
CHINA_PATH = ROOT / "backend" / "data" / "china.json"
CHINA_FULL_PATH = ROOT / "backend" / "data" / "china_full.json"
CHINA_URLS = [
    "https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json",
    "https://cdn.jsdelivr.net/npm/echarts@4.9.0/map/json/china.json",
]
BASE_URL = "https://cdn.jsdelivr.net/gh/aourednik/historical-basemaps@master/geojson/world_{year}.geojson"

# 东亚关注区（仅用于判断是否保留要素，不做逐点裁剪）
BBOX = (70.0, 15.0, 145.0, 56.0)

ERAS = [
    {
        "id": "donghan",
        "dynasty": "东汉",
        "year": 200,
        "core": ["Han"],
        "neighbors": [],
        "source_note": "historical-basemaps · CE 200 汉疆域",
    },
    {
        "id": "nanchao",
        "dynasty": "南朝",
        "year": 500,
        "core": ["Jin Empire"],
        "neighbors": [],
        "source_note": "historical-basemaps · CE 500 晋/南朝政权",
    },
    {
        "id": "tang",
        "dynasty": "唐",
        "year": 800,
        "core": ["Tang Empire"],
        "neighbors": ["Tibetan Empire"],
        "source_note": "historical-basemaps · CE 800 唐与吐蕃",
    },
    {
        "id": "song",
        "dynasty": "宋",
        "year": 1000,
        "core": ["Song Empire"],
        "neighbors": ["Liao", "Tibet", "Korea"],
        "source_note": "historical-basemaps · CE 1000 宋辽并立",
    },
    {
        "id": "ming",
        "dynasty": "明",
        "year": 1500,
        "core": ["Ming Chinese Empire"],
        "neighbors": ["Tibet", "Korea"],
        "source_note": "historical-basemaps · CE 1500 明疆域",
    },
    {
        "id": "qing",
        "dynasty": "清",
        "year": 1800,
        "core": ["Qing Empire", "Manchu Empire"],
        "neighbors": ["Korea"],
        "source_note": "historical-basemaps · CE 1800 清疆域",
    },
]

NAME_ZH = {
    "Han": "汉",
    "Yueban": "悦般",
    "Jin Empire": "晋",
    "Tang Empire": "唐",
    "Tufan Empire": "吐蕃",
    "Tibetan Empire": "吐蕃",
    "Tibet": "吐蕃/西藏",
    "Uyghurs": "回鹘",
    "Silla": "新罗",
    "Korea": "朝鲜",
    "Song Empire": "宋",
    "Liao": "辽",
    "Khitans": "契丹",
    "Ming Chinese Empire": "明",
    "Qing Empire": "清",
    "Manchu Empire": "清",
    "Sui Empire": "隋",
}


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "HerbaAtlas/1.0"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8"))


def point_in_bbox(lon: float, lat: float) -> bool:
    return BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3]


def ring_intersects_bbox(ring) -> bool:
    for pt in ring:
        if not isinstance(pt, (list, tuple)) or len(pt) < 2:
            continue
        try:
            lon, lat = float(pt[0]), float(pt[1])
        except (TypeError, ValueError):
            continue
        if point_in_bbox(lon, lat):
            return True
    return False


def geom_intersects_bbox(geom: dict) -> bool:
    gtype = geom.get("type")
    coords = geom.get("coordinates") or []
    if gtype == "Polygon":
        return any(ring_intersects_bbox(r) for r in coords)
    if gtype == "MultiPolygon":
        for poly in coords:
            if any(ring_intersects_bbox(r) for r in poly):
                return True
    return False


def simplify_ring(coords, max_pts: int = 220):
    cleaned = []
    for pt in coords:
        if not isinstance(pt, (list, tuple)) or len(pt) < 2:
            continue
        try:
            cleaned.append([float(pt[0]), float(pt[1])])
        except (TypeError, ValueError):
            continue
    if len(cleaned) < 4:
        return []
    if len(cleaned) <= max_pts:
        ring = cleaned
    else:
        step = max(1, len(cleaned) // max_pts)
        ring = cleaned[::step]
        if ring[-1] != cleaned[-1]:
            ring.append(cleaned[-1])
    if ring[0] != ring[-1]:
        ring.append(ring[0][:])
    return ring


def process_geometry(geom: dict):
    if not geom:
        return None
    if not geom_intersects_bbox(geom):
        return None
    gtype = geom.get("type")
    coords = geom.get("coordinates")
    if gtype == "Polygon":
        rings = []
        for ring in coords or []:
            simplified = simplify_ring(ring)
            if len(simplified) >= 4:
                rings.append(simplified)
        if not rings:
            return None
        return {"type": "Polygon", "coordinates": rings}
    if gtype == "MultiPolygon":
        polys = []
        for poly in coords or []:
            rings = []
            for ring in poly:
                simplified = simplify_ring(ring)
                if len(simplified) >= 4:
                    rings.append(simplified)
            if rings:
                polys.append(rings)
        if not polys:
            return None
        return {"type": "MultiPolygon", "coordinates": polys}
    return None


def clip_coords(coords):
    """兼容旧调用：转为数值坐标。"""
    return simplify_ring(coords, max_pts=10000)


def centroid_of_feature(feat: dict):
    geom = feat.get("geometry") or {}
    gtype = geom.get("type")
    coords = geom.get("coordinates")
    pts = []
    if gtype == "Polygon" and coords:
        pts = coords[0]
    elif gtype == "MultiPolygon" and coords:
        pts = coords[0][0]
    if not pts:
        return None
    xs, ys = [], []
    for p in pts:
        if not isinstance(p, (list, tuple)) or len(p) < 2:
            continue
        try:
            xs.append(float(p[0]))
            ys.append(float(p[1]))
        except (TypeError, ValueError):
            continue
    if not xs:
        return None
    return sum(xs) / len(xs), sum(ys) / len(ys)


def ray_cast(lon: float, lat: float, ring) -> bool:
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        intersect = ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi
        )
        if intersect:
            inside = not inside
        j = i
    return inside


def point_in_geom(lon: float, lat: float, geom: dict) -> bool:
    gtype = geom.get("type")
    coords = geom.get("coordinates") or []
    if gtype == "Polygon":
        if not coords:
            return False
        if not ray_cast(lon, lat, coords[0]):
            return False
        for hole in coords[1:]:
            if ray_cast(lon, lat, hole):
                return False
        return True
    if gtype == "MultiPolygon":
        for poly in coords:
            if point_in_geom(lon, lat, {"type": "Polygon", "coordinates": poly}):
                return True
    return False


def merge_core_geoms(features: list[dict]) -> dict | None:
    polys = []
    for f in features:
        g = f.get("geometry")
        if not g:
            continue
        if g["type"] == "Polygon":
            polys.append(g["coordinates"])
        elif g["type"] == "MultiPolygon":
            polys.extend(g["coordinates"])
    if not polys:
        return None
    if len(polys) == 1:
        return {"type": "Polygon", "coordinates": polys[0]}
    return {"type": "MultiPolygon", "coordinates": polys}


def extract_era(world: dict, era: dict, china: dict) -> dict:
    want = set(era["core"] + era["neighbors"])
    picked = []
    for f in world.get("features") or []:
        name = (f.get("properties") or {}).get("NAME") or ""
        if name not in want:
            continue
        geom = process_geometry(f.get("geometry") or {})
        if not geom:
            continue
        role = "core" if name in era["core"] else "neighbor"
        picked.append(
            {
                "type": "Feature",
                "properties": {
                    "name": NAME_ZH.get(name, name),
                    "name_en": name,
                    "role": role,
                    "dynasty": era["dynasty"],
                },
                "geometry": geom,
            }
        )

    core_feats = [f for f in picked if f["properties"]["role"] == "core"]
    core_geom = merge_core_geoms(core_feats)

    # 现代省级示意：重心落入核心疆域内的省
    provinces = []
    if core_geom and china:
        for f in china.get("features") or []:
            name = (f.get("properties") or {}).get("name") or ""
            if not name:
                continue
            c = centroid_of_feature(f)
            if not c:
                continue
            if not point_in_geom(c[0], c[1], core_geom):
                continue
            geom = process_geometry(f.get("geometry") or {})
            if not geom:
                continue
            provinces.append(
                {
                    "type": "Feature",
                    "properties": {
                        "name": name,
                        "role": "province",
                        "dynasty": era["dynasty"],
                    },
                    "geometry": geom,
                }
            )

    features = picked + provinces
    return {
        "type": "FeatureCollection",
        "properties": {
            "id": era["id"],
            "dynasty": era["dynasty"],
            "year": era["year"],
            "source": era["source_note"],
            "attribution": "Historical boundaries © aourednik/historical-basemaps (open data)",
        },
        "features": features,
    }


def load_china() -> dict:
    for path in (CHINA_FULL_PATH, CHINA_PATH):
        if path.is_file():
            raw = path.read_text(encoding="utf-8")
            # 跳过 echarts 压缩格式（坐标非数值）
            if '"coordinates":["@@' in raw or "coordinates\":[\"@@" in raw:
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            feats = data.get("features") or []
            if not feats:
                continue
            sample = ((feats[0].get("geometry") or {}).get("coordinates") or [[[[0]]]])
            # 粗检：第一点是否为数值
            try:
                pt = sample[0][0] if feats[0]["geometry"]["type"] == "MultiPolygon" else sample[0]
                float(pt[0])
                float(pt[1])
                print("use china geo", path.name)
                return data
            except Exception:
                continue

    for url in CHINA_URLS:
        try:
            print("download china", url)
            data = fetch_json(url)
            CHINA_FULL_PATH.write_text(
                json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
            return data
        except Exception as exc:
            print("china download fail", exc)
    return {}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    china = load_china()

    cache: dict[int, dict] = {}
    index = []
    for era in ERAS:
        y = era["year"]
        if y not in cache:
            url = BASE_URL.format(year=y)
            print("download", url)
            cache[y] = fetch_json(url)
        fc = extract_era(cache[y], era, china)
        out = OUT_DIR / f"{era['id']}.json"
        out.write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        size_kb = out.stat().st_size / 1024
        roles = {}
        for f in fc["features"]:
            r = f["properties"].get("role")
            roles[r] = roles.get(r, 0) + 1
        print(f"  -> {era['id']}: {len(fc['features'])} features {roles}, {size_kb:.1f} KB")
        index.append(
            {
                "id": era["id"],
                "dynasty": era["dynasty"],
                "year": era["year"],
                "source": era["source_note"],
                "features": len(fc["features"]),
            }
        )

    (OUT_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("done", OUT_DIR)


if __name__ == "__main__":
    main()
