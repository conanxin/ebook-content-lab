from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEGACY_GAP_SEGMENT_IDS = {"seg-003", "seg-008", "seg-010", "seg-011", "seg-013", "seg-014", "seg-015"}


def load_segments() -> list[dict[str, Any]]:
    return json.loads((ROOT / "data" / "route_segments.json").read_text(encoding="utf-8"))


def pages(seg: dict[str, Any]) -> list[int]:
    return sorted({int(ref["page"]) for ref in seg.get("book_refs", []) if ref.get("page") is not None})


def has_coord(point: dict[str, Any]) -> bool:
    return point.get("lat") is not None and point.get("lng") is not None


def do_not_connect(seg: dict[str, Any]) -> bool:
    value = seg.get("do_not_connect_in_gpx")
    if isinstance(value, bool):
        return value
    return seg.get("id") in LEGACY_GAP_SEGMENT_IDS


def continuity_properties(seg: dict[str, Any]) -> dict[str, Any]:
    return {
        "movement_type": seg.get("movement_type"),
        "continuity_status": seg.get("continuity_status"),
        "walkability_status": seg.get("walkability_status"),
        "modern_followability": seg.get("modern_followability"),
        "do_not_connect_in_gpx": do_not_connect(seg),
        "gap_notes": seg.get("gap_notes", []),
    }


def point_feature(point: dict[str, Any], seg: dict[str, Any], role: str, page: int | None) -> dict[str, Any] | None:
    if not has_coord(point):
        return None
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [point["lng"], point["lat"]]},
        "properties": {
            "name": point.get("name"),
            "segment_id": seg.get("id"),
            "role": role,
            "page": page,
            "coordinate_source": point.get("coordinate_source"),
            "coordinate_confidence": point.get("coordinate_confidence"),
            **continuity_properties(seg),
        },
    }


def main() -> int:
    segments = load_segments()
    route_features = []
    place_features = []

    for seg in segments:
        seg_pages = pages(seg)
        point_chain = [seg["start"], *seg.get("via", []), seg["end"]]
        coords = [[p["lng"], p["lat"]] for p in point_chain if has_coord(p)]
        route_gap = do_not_connect(seg)
        missing_geometry = route_gap or len(coords) < 2 or len(coords) != len(point_chain)
        coordinate_states = [p.get("coordinate_confidence", "missing") for p in point_chain]
        if "missing" in coordinate_states:
            coordinate_confidence = "missing"
        elif "approximate" in coordinate_states:
            coordinate_confidence = "approximate"
        else:
            coordinate_confidence = "verified"
        route_features.append(
            {
                "type": "Feature",
                "geometry": None if missing_geometry else {"type": "LineString", "coordinates": coords},
                "properties": {
                    "segment_id": seg.get("id"),
                    "order": seg.get("order"),
                    "title": seg.get("title"),
                    "start_name": seg.get("start", {}).get("name"),
                    "end_name": seg.get("end", {}).get("name"),
                    "pages": seg_pages,
                    "confidence": seg.get("confidence"),
                    "coordinate_confidence": coordinate_confidence,
                    "route_summary": seg.get("route_summary"),
                    "missing_geometry": missing_geometry,
                    "route_gap": route_gap,
                    **continuity_properties(seg),
                },
            }
        )
        first_page = seg_pages[0] if seg_pages else None
        for role, point in [("start", seg["start"]), ("end", seg["end"])]:
            feature = point_feature(point, seg, role, first_page)
            if feature:
                place_features.append(feature)
        for point in seg.get("via", []):
            feature = point_feature(point, seg, "via", first_page)
            if feature:
                place_features.append(feature)

    (ROOT / "data" / "route.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": route_features}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (ROOT / "data" / "route_places.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": place_features}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {ROOT / 'data' / 'route.geojson'}")
    print(f"Wrote {ROOT / 'data' / 'route_places.geojson'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
