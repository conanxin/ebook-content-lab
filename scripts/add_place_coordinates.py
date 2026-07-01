#!/usr/bin/env python3
"""Add conservative map coordinates to reading-guide public place indexes."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.lib.project_paths import from_project
except ModuleNotFoundError:
    from lib.project_paths import from_project


VERSION = "v0.7-A14"


def coord(
    lat: float,
    lng: float,
    status: str,
    note: str,
    source_type: str | None = None,
) -> dict[str, Any]:
    return {
        "lat": lat,
        "lng": lng,
        "coordinate_status": status,
        "coordinate_source_type": source_type,
        "coordinate_review_note": note,
    }


# Coordinates are conservative reading-map anchors. Exact point-level claims are
# only made where the public source identifies a specific landmark/site; broader
# city or combined-route labels are marked approximate.
COORDINATES: dict[str, dict[str, Any]] = {
    "娘子关": coord(37.94, 113.88, "approximate_coordinate", "按娘子关关隘/镇域作阅读地图近似点，后续建议补地方官方坐标。"),
    "骊山": coord(34.36, 109.22, "approximate_coordinate", "按骊山景区山体作近似点，具体书中落点待复核。"),
    "西安": coord(34.3416, 108.9398, "public_coordinate", "按西安市城市中心作城市节点坐标。"),
    "半坡": coord(34.279, 109.052, "public_coordinate", "按半坡遗址/博物馆区域作阅读地图坐标。"),
    "碑林": coord(34.257, 108.954, "public_coordinate", "按西安碑林博物馆区域作阅读地图坐标。"),
    "成都": coord(30.5728, 104.0668, "public_coordinate", "按成都市城市中心作城市节点坐标。"),
    "杜甫草堂": coord(30.660, 104.027, "public_coordinate", "按杜甫草堂博物馆区域作阅读地图坐标。"),
    "武侯祠": coord(30.647, 104.048, "public_coordinate", "按成都武侯祠区域作阅读地图坐标。"),
    "青城山": coord(30.905, 103.574, "public_coordinate", "按青城山世界遗产/景区区域作阅读地图坐标。"),
    "乐山大佛": coord(29.547, 103.772, "public_coordinate", "按乐山大佛景区区域作阅读地图坐标。"),
    "峨嵋山脚": coord(29.602, 103.484, "approximate_coordinate", "按峨眉山景区入口地带作近似阅读坐标，具体山脚位置待人工复核。"),
    "昆明车站": coord(25.017, 102.722, "approximate_coordinate", "按昆明站城市交通节点作近似坐标。"),
    "昆明温泉": coord(24.958, 102.45, "approximate_coordinate", "按昆明/安宁温泉方向作近似阅读坐标，具体温泉点位待复核。"),
    "西山": coord(24.965, 102.625, "approximate_coordinate", "按昆明西山/滇池西岸山地作近似坐标。"),
    "石林": coord(24.817, 103.324, "public_coordinate", "按石林喀斯特景区区域作阅读地图坐标。"),
    "贵阳花溪": coord(26.409, 106.670, "approximate_coordinate", "按贵阳花溪区作近似坐标，具体书中地点待复核。"),
    "桂林伏波山": coord(25.284, 110.300, "public_coordinate", "按桂林伏波山景点区域作阅读地图坐标。"),
    "七星山": coord(25.276, 110.318, "approximate_coordinate", "按桂林七星景区区域作近似坐标。"),
    "象鼻山": coord(25.273, 110.292, "public_coordinate", "按桂林象鼻山景点区域作阅读地图坐标。"),
    "漓江": coord(25.167, 110.417, "approximate_coordinate", "漓江为线性水系，按桂林至阳朔游览段作近似阅读坐标。"),
    "阳朔": coord(24.778, 110.497, "public_coordinate", "按阳朔县城/漓江游览节点作阅读地图坐标。"),
    "梧州": coord(23.476, 111.279, "public_coordinate", "按梧州市城市节点作阅读地图坐标。"),
    "肇庆天柱阁": coord(23.05, 112.465, "approximate_coordinate", "当前公开来源只支撑肇庆城市背景，天柱阁精确点位待复核。"),
    "广州中山大学": coord(23.096, 113.293, "approximate_coordinate", "按广州中山大学旧校园/海珠校区方向作近似坐标，具体校区待复核。"),
    "白云山": coord(23.188, 113.297, "public_coordinate", "按广州白云山景区区域作阅读地图坐标。"),
    "漳州": coord(24.513, 117.647, "public_coordinate", "按漳州市城市节点作阅读地图坐标。"),
    "厦门": coord(24.4798, 118.0894, "public_coordinate", "按厦门城市节点作阅读地图坐标。"),
    "福州": coord(26.0745, 119.2965, "public_coordinate", "按福州市城市节点作阅读地图坐标。"),
    "鼓浪屿": coord(24.448, 118.067, "public_coordinate", "按鼓浪屿世界遗产岛屿区域作阅读地图坐标。"),
    "泉州": coord(24.874, 118.675, "public_coordinate", "按泉州世界遗产城市节点作阅读地图坐标。"),
    "福州西湖": coord(26.089, 119.291, "public_coordinate", "按福州西湖公园区域作阅读地图坐标。"),
    "涌泉寺": coord(26.079, 119.392, "public_coordinate", "按福州鼓山涌泉寺区域作阅读地图坐标。"),
    "北雁荡": coord(28.373, 121.061, "approximate_coordinate", "按雁荡山景区北部区域作近似坐标，具体书中路线待复核。"),
    "南雁荡": coord(27.655, 120.123, "approximate_coordinate", "按南雁荡山区域作近似坐标，具体景点范围待复核。"),
    "黄山天都峰排云亭": coord(30.132, 118.166, "approximate_coordinate", "按黄山风景区核心区域作近似坐标，天都峰/排云亭需分点复核。"),
    "青阳九华山": coord(30.478, 117.810, "public_coordinate", "按九华山景区区域作阅读地图坐标。"),
    "安庆小孤山": coord(29.74, 116.17, "approximate_coordinate", "按长江小孤山区域作近似坐标，具体点位待复核。"),
    "鄱阳五老峰": coord(29.56, 116.02, "approximate_coordinate", "按庐山五老峰区域作近似坐标，鄱阳语境待复核。"),
    "三叠瀑": coord(29.55, 115.99, "approximate_coordinate", "按庐山三叠泉瀑布区域作近似坐标。"),
    "南京中山陵": coord(32.064, 118.849, "public_coordinate", "按南京中山陵景区区域作阅读地图坐标。"),
    "玄武湖": coord(32.071, 118.794, "public_coordinate", "按南京玄武湖公园区域作阅读地图坐标。"),
    "苏州园林": coord(31.32, 120.625, "approximate_coordinate", "苏州园林为多点世界遗产，按苏州古城园林区域作近似阅读坐标。"),
    "苏州天平山沧浪亭": coord(31.304, 120.621, "approximate_coordinate", "复合地点，暂按苏州古城园林节点作近似坐标，天平山需另核。"),
    "上海": coord(31.2304, 121.4737, "public_coordinate", "按上海城市中心作城市节点坐标。"),
    "青岛崂山": coord(36.182, 120.600, "public_coordinate", "按青岛崂山景区区域作阅读地图坐标。"),
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def place_name(item: dict[str, Any]) -> str:
    return str(item.get("place_name") or item.get("place") or item.get("name") or "").strip()


def coordinate_payload(place: dict[str, Any]) -> dict[str, Any]:
    name = place_name(place)
    if name in COORDINATES:
        data = dict(COORDINATES[name])
        source_type = data.get("coordinate_source_type") or place.get("source_type") or "other"
        return {
            "coordinates": {"lat": data["lat"], "lng": data["lng"]},
            "coordinate_status": data["coordinate_status"],
            "coordinate_source_name": place.get("source_name") or "公开来源",
            "coordinate_source_url": place.get("source_url"),
            "coordinate_source_type": source_type,
            "coordinate_review_note": data["coordinate_review_note"],
            "updated_in": VERSION,
        }
    return {
        "coordinates": None,
        "coordinate_status": "needs_coordinate_review",
        "coordinate_source_name": None,
        "coordinate_source_url": None,
        "coordinate_source_type": "unknown",
        "coordinate_review_note": "待补充可核验坐标来源；暂不在路线地图中定位。",
        "updated_in": VERSION,
    }


def apply_coordinate(place: dict[str, Any]) -> dict[str, Any]:
    result = dict(place)
    result.update(coordinate_payload(place))
    return result


def build_coordinate_stats(places: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(item.get("coordinate_status") or "needs_coordinate_review") for item in places)
    source_types = Counter(
        str(item.get("coordinate_source_type") or "unknown")
        for item in places
        if item.get("coordinate_status") in {"public_coordinate", "approximate_coordinate"}
    )
    return {
        "version": VERSION,
        "total_place_count": len(places),
        "public_coordinate_count": counts.get("public_coordinate", 0),
        "approximate_coordinate_count": counts.get("approximate_coordinate", 0),
        "needs_coordinate_review_count": counts.get("needs_coordinate_review", 0),
        "coordinate_ready_count": counts.get("public_coordinate", 0) + counts.get("approximate_coordinate", 0),
        "coordinate_source_type_counts": dict(sorted(source_types.items())),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def build_travel_map_nodes(place_index: list[dict[str, Any]]) -> list[dict[str, Any]]:
    nodes = []
    for order, place in enumerate(place_index, start=1):
        nodes.append(
            {
                "order": order,
                "place_name": place_name(place),
                "letters": place.get("letters", []),
                "coordinates": place.get("coordinates"),
                "coordinate_status": place.get("coordinate_status"),
                "source_status": place.get("source_status"),
                "source_name": place.get("source_name"),
                "coordinate_review_note": place.get("coordinate_review_note"),
            }
        )
    return nodes


def sync_place_fields(target: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    result = dict(target)
    for key in [
        "coordinates",
        "coordinate_status",
        "coordinate_source_name",
        "coordinate_source_url",
        "coordinate_source_type",
        "coordinate_review_note",
        "updated_in",
    ]:
        result[key] = source.get(key)
    return result


def render_plan() -> str:
    return "\n".join(
        [
            "# v0.7-A14 Map Coordinates and Mobile Polish Plan",
            "",
            "## A14 Goals",
            "",
            "- Add conservative coordinates for the place route index.",
            "- Improve the paper-map route experience without adding a heavy map SDK.",
            "- Polish mobile reading, filters, collapsible panels, and jump navigation.",
            "",
            "## Coordinate Strategy",
            "",
            "- Use public or approximate coordinates only when a stable public place identity exists.",
            "- Use `public_coordinate` for clear city, landmark, site, or scenic-area anchors.",
            "- Use `approximate_coordinate` for broad areas, composite labels, or route-level reading anchors.",
            "- Use `needs_coordinate_review` when the place is uncertain.",
            "",
            "## Boundary",
            "",
            "A14 does not publish private files, does not edit manual-review results, and does not promote status.",
            "",
            "## A15 Suggestion",
            "",
            "A15 can replace approximate coordinates with verified point sources or start real manual review.",
            "",
        ]
    )


def render_report(stats: dict[str, Any], source_status_counts: Counter[str]) -> str:
    lines = [
        "# Map Mobile Polish Report v0.7-A14",
        "",
        "## Coordinate Coverage",
        "",
        f"- Total places: `{stats['total_place_count']}`",
        f"- Public coordinates: `{stats['public_coordinate_count']}`",
        f"- Approximate coordinates: `{stats['approximate_coordinate_count']}`",
        f"- Needs coordinate review: `{stats['needs_coordinate_review_count']}`",
        "",
        "## Coordinate Source Type Counts",
        "",
    ]
    for key, value in stats["coordinate_source_type_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Place Source Counts",
            "",
            f"- public_source: `{source_status_counts.get('public_source', 0)}`",
            f"- needs_source_review: `{source_status_counts.get('needs_source_review', 0)}`",
            "",
            "## UI Updates",
            "",
            "- Added route-map data for a lightweight paper route map.",
            "- Added coordinate badges for public / approximate / pending status.",
            "- Added mobile-oriented toggles, collapsible panels, and back-to-top navigation.",
            "- Added place filters for source and coordinate status.",
            "",
            "## Boundary Check",
            "",
            "- Public preview state preserved.",
            "- Manual review results unchanged.",
            "- Private source files not published.",
            "- Local build result: to be verified by `npm run build`.",
            "",
            "## Online URL",
            "",
            "- https://conanxin.github.io/ebook-content-lab/#/projects/second-reading-guide",
            "",
        ]
    )
    return "\n".join(lines)


def render_backlog(places: list[dict[str, Any]]) -> str:
    lines = [
        "# Place Coordinate Backlog v0.7-A14",
        "",
        "## Needs Coordinate Review",
        "",
        "| place | letters | note | next check |",
        "|---|---|---|---|",
    ]
    for item in places:
        if item.get("coordinate_status") == "needs_coordinate_review":
            lines.append(
                f"| {place_name(item)} | {'、'.join(item.get('letters', []) or item.get('appears_in_letters', []) or []) or '待复核'} | "
                f"{item.get('coordinate_review_note')} | 查官方文旅、博物馆、OpenStreetMap 或 Wikidata 坐标 |"
            )
    lines.extend(["", "## Approximate Coordinates", "", "| place | status | note |", "|---|---|---|"])
    for item in places:
        if item.get("coordinate_status") == "approximate_coordinate":
            lines.append(f"| {place_name(item)} | approximate_coordinate | {item.get('coordinate_review_note')} |")
    lines.append("")
    return "\n".join(lines)


def build(project: str) -> dict[str, Any]:
    paths = from_project(project)
    overview = read_json(paths.book_overview_json)
    cards_data = read_json(paths.chapter_reading_cards_json)
    questions_data = read_json(paths.reading_questions_json)

    place_index = [apply_coordinate(item) for item in overview.get("place_route_index", []) or []]
    coordinate_by_place = {place_name(item): item for item in place_index}
    overview["place_route_index"] = place_index

    place_then_now = []
    for item in overview.get("place_then_now", []) or []:
        coord_item = coordinate_by_place.get(place_name(item))
        place_then_now.append(sync_place_fields(item, coord_item) if coord_item else apply_coordinate(item))
    overview["place_then_now"] = place_then_now

    chapters = cards_data.get("chapters", [])
    for chapter in chapters:
        chapter_route = []
        for item in chapter.get("route_now", []) or []:
            coord_item = coordinate_by_place.get(place_name(item))
            chapter_route.append(sync_place_fields(item, coord_item) if coord_item else apply_coordinate(item))
        chapter["route_now"] = chapter_route

    timeline = overview.get("route_timeline", []) or []
    for node in timeline:
        node_places = node.get("primary_places", []) or []
        coordinate_ready = sum(
            1
            for name in node_places
            if coordinate_by_place.get(str(name), {}).get("coordinate_status") in {"public_coordinate", "approximate_coordinate"}
        )
        node["coordinate_status_summary"] = {
            "coordinate_ready_count": coordinate_ready,
            "needs_coordinate_review_count": max(0, len(node_places) - coordinate_ready),
            "updated_in": VERSION,
        }
    overview["route_timeline"] = timeline
    overview["travel_map"] = {
        "version": VERSION,
        "map_mode": "paper-route-map",
        "description": "轻量纸面路线图，使用公开或近似坐标帮助阅读，不作为导航轨迹。",
        "nodes": build_travel_map_nodes(place_index),
    }

    stats = build_coordinate_stats(place_index)
    overview["coordinate_stats"] = stats
    overview.setdefault("source_enrichment", {})["map_mobile_polish"] = stats

    payloads = {
        "book_overview.json": overview,
        "chapter_reading_cards.json": cards_data,
        "key_concepts.json": read_json(paths.key_concepts_json),
        "quote_index.json": read_json(paths.quote_index_json),
        "reading_questions.json": questions_data,
    }
    for name, payload in payloads.items():
        write_json(paths.public_path(name), payload)
        write_json(paths.web_project_path(name), payload)

    source_counts = Counter(str(item.get("source_status") or "needs_source_review") for item in place_index)
    paths.report_path("v0.7_a14_map_mobile_polish_plan.md").write_text(render_plan(), encoding="utf-8")
    paths.report_path("map_mobile_polish_report_v0.7_a14.md").write_text(render_report(stats, source_counts), encoding="utf-8")
    paths.report_path("place_coordinate_backlog_v0.7_a14.md").write_text(render_backlog(place_index), encoding="utf-8")
    return stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    stats = build(args.project)
    print("A14 map coordinates added")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
