from __future__ import annotations

import json
import re
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def value_text(value: Any) -> str:
    if value is None or value == "" or value == []:
        return "书中未明示"
    if isinstance(value, list):
        if not value:
            return "书中未明示"
        return "\n".join(f"- {value_text(item)}" for item in value)
    return str(value)


def inline_list(items: Any) -> str:
    values = [str(item) for item in items if item]
    return "、".join(values) if values else "书中未明示"


def segment_label(segment: dict[str, Any]) -> str:
    return f"{segment['id']} {segment.get('title', '')}"


def segment_points(segment: dict[str, Any]) -> list[dict[str, Any]]:
    return [segment.get("start", {}), *segment.get("via", []), segment.get("end", {})]


def page_numbers_from_text(text: str) -> set[int]:
    pages: set[int] = set()
    for number in re.findall(r"第\s*(\d{1,3})\s*页", text):
        pages.add(int(number))
    for number in re.findall(r"\bp(\d{1,3})\b", text, flags=re.IGNORECASE):
        pages.add(int(number))
    if re.fullmatch(r"[\s\-、,，0-9]+", text.strip()):
        for number in re.findall(r"\d{1,3}", text):
            pages.add(int(number))
    return pages


def extract_section(markdown: str, heading: str) -> list[str]:
    lines = markdown.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == f"## {heading}":
            start = index + 1
            break
    if start is None:
        return []
    section: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        if line.strip():
            section.append(line)
    return section


