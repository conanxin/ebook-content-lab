from __future__ import annotations

import argparse
import csv
import html
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import fitz


FOCUS_PAGES = {30, 54, 76, 100, 122, 148, 172, 192, 216, 240, 262, 280, 302, 322, 342}
ROUTE_FIELDS = [
    "route_summary",
    "walking_directions",
    "terrain",
    "roads_or_paths",
    "water_sources",
    "resupply",
    "lodging",
    "risks_or_notes",
]
STATUS_FIELDS = [
    "movement_type",
    "continuity_status",
    "walkability_status",
    "modern_followability",
    "do_not_connect_in_gpx",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_pages(path: Path) -> dict[int, dict[str, Any]]:
    pages: dict[int, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            pages[int(row["page"])] = row
    return pages


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "；".join(str(item) for item in value if item is not None)
    return str(value)


def compact(value: str, limit: int = 180) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def page_numbers_from_text(value: str) -> set[int]:
    pages: set[int] = set()
    for match in re.finditer(r"(?:第\s*)?(\d{1,3})\s*页|p(\d{1,3})", value, flags=re.IGNORECASE):
        num = match.group(1) or match.group(2)
        if num:
            pages.add(int(num))
    return pages


def all_segment_pages(segment: dict[str, Any]) -> set[int]:
    pages: set[int] = set()
    for ref_group in ["book_refs", "chapter_refs"]:
        for ref in segment.get(ref_group) or []:
            if ref.get("page") is not None:
                pages.add(int(ref["page"]))
    for field in ["review_notes", "evidence_notes", "gap_notes"]:
        pages.update(page_numbers_from_text(clean_text(segment.get(field))))
    return pages


def point_label(point: dict[str, Any], role: str) -> str:
    name = point.get("name", "")
    conf = point.get("coordinate_confidence", "")
    return f"{role}: {name} ({conf})"


def segment_places(segment: dict[str, Any]) -> list[str]:
    places = [point_label(segment.get("start", {}), "起点")]
    places.extend(point_label(point, f"途经{i}") for i, point in enumerate(segment.get("via", []), start=1))
    places.append(point_label(segment.get("end", {}), "终点"))
    return places


def snippet_for(page_text: str, quote: str | None = None, limit: int = 420) -> str:
    text = re.sub(r"\s+", " ", page_text or "").strip()
    if not text:
        return ""
    if quote:
        q = re.sub(r"\s+", " ", quote).strip()
        idx = text.find(q)
        if idx >= 0:
            start = max(0, idx - 120)
            end = min(len(text), idx + len(q) + 180)
            return text[start:end]
    return text[:limit]


def page_image_name(page: int) -> str:
    return f"page_{page:03d}.png"


def render_pages(pdf_path: Path, pages: set[int], out_dir: Path) -> list[int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[int] = []
    doc = fitz.open(pdf_path)
    try:
        for page_no in sorted(pages):
            if page_no < 1 or page_no > doc.page_count:
                continue
            page = doc.load_page(page_no - 1)
            pix = page.get_pixmap(matrix=fitz.Matrix(1.7, 1.7), alpha=False)
            pix.save(out_dir / page_image_name(page_no))
            rendered.append(page_no)
    finally:
        doc.close()
    return rendered


def load_blocks(data_dir: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    path = data_dir / "route_walkable_blocks.json"
    if not path.exists():
        return {}, []
    blocks = load_json(path)
    by_segment: dict[str, dict[str, Any]] = {}
    for block in blocks:
        for sid in block.get("segment_ids", []):
            by_segment[sid] = block
    return by_segment, blocks


def status_class(value: Any) -> str:
    if value in {"mixed", "vehicle", "unclear", "gap_before", "gap_after", "isolated", "needs_field_check"}:
        return " flag"
    if value is True:
        return " flag"
    return ""


def field_class(value: Any) -> str:
    text = clean_text(value)
    if "书中未明示" in text:
        return " flag"
    return ""


def make_badge(label: str, value: Any) -> str:
    cls = status_class(value)
    text = html.escape(str(value))
    return f'<span class="badge{cls}"><b>{html.escape(label)}</b>{text}</span>'


def html_list(items: list[str], empty: str = "无") -> str:
    if not items:
        return f"<p class=\"muted\">{empty}</p>"
    return "<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in items) + "</ul>"


def html_field(label: str, value: Any) -> str:
    text = clean_text(value)
    if not text:
        text = "无"
    cls = field_class(text)
    return f'<div class="field{cls}"><dt>{html.escape(label)}</dt><dd>{html.escape(text)}</dd></div>'


def build_page_map(segments: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    page_map: dict[int, dict[str, Any]] = defaultdict(lambda: {"segments": set(), "fields": set(), "places": set(), "questions": []})
    for page in FOCUS_PAGES:
        item = page_map[page]
        item["fields"].add("重点复核页")
        item["questions"].append("核对地名 OCR、章节标题、方向词、是否只是章节出处。")
    for segment in segments:
        sid = segment["id"]
        places = segment_places(segment)
        for ref in segment.get("book_refs") or []:
            page = int(ref["page"])
            item = page_map[page]
            item["segments"].add(sid)
            item["fields"].add("book_refs")
            item["places"].update(places)
            item["questions"].append("核对短摘是否来自该页，并且是否支撑路线事实。")
        for ref in segment.get("chapter_refs") or []:
            page = int(ref["page"])
            item = page_map[page]
            item["segments"].add(sid)
            item["fields"].add("chapter_refs")
            item["places"].update(places)
            item["questions"].append("核对该页是否只是章节/段落标题出处，不要当作路线事实。")
        for field in ["review_notes", "evidence_notes", "gap_notes"]:
            for page in page_numbers_from_text(clean_text(segment.get(field))):
                item = page_map[page]
                item["segments"].add(sid)
                item["fields"].add(field)
                item["places"].update(places)
                item["questions"].append(f"核对 {field} 中提到的 OCR、地名、断点或证据问题。")
    return page_map


def add_checklist_row(
    rows: list[dict[str, Any]],
    segment_id: str,
    page: int | str,
    field: str,
    issue: str,
    current_value: Any,
    question: str,
    notes: str = "",
) -> None:
    rows.append(
        {
            "segment_id": segment_id,
            "page": page,
            "field": field,
            "issue": issue,
            "current_value": compact(clean_text(current_value), 260),
            "question": question,
            "manual_result": "",
            "notes": notes,
        }
    )


def build_checklist(segments: list[dict[str, Any]], blocks_by_segment: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for segment in segments:
        sid = segment["id"]
        for ref in segment.get("book_refs") or []:
            add_checklist_row(
                rows,
                sid,
                ref.get("page", ""),
                "book_refs",
                "书中路线证据核对",
                ref.get("quote", ""),
                "短摘是否确在该页，且是否支持本段起终点、途经地、方向、道路/水源/补给/住宿/风险等路线事实？",
                ref.get("note", ""),
            )
        for ref in segment.get("chapter_refs") or []:
            add_checklist_row(
                rows,
                sid,
                ref.get("page", ""),
                "chapter_refs",
                "章节出处核对",
                ref.get("quote", ""),
                "该引用是否只是章节/段落标题出处，而非路线事实证据？",
                ref.get("note", ""),
            )
        for field in ROUTE_FIELDS:
            value = segment.get(field)
            if "书中未明示" in clean_text(value):
                add_checklist_row(rows, sid, "", field, "书中未明示", value, "该字段是否确实无书中明示依据？")
        if segment.get("evidence_status") != "pass":
            add_checklist_row(
                rows,
                sid,
                "",
                "evidence_status",
                "evidence_status 非 pass",
                segment.get("evidence_status"),
                "该段证据清理后的 warning 状态是否符合你的人工判断？",
            )
        for note in segment.get("evidence_notes") or []:
            add_checklist_row(rows, sid, "", "evidence_notes", "证据处理说明核对", note, "该证据处理说明是否需要调整？")
        for note in segment.get("review_notes") or []:
            pages = sorted(page_numbers_from_text(note)) or [""]
            for page in pages:
                add_checklist_row(rows, sid, page, "review_notes", "复核备注", note, "该复核备注是否仍成立？是否需要回看原书扫描页？")
        for note in segment.get("gap_notes") or []:
            pages = sorted(page_numbers_from_text(note)) or [""]
            for page in pages:
                add_checklist_row(rows, sid, page, "gap_notes", "断点/GPX 规则", note, "是否确认存在乘车、补走、断点或不应强连 GPX？")
        for field in STATUS_FIELDS:
            value = segment.get(field)
            if value in {"mixed", "vehicle", "unclear", "needs_field_check", "gap_before", "gap_after", "isolated"} or value is True:
                add_checklist_row(
                    rows,
                    sid,
                    "",
                    field,
                    "状态高亮复核",
                    value,
                    "该状态是否与书中证据、复核备注和 GPX 导出规则一致？",
                    f"walkable_block={blocks_by_segment.get(sid, {}).get('block_id', '')}",
                )
        for role, point in [("start", segment.get("start", {})), *[(f"via[{i}]", p) for i, p in enumerate(segment.get("via", []), start=1)], ("end", segment.get("end", {}))]:
            if point.get("coordinate_confidence") == "approximate":
                add_checklist_row(
                    rows,
                    sid,
                    "",
                    role,
                    "approximate 坐标",
                    f"{point.get('name')} ({point.get('lat')}, {point.get('lng')}) source={point.get('coordinate_source')}",
                    "该地名和 approximate 坐标是否需要人工核对？",
                )
    return rows


def render_segment_html(segment: dict[str, Any], pages: dict[int, dict[str, Any]], rendered_pages: set[int], blocks_by_segment: dict[str, dict[str, Any]], focus_pages: set[int]) -> str:
    sid = segment["id"]
    block = blocks_by_segment.get(sid)
    enters_track = bool(block) and not segment.get("do_not_connect_in_gpx")
    waypoint_only = bool(segment.get("do_not_connect_in_gpx"))
    start_end = f"{segment.get('start', {}).get('name', '')} → {segment.get('end', {}).get('name', '')}"
    via_names = [point.get("name", "") for point in segment.get("via", [])]
    page_set = sorted(all_segment_pages(segment) | {int(ref["page"]) for ref in segment.get("book_refs", []) if ref.get("page")} | {int(ref["page"]) for ref in segment.get("chapter_refs", []) if ref.get("page")})
    status_badges = [
        make_badge("movement", segment.get("movement_type")),
        make_badge("continuity", segment.get("continuity_status")),
        make_badge("walkability", segment.get("walkability_status")),
        make_badge("followability", segment.get("modern_followability")),
        make_badge("do_not_connect", segment.get("do_not_connect_in_gpx")),
        make_badge("GPX track", "yes" if enters_track else "no"),
        make_badge("waypoint only", "yes" if waypoint_only else "no"),
    ]
    if segment.get("evidence_status") != "pass":
        status_badges.append(make_badge("evidence_status", segment.get("evidence_status")))

    point_cards = []
    for role, point in [("起点", segment.get("start", {})), *[(f"途经 {i}", p) for i, p in enumerate(segment.get("via", []), start=1)], ("终点", segment.get("end", {}))]:
        cls = " point approximate" if point.get("coordinate_confidence") == "approximate" else " point"
        point_cards.append(
            f'<li class="{cls.strip()}"><b>{html.escape(role)}</b> {html.escape(point.get("name", ""))}'
            f'<small>{html.escape(str(point.get("coordinate_confidence", "")))} / {html.escape(str(point.get("coordinate_source", "")))}</small></li>'
        )

    book_refs = []
    for ref in segment.get("book_refs") or []:
        page = int(ref["page"])
        book_refs.append(
            f'<div class="ref route-ref"><b>第 {page} 页</b><q>{html.escape(ref.get("quote", ""))}</q><p>{html.escape(ref.get("note", ""))}</p></div>'
        )
    chapter_refs = []
    for ref in segment.get("chapter_refs") or []:
        page = int(ref["page"])
        cls = "ref chapter-ref focus" if page in focus_pages else "ref chapter-ref"
        chapter_refs.append(
            f'<div class="{cls}"><b>第 {page} 页</b><q>{html.escape(ref.get("quote", ""))}</q><p>{html.escape(ref.get("note", ""))}</p></div>'
        )

    ocr_blocks = []
    for page in page_set:
        page_row = pages.get(page, {})
        text = page_row.get("text", "")
        refs = [ref for ref in (segment.get("book_refs") or []) + (segment.get("chapter_refs") or []) if int(ref.get("page", -1)) == page]
        quote = refs[0].get("quote") if refs else None
        cls = "ocr-page focus" if page in focus_pages or page_row.get("needs_review") else "ocr-page"
        image_html = ""
        if page in rendered_pages:
            image_html = f'<a href="pages/{page_image_name(page)}"><img src="pages/{page_image_name(page)}" alt="第 {page} 页扫描图"></a>'
        ocr_blocks.append(
            f'<article class="{cls}"><h4>第 {page} 页 OCR 文本片段'
            f'{" · 重点复核页" if page in focus_pages else ""}'
            f'{" · OCR needs_review" if page_row.get("needs_review") else ""}</h4>'
            f'<p>{html.escape(snippet_for(text, quote))}</p>{image_html}</article>'
        )

    return f"""
    <section class="segment" id="{html.escape(sid)}">
      <header>
        <h2>{html.escape(sid)} · {html.escape(segment.get("title", ""))}</h2>
        <p class="start-end">{html.escape(start_end)}</p>
        <div class="badges">{''.join(status_badges)}</div>
      </header>
      <div class="layout">
        <div>
          <h3>路线字段</h3>
          <dl class="fields">
            {html_field("途经地", "；".join(via_names) if via_names else "无")}
            {html_field("route_summary", segment.get("route_summary"))}
            {html_field("walking_directions", segment.get("walking_directions"))}
            {html_field("terrain", segment.get("terrain"))}
            {html_field("roads_or_paths", segment.get("roads_or_paths"))}
            {html_field("water_sources", segment.get("water_sources"))}
            {html_field("resupply", segment.get("resupply"))}
            {html_field("lodging", segment.get("lodging"))}
            {html_field("risks_or_notes", segment.get("risks_or_notes"))}
          </dl>
          <h3>坐标与地名</h3>
          <ul class="points">{''.join(point_cards)}</ul>
          <h3>断点 / GPX 规则</h3>
          {html_list(segment.get("gap_notes") or [])}
          <h3>confidence / evidence</h3>
          <dl class="fields">
            {html_field("confidence", segment.get("confidence"))}
            {html_field("evidence_status", segment.get("evidence_status"))}
            {html_field("evidence_notes", segment.get("evidence_notes"))}
          </dl>
          <h3>review_notes</h3>
          {html_list(segment.get("review_notes") or [])}
        </div>
        <div>
          <h3>书中路线证据</h3>
          {''.join(book_refs) if book_refs else '<p class="muted">无</p>'}
          <h3>章节出处 <span class="muted">不要当路线证据</span></h3>
          {''.join(chapter_refs) if chapter_refs else '<p class="muted">无</p>'}
        </div>
      </div>
      <h3>OCR 文本片段与原书扫描页</h3>
      <div class="ocr-grid">{''.join(ocr_blocks)}</div>
    </section>
    """


def build_html(out_dir: Path, segments: list[dict[str, Any]], pages: dict[int, dict[str, Any]], rendered_pages: set[int], blocks_by_segment: dict[str, dict[str, Any]]) -> None:
    focus_pages = FOCUS_PAGES
    nav = "".join(f'<a href="#{html.escape(seg["id"])}">{html.escape(seg["id"])}</a>' for seg in segments)
    segment_html = "\n".join(render_segment_html(seg, pages, rendered_pages, blocks_by_segment, focus_pages) for seg in segments)
    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>《从大都到上都》路线人工复核包</title>
  <style>
    :root {{ color-scheme: light; --ink:#202124; --muted:#68707a; --line:#d8dee8; --soft:#f6f8fb; --flag:#fff0d6; --bad:#ffe2df; --blue:#e8f1ff; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans SC","Microsoft YaHei",sans-serif; color:var(--ink); background:#fff; }}
    header.top {{ position:sticky; top:0; z-index:5; background:#ffffffee; backdrop-filter:blur(8px); border-bottom:1px solid var(--line); padding:14px 22px; }}
    h1 {{ margin:0 0 8px; font-size:22px; }}
    h2 {{ margin:0; font-size:20px; }}
    h3 {{ margin:18px 0 8px; font-size:15px; }}
    h4 {{ margin:0 0 8px; font-size:14px; }}
    nav {{ display:flex; gap:8px; flex-wrap:wrap; }}
    nav a {{ color:#245b7a; text-decoration:none; border:1px solid var(--line); padding:4px 8px; border-radius:6px; font-size:13px; }}
    main {{ padding:20px; max-width:1440px; margin:0 auto; }}
    .segment {{ border:1px solid var(--line); border-radius:8px; padding:18px; margin:0 0 22px; background:#fff; }}
    .start-end {{ margin:6px 0 10px; color:var(--muted); }}
    .badges {{ display:flex; flex-wrap:wrap; gap:8px; }}
    .badge {{ display:inline-flex; gap:6px; align-items:center; padding:4px 8px; border-radius:999px; border:1px solid var(--line); background:var(--soft); font-size:12px; }}
    .badge.flag, .flag {{ background:var(--flag); border-color:#e0a943; }}
    .layout {{ display:grid; grid-template-columns:minmax(0,1.2fr) minmax(320px,.8fr); gap:18px; align-items:start; }}
    .fields {{ display:grid; grid-template-columns:1fr; gap:8px; }}
    .field {{ border:1px solid var(--line); border-radius:6px; padding:8px 10px; background:#fff; }}
    .field dt {{ font-weight:700; font-size:12px; color:#3c4858; }}
    .field dd {{ margin:4px 0 0; line-height:1.55; }}
    .points {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:8px; padding:0; list-style:none; }}
    .point {{ border:1px solid var(--line); border-radius:6px; padding:8px; }}
    .point small {{ display:block; color:var(--muted); margin-top:4px; }}
    .approximate {{ background:var(--flag); }}
    .ref {{ border-left:4px solid #3b7891; background:var(--blue); padding:10px; margin:0 0 10px; }}
    .chapter-ref {{ border-left-color:#a06b15; background:var(--flag); }}
    .ref q {{ display:block; margin:6px 0; }}
    .ref p {{ margin:0; color:#374151; }}
    .ocr-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:12px; }}
    .ocr-page {{ border:1px solid var(--line); border-radius:8px; padding:10px; background:#fff; }}
    .ocr-page.focus {{ background:var(--flag); border-color:#e0a943; }}
    .ocr-page p {{ line-height:1.55; max-height:220px; overflow:auto; white-space:pre-wrap; }}
    .ocr-page img {{ width:100%; height:auto; display:block; border:1px solid var(--line); border-radius:4px; margin-top:8px; }}
    .muted {{ color:var(--muted); font-weight:400; }}
    @media (max-width:900px) {{ .layout {{ grid-template-columns:1fr; }} main {{ padding:12px; }} header.top {{ position:static; }} }}
  </style>
</head>
<body>
  <header class="top">
    <h1>《从大都到上都》路线人工复核包</h1>
    <p class="muted">生成时间：{html.escape(datetime.now().isoformat(timespec="seconds"))}。重点复核页：{", ".join(str(p) for p in sorted(FOCUS_PAGES))}。</p>
    <nav>{nav}</nav>
  </header>
  <main>
    {segment_html}
  </main>
</body>
</html>
"""
    (out_dir / "index.html").write_text(html_text, encoding="utf-8")


def build_review_index(out_dir: Path, page_map: dict[int, dict[str, Any]], rendered_pages: set[int]) -> None:
    lines = [
        "# 人工复核索引",
        "",
        "本索引用于核对路线证据页的扫描图、OCR 文本和路线字段。重点复核页来自项目复核清单；另包含 book_refs、chapter_refs 与复核备注中出现的页码。",
        "",
        "## 页码索引",
        "",
    ]
    for page in sorted(page_map):
        item = page_map[page]
        segments = sorted(item["segments"]) or ["未绑定具体 segment"]
        fields = sorted(item["fields"])
        places = sorted(item["places"])
        questions = []
        for question in item["questions"]:
            if question not in questions:
                questions.append(question)
        lines.extend(
            [
                f"### 第 {page} 页{'（重点复核页）' if page in FOCUS_PAGES else ''}",
                "",
                f"- 图片: `pages/{page_image_name(page)}`" if page in rendered_pages else "- 图片: 未渲染（页码超出 PDF 或渲染失败）",
                f"- 涉及 segment: {', '.join(segments)}",
                f"- 涉及字段: {', '.join(fields)}",
                f"- 涉及地名: {', '.join(places) if places else '未绑定'}",
                "- 人工核对问题:",
            ]
        )
        for question in questions or ["核对该页 OCR 与路线数据是否一致。"]:
            lines.append(f"  - {question}")
        lines.append("")
    out_dir.joinpath("review_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--segments", type=Path, required=True)
    parser.add_argument("--pages", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    out_dir = args.out_dir
    pages_dir = out_dir / "pages"
    out_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)

    segments = load_json(args.segments)
    page_rows = load_pages(args.pages)
    data_dir = args.segments.parent
    blocks_by_segment, _blocks = load_blocks(data_dir)

    page_map = build_page_map(segments)
    render_page_set = set(page_map) | FOCUS_PAGES
    rendered_pages = set(render_pages(args.pdf, render_page_set, pages_dir))

    checklist_rows = build_checklist(segments, blocks_by_segment)
    checklist_path = out_dir / "manual_review_checklist.csv"
    with checklist_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["segment_id", "page", "field", "issue", "current_value", "question", "manual_result", "notes"],
        )
        writer.writeheader()
        writer.writerows(checklist_rows)

    build_review_index(out_dir, page_map, rendered_pages)
    build_html(out_dir, segments, page_rows, rendered_pages, blocks_by_segment)

    public_data = data_dir.parent / "web" / "public" / "data"
    if public_data.exists():
        public_data.mkdir(parents=True, exist_ok=True)
        public_data.joinpath("review_index.md").write_text((out_dir / "review_index.md").read_text(encoding="utf-8"), encoding="utf-8")

    scores: list[tuple[int, str, str]] = []
    for segment in segments:
        score = 0
        if segment.get("do_not_connect_in_gpx"):
            score += 3
        if segment.get("movement_type") in {"mixed", "vehicle", "unclear"}:
            score += 2
        if segment.get("modern_followability") == "needs_field_check":
            score += 2
        score += sum(1 for point in [segment.get("start", {}), *segment.get("via", []), segment.get("end", {})] if point.get("coordinate_confidence") == "approximate") // 4
        score += len(segment.get("review_notes") or []) // 3
        scores.append((score, segment["id"], segment.get("title", "")))
    top_segments = [f"{sid} {title}" for score, sid, title in sorted(scores, reverse=True) if score > 0][:8]

    summary = [
        "# 复核包生成摘要",
        "",
        f"- Generated at: {datetime.now().isoformat(timespec='seconds')}",
        f"- PDF: `{args.pdf}`",
        f"- Segments: `{args.segments}`",
        f"- Rendered page images: {len(rendered_pages)}",
        f"- Checklist rows: {len(checklist_rows)}",
        f"- Entry: `index.html`",
        f"- Most review-needed segments: {', '.join(top_segments) if top_segments else '无'}",
    ]
    out_dir.joinpath("README.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    print(f"Wrote {out_dir / 'index.html'}")
    print(f"Wrote {out_dir / 'review_index.md'}")
    print(f"Wrote {checklist_path}")
    print(f"Rendered page images: {len(rendered_pages)}")
    print(f"Checklist rows: {len(checklist_rows)}")
    print(f"Most review-needed segments: {', '.join(top_segments) if top_segments else 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
