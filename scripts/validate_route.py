from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

MOVEMENT_TYPES = {"walked", "vehicle", "mixed", "inferred", "unclear"}
CONTINUITY_STATUSES = {"continuous", "gap_before", "gap_after", "isolated", "unclear"}
WALKABILITY_STATUSES = {"book_walkable", "partially_walkable", "not_walkable_as_written", "needs_review"}
MODERN_FOLLOWABILITY = {"likely_followable", "approximate_only", "not_enough_information", "needs_field_check"}


def valid_coord(point: dict[str, Any]) -> bool:
    lat = point.get("lat")
    lng = point.get("lng")
    if lat is None and lng is None:
        return True
    return isinstance(lat, (int, float)) and isinstance(lng, (int, float)) and -90 <= lat <= 90 and -180 <= lng <= 180


def require_enum(seg: dict[str, Any], field: str, allowed: set[str], errors: list[str]) -> None:
    sid = seg.get("id", "<missing-id>")
    value = seg.get(field)
    if value is None:
        errors.append(f"{sid}: missing {field}")
    elif value not in allowed:
        errors.append(f"{sid}: invalid {field}: {value!r}; expected one of {sorted(allowed)}")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/validate_route.py data/route_segments.json", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    segments = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    warnings: list[str] = []
    info: list[str] = []

    orders = [seg.get("order") for seg in segments]
    expected = list(range(1, len(segments) + 1))
    if orders != expected:
        errors.append(f"order must be consecutive: got {orders}, expected {expected}")

    for seg in segments:
        sid = seg.get("id", "<missing-id>")
        for field in ["id", "order", "title"]:
            if not seg.get(field):
                errors.append(f"{sid}: missing {field}")
        for role in ["start", "end"]:
            point = seg.get(role)
            if not isinstance(point, dict) or not point.get("name"):
                errors.append(f"{sid}: missing {role}.name")
            elif not valid_coord(point):
                errors.append(f"{sid}: invalid coordinate for {role} {point.get('name')}")

        refs = seg.get("book_refs") or []
        if not refs:
            errors.append(f"{sid}: missing book_refs")
        for idx, ref in enumerate(refs, start=1):
            if ref.get("page") is None or not ref.get("quote") or not ref.get("note"):
                errors.append(f"{sid}: book_ref #{idx} must include page, quote, note")
            if len(ref.get("quote", "")) > 120:
                warnings.append(f"{sid}: book_ref #{idx} quote longer than 120 chars")

        points = [seg.get("start", {}), *seg.get("via", []), seg.get("end", {})]
        missing_coords = [p.get("name") for p in points if p.get("lat") is None or p.get("lng") is None]
        if missing_coords and not seg.get("review_notes"):
            errors.append(f"{sid}: missing coordinates but no review_notes: {', '.join(filter(None, missing_coords))}")
        for point in points:
            if not valid_coord(point):
                errors.append(f"{sid}: invalid coordinate for {point.get('name')}")

        require_enum(seg, "movement_type", MOVEMENT_TYPES, errors)
        require_enum(seg, "continuity_status", CONTINUITY_STATUSES, errors)
        require_enum(seg, "walkability_status", WALKABILITY_STATUSES, errors)
        require_enum(seg, "modern_followability", MODERN_FOLLOWABILITY, errors)
        if "gap_notes" not in seg:
            errors.append(f"{sid}: missing gap_notes")
        elif not isinstance(seg.get("gap_notes"), list):
            errors.append(f"{sid}: gap_notes must be a list")
        if "do_not_connect_in_gpx" not in seg:
            errors.append(f"{sid}: missing do_not_connect_in_gpx")
        elif not isinstance(seg.get("do_not_connect_in_gpx"), bool):
            errors.append(f"{sid}: do_not_connect_in_gpx must be boolean")
        elif seg.get("do_not_connect_in_gpx") and not seg.get("gap_notes"):
            errors.append(f"{sid}: do_not_connect_in_gpx=true requires gap_notes")

        if seg.get("movement_type") and seg.get("movement_type") != "walked":
            info.append(f"{sid}: movement_type={seg.get('movement_type')}，GPX 应避免把非连续/乘车/补走信息强连。")
        if seg.get("do_not_connect_in_gpx"):
            info.append(f"{sid}: do_not_connect_in_gpx=true，export_gpx.py 应只导出 waypoint，不导出连续 track。")

    movement_counts = Counter(seg.get("movement_type") for seg in segments)
    continuity_counts = Counter(seg.get("continuity_status") for seg in segments)
    walkability_counts = Counter(seg.get("walkability_status") for seg in segments)
    followability_counts = Counter(seg.get("modern_followability") for seg in segments)
    do_not_connect = [seg.get("id") for seg in segments if seg.get("do_not_connect_in_gpx")]

    report = [
        "# 路线校验报告",
        "",
        f"- Generated at: {datetime.now().isoformat(timespec='seconds')}",
        f"- Input: `{path}`",
        f"- Segments: {len(segments)}",
        f"- Errors: {len(errors)}",
        f"- Warnings: {len(warnings)}",
        f"- Info: {len(info)}",
        "",
        "## Errors",
        "",
    ]
    report.extend([f"- {e}" for e in errors] or ["- None"])
    report.extend(["", "## Warnings", ""])
    report.extend([f"- {w}" for w in warnings] or ["- None"])
    report.extend(["", "## Info", ""])
    report.extend([f"- {i}" for i in info] or ["- None"])
    report.extend(["", "## Continuity Field Counts", ""])
    for label, counts, values in [
        ("movement_type", movement_counts, ["walked", "vehicle", "mixed", "inferred", "unclear"]),
        ("continuity_status", continuity_counts, ["continuous", "gap_before", "gap_after", "isolated", "unclear"]),
        (
            "walkability_status",
            walkability_counts,
            ["book_walkable", "partially_walkable", "not_walkable_as_written", "needs_review"],
        ),
        (
            "modern_followability",
            followability_counts,
            ["likely_followable", "approximate_only", "not_enough_information", "needs_field_check"],
        ),
    ]:
        report.append(f"### {label}")
        report.append("")
        for value in values:
            report.append(f"- {value}: {counts.get(value, 0)}")
        report.append("")
    report.extend(
        [
            "## GPX Connection Rules",
            "",
            f"- do_not_connect_in_gpx=true segments: {', '.join(do_not_connect) if do_not_connect else 'None'}",
            "- Validation expectation: export_gpx.py must not emit continuous track segments for these IDs.",
        ]
    )

    out = ROOT / "data" / "validation_report.md"
    out.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
