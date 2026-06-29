from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


CONTINUITY_FIELDS = [
    "movement_type",
    "continuity_status",
    "walkability_status",
    "modern_followability",
    "gap_notes",
    "do_not_connect_in_gpx",
]

VALID_VALUES = {
    "movement_type": {"walked", "vehicle", "mixed", "inferred", "unclear"},
    "continuity_status": {"continuous", "gap_before", "gap_after", "isolated", "unclear"},
    "walkability_status": {"book_walkable", "partially_walkable", "not_walkable_as_written", "needs_review"},
    "modern_followability": {"likely_followable", "approximate_only", "not_enough_information", "needs_field_check"},
}

ANNOTATIONS: dict[str, dict[str, Any]] = {
    "seg-001": {
        "movement_type": "walked",
        "continuity_status": "continuous",
        "walkability_status": "book_walkable",
        "modern_followability": "approximate_only",
        "gap_notes": [
            "书中显示第一日行走结束后另有乘车南返；本段 GPX 只表达健德门至皂甲屯的步行段，不连接乘车路线。"
        ],
        "do_not_connect_in_gpx": False,
    },
    "seg-002": {
        "movement_type": "walked",
        "continuity_status": "continuous",
        "walkability_status": "book_walkable",
        "modern_followability": "approximate_only",
        "gap_notes": [],
        "do_not_connect_in_gpx": False,
    },
    "seg-003": {
        "movement_type": "mixed",
        "continuity_status": "gap_after",
        "walkability_status": "partially_walkable",
        "modern_followability": "needs_field_check",
        "gap_notes": [
            "第98页及复核备注显示当天行走未连续到延庆旧县镇，后续存在乘车返回/休整信息。",
            "书中存在乘车/断点复核说明，不应与前后段强行连成连续徒步轨迹。",
            "该段只导出 waypoint，不作为连续 GPX track。",
        ],
        "do_not_connect_in_gpx": True,
    },
    "seg-004": {
        "movement_type": "walked",
        "continuity_status": "gap_before",
        "walkability_status": "book_walkable",
        "modern_followability": "approximate_only",
        "gap_notes": [
            "本段从旧县镇开始步行；与上一段之间存在已在 seg-003 标记的断点。"
        ],
        "do_not_connect_in_gpx": False,
    },
    "seg-005": {
        "movement_type": "walked",
        "continuity_status": "continuous",
        "walkability_status": "book_walkable",
        "modern_followability": "approximate_only",
        "gap_notes": [
            "部分中途地名曾因 OCR 和标题页证据不足被移入复核说明；GPX 仅按已保留正文证据和坐标生成参考线。"
        ],
        "do_not_connect_in_gpx": False,
    },
    "seg-006": {
        "movement_type": "walked",
        "continuity_status": "continuous",
        "walkability_status": "book_walkable",
        "modern_followability": "approximate_only",
        "gap_notes": [],
        "do_not_connect_in_gpx": False,
    },
    "seg-007": {
        "movement_type": "walked",
        "continuity_status": "continuous",
        "walkability_status": "book_walkable",
        "modern_followability": "approximate_only",
        "gap_notes": [],
        "do_not_connect_in_gpx": False,
    },
    "seg-008": {
        "movement_type": "mixed",
        "continuity_status": "gap_after",
        "walkability_status": "partially_walkable",
        "modern_followability": "needs_field_check",
        "gap_notes": [
            "第207页及复核备注显示进入老掌沟后联系车辆接应，步行终点与住宿点之间存在非步行接续。",
            "书中存在乘车/补走信息，不应与前后段强行连成连续徒步轨迹。",
            "该段只导出 waypoint，不作为连续 GPX track。",
        ],
        "do_not_connect_in_gpx": True,
    },
    "seg-009": {
        "movement_type": "mixed",
        "continuity_status": "gap_before",
        "walkability_status": "book_walkable",
        "modern_followability": "approximate_only",
        "gap_notes": [
            "本段包含补走前一日未完成路段；接送车路线不得计入步行路线。",
            "本段 GPX 只表达书中可支持的补走和随后步行部分。"
        ],
        "do_not_connect_in_gpx": False,
    },
    "seg-010": {
        "movement_type": "mixed",
        "continuity_status": "gap_after",
        "walkability_status": "partially_walkable",
        "modern_followability": "needs_field_check",
        "gap_notes": [
            "第260页及复核备注显示近五花草甸后搭车离开，不能画成完整步行到沽源。",
            "书中存在乘车/断点信息，不应与前后段强行连成连续徒步轨迹。",
            "该段只导出 waypoint，不作为连续 GPX track。",
        ],
        "do_not_connect_in_gpx": True,
    },
    "seg-011": {
        "movement_type": "mixed",
        "continuity_status": "gap_before",
        "walkability_status": "partially_walkable",
        "modern_followability": "needs_field_check",
        "gap_notes": [
            "第265页及复核备注显示本段先乘出租车到梳妆楼和五花草甸，再补走五花草甸至沽源。",
            "书中存在乘车/补走信息，不应与前后段强行连成连续徒步轨迹。",
            "该段只导出 waypoint，不作为连续 GPX track。",
        ],
        "do_not_connect_in_gpx": True,
    },
    "seg-012": {
        "movement_type": "walked",
        "continuity_status": "continuous",
        "walkability_status": "book_walkable",
        "modern_followability": "approximate_only",
        "gap_notes": [],
        "do_not_connect_in_gpx": False,
    },
    "seg-013": {
        "movement_type": "mixed",
        "continuity_status": "gap_after",
        "walkability_status": "partially_walkable",
        "modern_followability": "needs_field_check",
        "gap_notes": [
            "第318页及复核备注显示黑城子到正蓝旗存在车辆接续，需避免画成步行路线。",
            "书中存在乘车/断点信息，不应与前后段强行连成连续徒步轨迹。",
            "该段只导出 waypoint，不作为连续 GPX track。",
        ],
        "do_not_connect_in_gpx": True,
    },
    "seg-014": {
        "movement_type": "mixed",
        "continuity_status": "isolated",
        "walkability_status": "partially_walkable",
        "modern_followability": "needs_field_check",
        "gap_notes": [
            "第324页及复核备注显示本段先坐出租车到补走点，路线连续性需人工确认。",
            "书中存在乘车/补走信息，不应与前后段强行连成连续徒步轨迹。",
            "该段只导出 waypoint，不作为连续 GPX track。",
        ],
        "do_not_connect_in_gpx": True,
    },
    "seg-015": {
        "movement_type": "mixed",
        "continuity_status": "gap_before",
        "walkability_status": "partially_walkable",
        "modern_followability": "needs_field_check",
        "gap_notes": [
            "第344页及复核备注显示坐车过上都音高勒大桥后，从桥北开始最后一日步行。",
            "书中存在乘车/断点信息，不应与前后段强行连成连续徒步轨迹。",
            "该段只导出 waypoint，不作为连续 GPX track。",
        ],
        "do_not_connect_in_gpx": True,
    },
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def coordinate_note(segment: dict[str, Any]) -> str:
    points = [segment.get("start", {}), *segment.get("via", []), segment.get("end", {})]
    states = {point.get("coordinate_confidence", "missing") for point in points}
    if "missing" in states:
        return "存在缺坐标点，只能作为路线证据索引，不能生成完整地图线。"
    if "approximate" in states:
        return "包含 approximate 坐标，地图线只作为大致参考，仍需结合书中证据和实地路况核验。"
    return "坐标状态为 verified；仍以书中证据为路线依据。"


def merge_annotation(segment: dict[str, Any], annotation: dict[str, Any]) -> list[str]:
    changes: list[str] = []
    for field in CONTINUITY_FIELDS:
        old_value = segment.get(field, None)
        new_value = annotation[field]
        if field == "gap_notes":
            if not isinstance(old_value, list):
                segment[field] = list(new_value)
                changes.append(f"{field}: added")
            else:
                merged = list(old_value)
                for note in new_value:
                    if note not in merged:
                        merged.append(note)
                segment[field] = merged
                if merged != old_value:
                    changes.append(f"{field}: supplemented")
            continue
        if field == "do_not_connect_in_gpx":
            if not isinstance(old_value, bool):
                segment[field] = bool(new_value)
                changes.append(f"{field}: added")
            elif old_value != new_value:
                changes.append(f"{field}: preserved existing {old_value!r}, expected {new_value!r}")
            continue
        valid = VALID_VALUES[field]
        if old_value not in valid:
            segment[field] = new_value
            changes.append(f"{field}: added")
        elif old_value != new_value:
            changes.append(f"{field}: preserved existing {old_value!r}, expected {new_value!r}")
    return changes


def build_blocks(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for segment in segments:
        if segment.get("do_not_connect_in_gpx"):
            continue
        block_id = f"walk-block-{len(blocks) + 1:03d}"
        status = "partial" if segment.get("movement_type") != "walked" or segment.get("gap_notes") else "continuous"
        if segment.get("walkability_status") == "needs_review":
            status = "needs_review"
        blocks.append(
            {
                "block_id": block_id,
                "segment_ids": [segment["id"]],
                "start_name": segment.get("start", {}).get("name", ""),
                "end_name": segment.get("end", {}).get("name", ""),
                "status": status,
                "notes": coordinate_note(segment),
            }
        )
    return blocks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments", type=Path, required=True)
    parser.add_argument("--gpx-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--blocks", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    segments = load_json(args.segments)
    if not isinstance(segments, list):
        raise SystemExit("segments JSON must be a list")

    gpx_report_text = args.gpx_report.read_text(encoding="utf-8") if args.gpx_report.exists() else ""
    expected_skipped = {sid for sid, note in ANNOTATIONS.items() if note["do_not_connect_in_gpx"]}
    report_lines = [
        "# 路线连续性标注报告",
        "",
        f"- Generated at: {datetime.now().isoformat(timespec='seconds')}",
        f"- Input: `{args.segments}`",
        f"- GPX report: `{args.gpx_report}`",
        "- 说明: 本次只补充复走、断点和 GPX 连接规则字段，不改路线顺序、坐标、book_refs 或 chapter_refs。",
        "",
        "## 字段检查",
        "",
    ]

    missing_by_segment: dict[str, list[str]] = {}
    changes_by_segment: dict[str, list[str]] = {}
    for segment in segments:
        sid = segment.get("id")
        missing_fields = [field for field in CONTINUITY_FIELDS if field not in segment]
        missing_by_segment[sid] = missing_fields
        annotation = ANNOTATIONS.get(sid)
        if not annotation:
            raise SystemExit(f"missing continuity annotation for {sid}")
        changes_by_segment[sid] = merge_annotation(segment, annotation)

    blocks = build_blocks(segments)
    write_json(args.output, segments)
    write_json(args.blocks, blocks)

    movement_counts = Counter(segment.get("movement_type") for segment in segments)
    continuity_counts = Counter(segment.get("continuity_status") for segment in segments)
    walkability_counts = Counter(segment.get("walkability_status") for segment in segments)
    followability_counts = Counter(segment.get("modern_followability") for segment in segments)
    do_not_connect = [segment["id"] for segment in segments if segment.get("do_not_connect_in_gpx")]

    for sid, fields in missing_by_segment.items():
        report_lines.append(f"- {sid}: {'缺失 ' + ', '.join(fields) if fields else '字段已存在'}")
    report_lines.extend(["", "## 标注统计", ""])
    for title, counts, values in [
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
        report_lines.append(f"### {title}")
        report_lines.append("")
        for value in values:
            report_lines.append(f"- {value}: {counts.get(value, 0)}")
        report_lines.append("")

    report_lines.extend(
        [
            "## GPX 连接规则",
            "",
            f"- do_not_connect_in_gpx=true: {', '.join(do_not_connect) if do_not_connect else '无'}",
            f"- walkable blocks: {len(blocks)}",
            f"- 与当前 GPX 连续 track 数量对齐: {'yes' if len(blocks) == 8 else 'no'}",
            "",
            "## 与现有 GPX 报告交叉检查",
            "",
        ]
    )
    for sid in sorted(expected_skipped):
        found = sid in gpx_report_text
        report_lines.append(f"- {sid}: {'已出现在 GPX 断点报告中' if found else '未在 GPX 报告文本中找到，需复核'}")
    report_lines.extend(["", "## 分段修改", ""])
    for segment in segments:
        sid = segment["id"]
        report_lines.append(f"### {sid} {segment.get('title')}")
        report_lines.append("")
        report_lines.append(f"- changes: {'; '.join(changes_by_segment[sid]) if changes_by_segment[sid] else 'no value changes'}")
        report_lines.append(f"- movement_type: {segment.get('movement_type')}")
        report_lines.append(f"- continuity_status: {segment.get('continuity_status')}")
        report_lines.append(f"- walkability_status: {segment.get('walkability_status')}")
        report_lines.append(f"- modern_followability: {segment.get('modern_followability')}")
        report_lines.append(f"- do_not_connect_in_gpx: {segment.get('do_not_connect_in_gpx')}")
        notes = segment.get("gap_notes") or []
        report_lines.append("- gap_notes:")
        for note in notes:
            report_lines.append(f"  - {note}")
        if not notes:
            report_lines.append("  - 无")
        report_lines.append("")

    args.report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")
    print(f"Wrote {args.blocks}")
    print(f"Wrote {args.report}")
    print(f"do_not_connect={len(do_not_connect)} walkable_blocks={len(blocks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
