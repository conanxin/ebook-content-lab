from __future__ import annotations

import argparse
import html
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEGACY_GAP_SEGMENT_IDS = {"seg-003", "seg-008", "seg-010", "seg-011", "seg-013", "seg-014", "seg-015"}


def has_coord(point: dict[str, Any]) -> bool:
    return point.get("lat") is not None and point.get("lng") is not None


def do_not_connect(seg: dict[str, Any]) -> bool:
    value = seg.get("do_not_connect_in_gpx")
    if isinstance(value, bool):
        return value
    return seg.get("id") in LEGACY_GAP_SEGMENT_IDS


def role_label(role: str, index: int | None = None) -> str:
    if role == "start":
        return "起点"
    if role == "end":
        return "终点"
    return f"途经{index}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("segments", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    segments = json.loads(args.segments.read_text(encoding="utf-8"))
    missing: list[str] = []
    skipped_track: list[str] = []
    waypoints: list[str] = []
    track_segments: list[str] = []
    do_not_connect_ids: list[str] = []

    for seg in segments:
        points: list[tuple[str, dict[str, Any]]] = [("start", seg["start"])]
        points.extend((f"via-{i + 1}", point) for i, point in enumerate(seg.get("via", [])))
        points.append(("end", seg["end"]))
        trkpts = []
        for role, point in points:
            if role.startswith("via-"):
                label = role_label("via", int(role.split("-", 1)[1]))
            else:
                label = role_label(role)
            if has_coord(point):
                name = f"{seg['order']:02d} {label} {point.get('name')}"
                desc = f"{seg.get('title')} | {seg.get('route_summary', '')}"
                waypoints.append(
                    f'  <wpt lat="{point["lat"]}" lon="{point["lng"]}"><name>{html.escape(name)}</name><desc>{html.escape(desc)}</desc></wpt>'
                )
                trkpts.append(f'      <trkpt lat="{point["lat"]}" lon="{point["lng"]}"><name>{html.escape(name)}</name></trkpt>')
            else:
                missing.append(f"- {seg['id']} {label} {point.get('name')}: 缺坐标")

        if do_not_connect(seg):
            do_not_connect_ids.append(seg["id"])
            note = "；".join(seg.get("gap_notes") or []) or "存在乘车/补走/断点复核说明，仅导出 waypoint，不导出连续 track。"
            skipped_track.append(f"- {seg['id']} {seg.get('title')}: {note}")
        elif len(trkpts) >= 2:
            track_segments.append("    <trkseg>\n" + "\n".join(trkpts) + "\n    </trkseg>")

    gpx = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<gpx version="1.1" creator="dadu-shangdu-route" xmlns="http://www.topografix.com/GPX/1/1">',
        "  <metadata>",
        "    <name>《从大都到上都》徒步路线图解</name>",
        f"    <time>{datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')}</time>",
        "  </metadata>",
        *waypoints,
        "  <trk>",
        "    <name>从大都到上都</name>",
        *track_segments,
        "  </trk>",
        "</gpx>",
        "",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(gpx), encoding="utf-8")

    public_dir = ROOT / "web" / "public" / "data"
    public_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.output, public_dir / "route.gpx")

    report = [
        "# GPX 导出报告",
        "",
        f"- Generated at: {datetime.now().isoformat(timespec='seconds')}",
        f"- Input: `{args.segments}`",
        f"- Output: `{args.output}`",
        f"- Waypoints exported: {len(waypoints)}",
        f"- Track segments exported: {len(track_segments)}",
        f"- do_not_connect_in_gpx=true segments: {', '.join(do_not_connect_ids) if do_not_connect_ids else '无'}",
        "",
        "## 缺坐标未导出项",
        "",
    ]
    report.extend(missing or ["- 无"])
    report.extend(["", "## 因路线断点未导出连续 track", ""])
    report.extend(skipped_track or ["- 无"])
    (ROOT / "data" / "gpx_export_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    validation_path = ROOT / "data" / "validation_report.md"
    if validation_path.exists() and missing:
        with validation_path.open("a", encoding="utf-8") as f:
            f.write("\n## GPX 缺坐标未导出项\n\n")
            f.write("\n".join(missing) + "\n")

    print(f"Wrote {args.output}")
    print(f"Copied {public_dir / 'route.gpx'}")
    print(f"Wrote {ROOT / 'data' / 'gpx_export_report.md'}")
    print(f"waypoints={len(waypoints)} track_segments={len(track_segments)} skipped={len(skipped_track)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