def build_guide() -> tuple[Path, Path, dict[str, Any]]:
    segments = load_json(ROOT / "data" / "route_segments.json")
    blocks = load_json(ROOT / "data" / "route_walkable_blocks.json")
    review_notes = (ROOT / "data" / "review_notes.md").read_text(encoding="utf-8")

    block_by_segment: dict[str, dict[str, Any]] = {}
    for block in blocks:
        for segment_id in block.get("segment_ids", []):
            block_by_segment[segment_id] = block

    place_review_items = [
        line[2:].strip() for line in extract_section(review_notes, "地名歧义") if line.startswith("- ")
    ]
    manual_page_lines = [
        line for line in extract_section(review_notes, "需要人工回看 PDF 的页码") if line.startswith("- ")
    ]
    manual_pages = sorted(page_numbers_from_text("\n".join(manual_page_lines)))
    ocr_page_lines = [
        line[2:].strip() for line in extract_section(review_notes, "OCR 疑似错误") if line.startswith("- ")
    ]
    route_gap_lines = [
        line[2:].strip() for line in extract_section(review_notes, "路线断点") if line.startswith("- ")
    ]

    movement_counts = Counter(segment.get("movement_type") for segment in segments)
    continuity_counts = Counter(segment.get("continuity_status") for segment in segments)
    walkability_counts = Counter(segment.get("walkability_status") for segment in segments)
    followability_counts = Counter(segment.get("modern_followability") for segment in segments)
    do_not_connect = [segment for segment in segments if segment.get("do_not_connect_in_gpx")]
    waypoint_only = do_not_connect

    not_direct: list[tuple[dict[str, Any], list[str]]] = []
    for segment in segments:
        reasons: list[str] = []
        if segment.get("movement_type") in {"mixed", "vehicle", "unclear"}:
            reasons.append(f"movement_type={segment.get('movement_type')}")
        if segment.get("continuity_status") in {"gap_before", "gap_after", "isolated"}:
            reasons.append(f"continuity_status={segment.get('continuity_status')}")
        if segment.get("modern_followability") in {"not_enough_information", "needs_field_check"}:
            reasons.append(f"modern_followability={segment.get('modern_followability')}")
        if segment.get("do_not_connect_in_gpx"):
            reasons.append("do_not_connect_in_gpx=true / 只导出 waypoint")
        if reasons:
            not_direct.append((segment, reasons))

    approximate_points: list[tuple[str, str]] = []
    for segment in segments:
        for point in segment_points(segment):
            if point.get("coordinate_confidence") == "approximate":
                approximate_points.append((segment["id"], point.get("name", "")))

    lines: list[str] = []
    lines.append("# 《从大都到上都》徒步路线复走说明 v0.1")
    lines.append("")
    lines.append(
        f"> 生成时间：{datetime.now().isoformat(timespec='seconds')}。本文件由当前结构化路线数据生成，定位是“路线解读和复核说明”，不是户外导航手册。"
    )
    lines.append("")
    lines.append("## 1. 使用说明")
    lines.append("")
    lines.extend(
        [
            "- 本说明依据《从大都到上都》书中路线整理，路线事实以每段 `book_refs` 的页码和短摘为准。",
            "- 坐标为现代地图辅助定位，只用于帮助理解地名位置；`approximate` 坐标不能视为确定地点。",
            "- 章节出处 `chapter_refs` 和路线证据 `book_refs` 已分开记录；章节出处只说明段落/标题来源，不作为路线事实证据。",
            "- 有些段落存在乘车、补走、路线断点或现代路况不确定，已在 `movement_type`、`continuity_status`、`gap_notes` 和 `do_not_connect_in_gpx` 中标明。",
            "- 本说明不能当作未经核验的户外导航轨迹；实际出行前必须自行核验现代道路、封闭区域、天气、水源、住宿、补给和安全风险。",
        ]
    )
    lines.append("")
    lines.append("## 2. 路线总览")
    lines.append("")
    lines.extend(
        [
            f"- 总段数：{len(segments)}",
            f"- 书中明确徒步段数：{movement_counts.get('walked', 0)}",
            f"- mixed / vehicle / inferred / unclear 段数：mixed {movement_counts.get('mixed', 0)}，vehicle {movement_counts.get('vehicle', 0)}，inferred {movement_counts.get('inferred', 0)}，unclear {movement_counts.get('unclear', 0)}",
            f"- continuous / gap_before / gap_after / isolated 段数：continuous {continuity_counts.get('continuous', 0)}，gap_before {continuity_counts.get('gap_before', 0)}，gap_after {continuity_counts.get('gap_after', 0)}，isolated {continuity_counts.get('isolated', 0)}",
            f"- book_walkable / partially_walkable 段数：book_walkable {walkability_counts.get('book_walkable', 0)}，partially_walkable {walkability_counts.get('partially_walkable', 0)}",
            f"- approximate_only / needs_field_check 段数：approximate_only {followability_counts.get('approximate_only', 0)}，needs_field_check {followability_counts.get('needs_field_check', 0)}",
            f"- 连续徒步块数量：{len(blocks)}",
            f"- 不应连接 GPX 的段数：{len(do_not_connect)}（{inline_list(segment_label(segment) for segment in do_not_connect)}）",
            f"- 只导出 waypoint 的段数：{len(waypoint_only)}（{inline_list(segment_label(segment) for segment in waypoint_only)}）",
            f"- 坐标为 approximate 的地名点：{len(approximate_points)} 个；这些坐标均只作辅助定位。",
        ]
    )
    lines.append("")
    lines.append("### 需人工复核地名")
    lines.append("")
    lines.extend([f"- {item}" for item in place_review_items] or ["- 书中未明示"])
    lines.append("")
    lines.append("### 需人工复核页码")
    lines.append("")
    lines.append("- " + (", ".join(str(page) for page in manual_pages) if manual_pages else "书中未明示"))
    lines.append("")

    lines.append("## 3. 连续徒步块")
    lines.append("")
    lines.append(
        "连续徒步块与当前 GPX 的连续 track 对应。它们不包含 `do_not_connect_in_gpx=true` 的段落；即使一个块可导出为 track，也只表示当前数据可画成参考线，不表示已经完成现代户外路况核验。"
    )
    lines.append("")
    for block in blocks:
        segment_ids = block.get("segment_ids", [])
        block_segments = [next((segment for segment in segments if segment["id"] == sid), None) for sid in segment_ids]
        block_segments = [segment for segment in block_segments if segment]
        gap_notes: list[str] = []
        for segment in block_segments:
            gap_notes.extend(segment.get("gap_notes") or [])
        lines.append(f"### {block.get('block_id')}：{block.get('start_name')} → {block.get('end_name')}")
        lines.append("")
        lines.append(f"- 包含 segment：{', '.join(segment_ids)}")
        lines.append(f"- 状态：{block.get('status')}")
        lines.append(
            f"- 断点说明：{'; '.join(gap_notes) if gap_notes else '本块内部未标记 do_not_connect_in_gpx 断点；仍需注意 approximate 坐标和现代路况核验。'}"
        )
        lines.append("- 是否与 GPX track 对应：是")
        lines.append(f"- 备注：{block.get('notes') or '书中未明示'}")
        lines.append("")

    lines.append("## 4. 分段路线说明")
    lines.append("")
    for segment in segments:
        block = block_by_segment.get(segment["id"])
        waypoint = bool(segment.get("do_not_connect_in_gpx"))
        lines.append(f"### {segment['id']} {segment.get('title')}")
        lines.append("")
        lines.append(
            f"- 起点 → 终点：{segment.get('start', {}).get('name', '书中未明示')} → {segment.get('end', {}).get('name', '书中未明示')}"
        )
        lines.append(f"- 途经地：{inline_list(point.get('name') for point in segment.get('via', []))}")
        lines.append(f"- 书中路线概括：{value_text(segment.get('route_summary'))}")
        lines.append("- 步行方向：")
        directions = segment.get("walking_directions") or []
        lines.extend([f"  - {item}" for item in directions] or ["  - 书中未明示"])
        lines.append(f"- 地形：{value_text(segment.get('terrain'))}")
        lines.append(f"- 道路 / 路径：{value_text(segment.get('roads_or_paths'))}")
        lines.append(f"- 河流 / 水源：{value_text(segment.get('water_sources'))}")
        lines.append(f"- 补给：{value_text(segment.get('resupply'))}")
        lines.append(f"- 住宿：{value_text(segment.get('lodging'))}")
        lines.append(f"- 风险：{value_text(segment.get('risks_or_notes'))}")
        lines.append(f"- movement_type：{value_text(segment.get('movement_type'))}")
        lines.append(f"- continuity_status：{value_text(segment.get('continuity_status'))}")
        lines.append(f"- walkability_status：{value_text(segment.get('walkability_status'))}")
        lines.append(f"- modern_followability：{value_text(segment.get('modern_followability'))}")
        lines.append("- gap_notes：")
        gap_notes = segment.get("gap_notes") or []
        lines.extend([f"  - {item}" for item in gap_notes] or ["  - 书中未明示"])
        lines.append(f"- 是否不应连接 GPX：{'是' if segment.get('do_not_connect_in_gpx') else '否'}")
        lines.append(f"- 是否只导出 waypoint：{'是' if waypoint else '否'}")
        lines.append(f"- 是否属于连续徒步块：{block.get('block_id') if block else '否'}")
        lines.append("- 章节出处（chapter_refs，只作章节/标题出处，不作路线事实证据）：")
        chapter_refs = segment.get("chapter_refs") or []
        if chapter_refs:
            for ref in chapter_refs:
                lines.append(f"  - 第 {ref.get('page')} 页：{ref.get('quote')}（{ref.get('note')}）")
        else:
            lines.append("  - 书中未明示")
        lines.append("- 书中路线证据（book_refs）：")
        book_refs = segment.get("book_refs") or []
        if book_refs:
            for ref in book_refs:
                lines.append(f"  - 第 {ref.get('page')} 页：{ref.get('quote')}（{ref.get('note')}）")
        else:
            lines.append("  - 书中未明示")
        lines.append("- 复核事项：")
        review_items = (segment.get("review_notes") or []) + (segment.get("evidence_notes") or [])
        lines.extend([f"  - {item}" for item in review_items] or ["  - 书中未明示"])
        lines.append("")

    lines.append("## 5. 不适合直接复走的段落")
    lines.append("")
    lines.append(
        "以下段落不应被理解为“拿 GPX 就能直接走”的路线。列入原因可能包括 mixed、乘车/补走、断点、`needs_field_check`、或只导出 waypoint。"
    )
    lines.append("")
    for segment, reasons in not_direct:
        lines.append(f"- {segment_label(segment)}：{'; '.join(reasons)}")
    lines.append("")
    lines.append(
        "特别说明：`seg-009 老掌沟到小厂镇` 是 mixed，但没有设置 `do_not_connect_in_gpx=true`，因为当前 GPX 只表达书中可支持的补走和随后步行部分，不连接接送车路线；它仍需注意补走上下文。"
    )
    lines.append("")

    lines.append("## 6. 人工复核清单")
    lines.append("")
    lines.append("### 6.1 需要回看 PDF 的页码")
    lines.append("")
    lines.append("- " + (", ".join(str(page) for page in manual_pages) if manual_pages else "书中未明示"))
    lines.append("")
    lines.append("### 6.2 路线断点核对")
    lines.append("")
    lines.extend([f"- {item}" for item in route_gap_lines] or ["- 书中未明示"])
    lines.append("")
    lines.append("### 6.3 地名和 OCR 核对")
    lines.append("")
    lines.extend([f"- {item}" for item in place_review_items] or ["- 书中未明示"])
    if ocr_page_lines:
        lines.extend(f"- {item}" for item in ocr_page_lines)
    lines.append("")
    lines.append("### 6.4 字段核对问题")
    lines.append("")
    for segment in segments:
        issues: list[str] = []
        if segment.get("movement_type") in {"mixed", "vehicle", "unclear"}:
            issues.append("确认是否确有乘车、补走或非连续处理。")
        if segment.get("modern_followability") == "needs_field_check":
            issues.append("现代道路、封闭区域和实际可通行性需实地或地图复核。")
        if segment.get("do_not_connect_in_gpx"):
            issues.append("确认该段只导出 waypoint，不应自动连线。")
        if any(
            "书中未明示" in value_text(segment.get(field))
            for field in ["resupply", "lodging", "water_sources", "distance_km_book"]
        ):
            issues.append("补给、住宿、水源或里程中存在“书中未明示”，不要补写。")
        if issues:
            lines.append(f"- {segment_label(segment)}")
            lines.extend(f"  - {issue}" for issue in issues)
    lines.append("")

    lines.append("## 7. GPX 使用说明")
    lines.append("")
    lines.extend(
        [
            "- GPX 分成多个连续 track；当前导出报告显示 99 个 waypoint、8 个连续 track。",
            "- 断点 / 补走 / 乘车 / 不应连接的段落只导出 waypoint，不导出连续 track。",
            "- 不要把 waypoint 之间自动连线当成书中徒步轨迹；尤其不要把 `do_not_connect_in_gpx=true` 的段落强行连成连续路线。",
            "- GPX 中的坐标来自现代地图辅助定位，许多为 approximate，只能帮助理解书中地名的大致位置。",
            "- 使用任何户外 App 前，需要自行核验现代路况、通行权限、天气、水源、住宿、补给和安全风险。",
            "- 本说明可以帮助你按书中线索理解路线，但不能替代实地路书、官方道路信息或专业户外风险评估。",
        ]
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "数据来源文件：`data/route_segments.json`、`data/route_walkable_blocks.json`、`data/review_notes.md`、`data/gpx_export_report.md` 等当前项目产物。"
    )

    out_path = ROOT / "data" / "field_guide.md"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    public_path = ROOT / "web" / "public" / "data" / "field_guide.md"
    public_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out_path, public_path)

    stats = {
        "segments": len(segments),
        "walked": movement_counts.get("walked", 0),
        "mixed": movement_counts.get("mixed", 0),
        "vehicle": movement_counts.get("vehicle", 0),
        "inferred": movement_counts.get("inferred", 0),
        "unclear": movement_counts.get("unclear", 0),
        "do_not_connect": len(do_not_connect),
        "not_direct_ids": [segment["id"] for segment, _ in not_direct],
    }
    return out_path, public_path, stats


def main() -> int:
    out_path, public_path, stats = build_guide()
    print(f"Wrote {out_path}")
    print(f"Copied {public_path}")
    print(json.dumps(stats, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
