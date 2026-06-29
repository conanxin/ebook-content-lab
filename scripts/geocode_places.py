from __future__ import annotations

import argparse
import csv
import json
import math
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]


# Conservative helper gazetteer for common modern anchors along the Beijing-Shangdu corridor.
# These coordinates are only for map display and must not be used to change route order.
GAZETTEER: dict[str, dict[str, Any]] = {
    "北京": {"lat": 39.9042, "lng": 116.4074, "source": "manual modern city centroid", "confidence": "approximate"},
    "大都": {"lat": 39.9389, "lng": 116.3656, "source": "manual approximate Yuan Dadu site area, Beijing", "confidence": "approximate"},
    "元大都": {"lat": 39.9389, "lng": 116.3656, "source": "manual approximate Yuan Dadu site area, Beijing", "confidence": "approximate"},
    "蓝旗营": {"lat": 39.9959, "lng": 116.3204, "source": "manual modern place approximation", "confidence": "approximate"},
    "中关村": {"lat": 39.9837, "lng": 116.3162, "source": "manual modern place approximation", "confidence": "approximate"},
    "海淀": {"lat": 39.9599, "lng": 116.2981, "source": "manual modern district centroid", "confidence": "approximate"},
    "航天城": {"lat": 40.0674, "lng": 116.2563, "source": "manual modern place approximation", "confidence": "approximate"},
    "南沙河": {"lat": 40.104, "lng": 116.256, "source": "manual modern river crossing approximation", "confidence": "approximate"},
    "南玉河": {"lat": 40.118, "lng": 116.195, "source": "manual modern village approximation", "confidence": "approximate"},
    "昌平": {"lat": 40.2207, "lng": 116.2312, "source": "manual modern district center", "confidence": "approximate"},
    "巩华城": {"lat": 40.1303, "lng": 116.2855, "source": "manual historic site approximation", "confidence": "approximate"},
    "沙河": {"lat": 40.148, "lng": 116.288, "source": "manual modern town approximation", "confidence": "approximate"},
    "南口": {"lat": 40.239, "lng": 116.128, "source": "manual modern town approximation", "confidence": "approximate"},
    "居庸关": {"lat": 40.2884, "lng": 116.0697, "source": "manual modern scenic/historic site", "confidence": "verified"},
    "八达岭": {"lat": 40.3598, "lng": 116.0203, "source": "manual modern scenic/historic site", "confidence": "verified"},
    "延庆": {"lat": 40.4568, "lng": 115.9749, "source": "manual modern district center", "confidence": "approximate"},
    "康庄": {"lat": 40.374, "lng": 115.905, "source": "manual modern town approximation", "confidence": "approximate"},
    "怀来": {"lat": 40.4154, "lng": 115.5177, "source": "manual modern county center", "confidence": "approximate"},
    "鸡鸣驿": {"lat": 40.457, "lng": 115.276, "source": "manual historic post town approximation", "confidence": "approximate"},
    "宣化": {"lat": 40.608, "lng": 115.064, "source": "manual modern district center", "confidence": "approximate"},
    "张家口": {"lat": 40.8244, "lng": 114.8875, "source": "manual modern city center", "confidence": "approximate"},
    "张北": {"lat": 41.159, "lng": 114.715, "source": "manual modern county center", "confidence": "approximate"},
    "野狐岭": {"lat": 41.041, "lng": 114.832, "source": "manual pass/area approximation", "confidence": "approximate"},
    "崇礼": {"lat": 40.974, "lng": 115.282, "source": "manual modern district center", "confidence": "approximate"},
    "桦皮岭": {"lat": 41.05, "lng": 115.43, "source": "manual mountain pass approximation", "confidence": "approximate"},
    "沽源": {"lat": 41.669, "lng": 115.688, "source": "manual modern county center", "confidence": "approximate"},
    "闪电河": {"lat": 41.78, "lng": 115.95, "source": "manual river/area approximation", "confidence": "approximate"},
    "多伦": {"lat": 42.203, "lng": 116.485, "source": "manual modern county center", "confidence": "approximate"},
    "正蓝旗": {"lat": 42.245, "lng": 116.003, "source": "manual modern banner seat approximation", "confidence": "approximate"},
    "上都": {"lat": 42.358, "lng": 116.185, "source": "manual approximate Xanadu/Shangdu ruins", "confidence": "approximate"},
    "元上都遗址": {"lat": 42.358, "lng": 116.185, "source": "manual approximate Xanadu/Shangdu ruins", "confidence": "approximate"},
    "上都遗址": {"lat": 42.358, "lng": 116.185, "source": "manual approximate Xanadu/Shangdu ruins", "confidence": "approximate"},
    "健德门": {"lat": 39.976, "lng": 116.381, "source": "manual approximate Yuan Dadu Jiandemen area", "confidence": "approximate"},
    "明德门": {"lat": 42.357, "lng": 116.188, "source": "manual approximate Shangdu Mingdemen area", "confidence": "approximate"},
    "小月河": {"lat": 40.008, "lng": 116.37, "source": "manual modern river corridor approximation", "confidence": "approximate"},
    "清河": {"lat": 40.035, "lng": 116.34, "source": "manual modern place/river approximation", "confidence": "approximate"},
    "广济桥": {"lat": 40.04, "lng": 116.34, "source": "manual historic bridge area approximation", "confidence": "approximate"},
    "皇后店": {"lat": 40.115, "lng": 116.245, "source": "manual modern village approximation", "confidence": "approximate"},
    "皂甲屯": {"lat": 40.128, "lng": 116.186, "source": "manual modern village approximation", "confidence": "approximate"},
    "北玉河村": {"lat": 40.143, "lng": 116.177, "source": "manual modern village approximation", "confidence": "approximate"},
    "南玉河村": {"lat": 40.118, "lng": 116.195, "source": "manual modern village approximation", "confidence": "approximate"},
    "昌平镇": {"lat": 40.2207, "lng": 116.2312, "source": "manual modern town center", "confidence": "approximate"},
    "旧县村": {"lat": 40.252, "lng": 116.18, "source": "manual modern village approximation", "confidence": "approximate"},
    "龙虎台村": {"lat": 40.276, "lng": 116.153, "source": "manual modern village approximation", "confidence": "approximate"},
    "居庸关云台": {"lat": 40.288, "lng": 116.068, "source": "manual historic site approximation", "confidence": "approximate"},
    "弹琴峡": {"lat": 40.305, "lng": 116.06, "source": "manual gorge area approximation", "confidence": "approximate"},
    "水关长城": {"lat": 40.333, "lng": 116.035, "source": "manual modern scenic site approximation", "confidence": "approximate"},
    "八达岭关城": {"lat": 40.3598, "lng": 116.0203, "source": "manual modern scenic/historic site", "confidence": "verified"},
    "岔道城": {"lat": 40.365, "lng": 115.995, "source": "manual historic village approximation", "confidence": "approximate"},
    "小泥河村": {"lat": 40.401, "lng": 115.975, "source": "manual modern village approximation", "confidence": "approximate"},
    "大泥河村": {"lat": 40.414, "lng": 115.957, "source": "manual modern village approximation", "confidence": "approximate"},
    "大榆树镇": {"lat": 40.432, "lng": 115.94, "source": "manual modern town approximation", "confidence": "approximate"},
    "延庆旧县镇": {"lat": 40.497, "lng": 116.05, "source": "manual modern town approximation", "confidence": "approximate"},
    "车坊": {"lat": 40.535, "lng": 116.07, "source": "manual modern village approximation", "confidence": "approximate"},
    "黑峪口村": {"lat": 40.58, "lng": 116.065, "source": "manual modern village approximation", "confidence": "approximate"},
    "盘云岭": {"lat": 40.64, "lng": 116.05, "source": "manual mountain pass approximation", "confidence": "approximate"},
    "燕山天池宾馆": {"lat": 40.624, "lng": 115.93, "source": "manual lodging area approximation near Baihepu Reservoir", "confidence": "approximate"},
    "白河堡水库": {"lat": 40.624, "lng": 115.93, "source": "manual reservoir approximation", "confidence": "approximate"},
    "白河河谷": {"lat": 40.68, "lng": 115.9, "source": "manual river valley approximation", "confidence": "approximate"},
    "骆驼山": {"lat": 40.73, "lng": 115.86, "source": "manual village/mountain area approximation", "confidence": "approximate"},
    "郑家窑村": {"lat": 40.79, "lng": 115.8, "source": "manual modern village approximation", "confidence": "approximate"},
    "长伸地村": {"lat": 40.855, "lng": 115.73, "source": "manual modern village approximation", "confidence": "approximate"},
    "镇虏楼": {"lat": 40.855, "lng": 115.73, "source": "manual historic tower near Changshendi approximation", "confidence": "approximate"},
    "巡检司村": {"lat": 40.885, "lng": 115.67, "source": "manual modern village approximation", "confidence": "approximate"},
    "不堡子村": {"lat": 40.91, "lng": 115.62, "source": "manual OCR-normalized village approximation", "confidence": "approximate"},
    "红沙梁": {"lat": 40.93, "lng": 115.58, "source": "manual pass/ridge approximation", "confidence": "approximate"},
    "小堡村": {"lat": 40.95, "lng": 115.55, "source": "manual modern village approximation", "confidence": "approximate"},
    "龙门所镇": {"lat": 40.98, "lng": 115.49, "source": "manual modern town approximation", "confidence": "approximate"},
    "龙门所": {"lat": 40.98, "lng": 115.49, "source": "manual modern town approximation", "confidence": "approximate"},
    "巴图营大桥": {"lat": 40.96, "lng": 115.5, "source": "manual bridge area approximation", "confidence": "approximate"},
    "塘子庙": {"lat": 40.99, "lng": 115.42, "source": "manual hot spring village approximation", "confidence": "approximate"},
    "东万口乡": {"lat": 41.05, "lng": 115.32, "source": "manual modern township approximation", "confidence": "approximate"},
    "白草镇": {"lat": 41.09, "lng": 115.22, "source": "manual modern town approximation", "confidence": "approximate"},
    "三道川村": {"lat": 41.14, "lng": 115.18, "source": "manual modern village approximation", "confidence": "approximate"},
    "禹龙山村": {"lat": 41.18, "lng": 115.13, "source": "manual modern village approximation", "confidence": "approximate"},
    "山神庙村": {"lat": 41.22, "lng": 115.06, "source": "manual modern village approximation", "confidence": "approximate"},
    "黑龙山村": {"lat": 41.25, "lng": 115.02, "source": "manual modern village approximation", "confidence": "approximate"},
    "南沟门": {"lat": 41.29, "lng": 114.98, "source": "manual valley entrance approximation", "confidence": "approximate"},
    "老掌沟": {"lat": 41.34, "lng": 114.94, "source": "manual valley/scenic area approximation", "confidence": "approximate"},
    "沟门村": {"lat": 41.38, "lng": 114.94, "source": "manual modern village approximation", "confidence": "approximate"},
    "前坝村": {"lat": 41.42, "lng": 114.95, "source": "manual modern village approximation", "confidence": "approximate"},
    "黄土坑村": {"lat": 41.46, "lng": 114.97, "source": "manual modern village approximation", "confidence": "approximate"},
    "雷大道村": {"lat": 41.49, "lng": 114.99, "source": "manual modern village approximation", "confidence": "approximate"},
    "三间房村": {"lat": 41.53, "lng": 115.03, "source": "manual modern village approximation", "confidence": "approximate"},
    "小厂镇": {"lat": 41.57, "lng": 115.07, "source": "manual modern town approximation", "confidence": "approximate"},
    "馒头山村": {"lat": 41.6, "lng": 115.09, "source": "manual OCR-normalized village approximation", "confidence": "approximate"},
    "小南滩村": {"lat": 41.63, "lng": 115.11, "source": "manual modern village approximation", "confidence": "approximate"},
    "石柱村": {"lat": 41.66, "lng": 115.14, "source": "manual OCR-normalized village approximation", "confidence": "approximate"},
    "石头城水库": {"lat": 41.69, "lng": 115.17, "source": "manual reservoir approximation", "confidence": "approximate"},
    "石头城村": {"lat": 41.715, "lng": 115.18, "source": "manual modern village approximation", "confidence": "approximate"},
    "牛群头": {"lat": 41.72, "lng": 115.2, "source": "manual historic site area approximation", "confidence": "approximate"},
    "五花草甸": {"lat": 41.75, "lng": 115.31, "source": "manual scenic area approximation", "confidence": "approximate"},
    "河东村": {"lat": 41.66, "lng": 115.66, "source": "manual modern village approximation near Guyuan", "confidence": "approximate"},
    "闪电河水库": {"lat": 41.66, "lng": 115.7, "source": "manual reservoir approximation", "confidence": "approximate"},
    "梳妆楼": {"lat": 41.69, "lng": 115.78, "source": "manual historic site approximation", "confidence": "approximate"},
    "沽源县城": {"lat": 41.669, "lng": 115.688, "source": "manual modern county center", "confidence": "approximate"},
    "沽源镇": {"lat": 41.669, "lng": 115.688, "source": "manual modern county center", "confidence": "approximate"},
    "察罕脑儿": {"lat": 41.72, "lng": 115.86, "source": "manual historic lake/palace area approximation", "confidence": "approximate"},
    "小宏城子": {"lat": 41.73, "lng": 115.86, "source": "manual historic site approximation", "confidence": "approximate"},
    "大宏城子": {"lat": 41.74, "lng": 115.82, "source": "manual historic site approximation", "confidence": "approximate"},
    "水泉淖尔": {"lat": 41.78, "lng": 115.93, "source": "manual lake approximation", "confidence": "approximate"},
    "转佛庙": {"lat": 41.83, "lng": 116.03, "source": "manual modern village approximation", "confidence": "approximate"},
    "马神庙村": {"lat": 41.88, "lng": 116.08, "source": "manual modern village approximation", "confidence": "approximate"},
    "塞北管理区": {"lat": 41.91, "lng": 116.12, "source": "manual modern area approximation", "confidence": "approximate"},
    "黄土湾村": {"lat": 41.96, "lng": 116.16, "source": "manual modern village approximation", "confidence": "approximate"},
    "河北内蒙古分界线": {"lat": 42.02, "lng": 116.22, "source": "manual boundary crossing approximation", "confidence": "approximate"},
    "明安驿": {"lat": 42.03, "lng": 116.24, "source": "manual historic post station area approximation", "confidence": "approximate"},
    "李陵台": {"lat": 42.09, "lng": 116.28, "source": "manual historic site approximation", "confidence": "approximate"},
    "李陵台遗址": {"lat": 42.09, "lng": 116.28, "source": "manual historic site approximation", "confidence": "approximate"},
    "黑城子镇": {"lat": 42.13, "lng": 116.33, "source": "manual modern town approximation", "confidence": "approximate"},
    "黑城子": {"lat": 42.13, "lng": 116.33, "source": "manual modern town approximation", "confidence": "approximate"},
    "滦河东岸沙丘": {"lat": 42.15, "lng": 116.32, "source": "manual dunes area approximation", "confidence": "approximate"},
    "梁河东岸沙丘": {"lat": 42.15, "lng": 116.32, "source": "manual OCR-normalized dunes area approximation", "confidence": "approximate"},
    "四郎城": {"lat": 42.24, "lng": 116.08, "source": "manual historic site approximation", "confidence": "approximate"},
    "上都镇": {"lat": 42.245, "lng": 116.003, "source": "manual modern banner seat approximation", "confidence": "approximate"},
    "上都音高勒大桥": {"lat": 42.28, "lng": 116.08, "source": "manual bridge approximation on Shangdu Gol", "confidence": "approximate"},
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_name(name: str | None) -> str:
    return (name or "").strip().replace("（", "(").split("(")[0].strip()


def haversine_km(a: dict[str, Any], b: dict[str, Any]) -> float | None:
    if a.get("lat") is None or a.get("lng") is None or b.get("lat") is None or b.get("lng") is None:
        return None
    lat1, lon1, lat2, lon2 = map(math.radians, [a["lat"], a["lng"], b["lat"], b["lng"]])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0088 * 2 * math.asin(math.sqrt(h))


def maybe_geocode_nominatim(name: str) -> dict[str, Any] | None:
    query = f"{name}, China"
    params = urlencode({"q": query, "format": "jsonv2", "limit": "1"})
    req = Request(
        f"https://nominatim.openstreetmap.org/search?{params}",
        headers={"User-Agent": "dadu-shangdu-route-personal-project/0.1"},
    )
    try:
        with urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    if not data:
        return None
    item = data[0]
    return {
        "lat": float(item["lat"]),
        "lng": float(item["lon"]),
        "source": f"Nominatim/OpenStreetMap search: {query}",
        "confidence": "approximate",
    }


def geocode_point(point: dict[str, Any], use_web: bool) -> tuple[dict[str, Any], str | None]:
    name = normalize_name(point.get("name"))
    if not name:
        point["coordinate_confidence"] = "missing"
        return point, "empty place name"
    if point.get("lat") is not None and point.get("lng") is not None:
        return point, None
    hit = GAZETTEER.get(name)
    if hit is None:
        for key, value in GAZETTEER.items():
            if key in name or name in key:
                hit = value
                break
    if hit is None and use_web:
        time.sleep(1.1)
        hit = maybe_geocode_nominatim(name)
    if hit:
        point["lat"] = hit["lat"]
        point["lng"] = hit["lng"]
        point["coordinate_source"] = hit["source"]
        point["coordinate_confidence"] = hit["confidence"]
        return point, None
    point["lat"] = None
    point["lng"] = None
    point["coordinate_source"] = None
    point["coordinate_confidence"] = "missing"
    return point, f"missing coordinate: {name}"


def read_candidates(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_candidates(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "name",
        "segment_id",
        "role",
        "page",
        "evidence",
        "lat",
        "lng",
        "coordinate_source",
        "coordinate_confidence",
        "notes",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments", type=Path, default=ROOT / "data" / "route_segments.draft.json")
    parser.add_argument("--places", type=Path, default=ROOT / "data" / "place_candidates.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "route_segments.json")
    parser.add_argument("--use-web", action="store_true", help="Use Nominatim for names missing from the local gazetteer.")
    args = parser.parse_args()

    segments = load_json(args.segments)
    missing_notes: list[str] = []

    for seg in segments:
        for role in ["start", "end"]:
            point, note = geocode_point(seg[role], args.use_web)
            seg[role] = point
            if note:
                missing_notes.append(f"- {seg['id']} {role}: {note}")
        for idx, point in enumerate(seg.get("via", [])):
            point, note = geocode_point(point, args.use_web)
            seg["via"][idx] = point
            if note:
                missing_notes.append(f"- {seg['id']} via: {note}")

        points = [seg["start"], *seg.get("via", []), seg["end"]]
        total = 0.0
        complete = True
        for a, b in zip(points, points[1:]):
            km = haversine_km(a, b)
            if km is None:
                complete = False
                break
            total += km
        seg["distance_km_computed"] = round(total, 2) if complete and len(points) >= 2 else None
        coord_states = [p.get("coordinate_confidence", "missing") for p in points]
        if "missing" in coord_states:
            seg.setdefault("review_notes", []).append("本段存在缺坐标地点，地图几何不完整。")

    candidate_rows = read_candidates(args.places)
    updated_candidates: list[dict[str, Any]] = []
    for row in candidate_rows:
        point = {
            "name": row.get("name"),
            "lat": float(row["lat"]) if row.get("lat") else None,
            "lng": float(row["lng"]) if row.get("lng") else None,
            "coordinate_source": row.get("coordinate_source") or None,
            "coordinate_confidence": row.get("coordinate_confidence") or "missing",
        }
        point, note = geocode_point(point, args.use_web)
        updated = {**row, **point}
        if note and note not in (row.get("notes") or ""):
            updated["notes"] = ((row.get("notes") or "") + f"; {note}").strip("; ")
        updated_candidates.append(updated)
    if updated_candidates:
        write_candidates(args.places, updated_candidates)

    save_json(args.output, segments)

    report = [
        "# 坐标补充报告",
        "",
        f"- Generated at: {datetime.now().isoformat(timespec='seconds')}",
        f"- 输入路线: `{args.segments}`",
        f"- 输出路线: `{args.output}`",
        f"- 候选地名: `{args.places}`",
        f"- 使用在线 Nominatim: {args.use_web}",
        "",
        "## 坐标规则",
        "",
        "- 坐标只用于现代地图辅助定位，不作为书中路线证据。",
        "- 脚本不改变路线顺序、起点、终点或途经地列表。",
        "",
        "## 缺失坐标",
        "",
    ]
    report.extend(missing_notes if missing_notes else ["- 无"])
    (ROOT / "data" / "geocoding_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    notes_path = ROOT / "data" / "review_notes.md"
    existing = notes_path.read_text(encoding="utf-8") if notes_path.exists() else "# 复核说明\n"
    addition = "\n\n## 坐标补充复核\n\n" + ("\n".join(missing_notes) if missing_notes else "- 本轮没有新增缺坐标项。") + "\n"
    if "## 坐标补充复核" not in existing:
        notes_path.write_text(existing.rstrip() + addition, encoding="utf-8")

    print(f"Wrote {args.output}")
    print(f"Wrote {ROOT / 'data' / 'geocoding_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
