# -*- coding: utf-8 -*-
"""Audit route segment claims against OCR book-page evidence.

This script is intentionally conservative. It only checks whether segment
claims can be supported by pages already cited in book_refs. It never uses
coordinates or outside map data to infer route facts.
"""

from __future__ import annotations

import argparse
import copy
import csv
import difflib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


AUDITED_FIELDS = [
    "route_summary",
    "walking_directions",
    "terrain",
    "roads_or_paths",
    "water_sources",
    "resupply",
    "lodging",
    "risks_or_notes",
]

STOP_VALUES = {
    "",
    "null",
    "none",
    "书中未明示",
    "未明示",
    "无",
    "不详",
}

CLAUSE_SPLIT_RE = re.compile(r"[。！？；;：:\n\r]+")
SOFT_SPLIT_RE = re.compile(r"[，,、（）()\[\]【】]+")
ROUTE_CODE_RE = re.compile(r"\b(?:G|S|X)\s*\d{2,4}\b|\b\d{3}\b", re.I)
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")

ANCHOR_KEYWORDS = [
    "健德门",
    "皂甲屯",
    "小月河",
    "清河",
    "南沙河",
    "南玉河",
    "北玉河",
    "甲屯路",
    "沙阳路",
    "旧县",
    "龙虎台",
    "南口",
    "居庸关",
    "关沟",
    "水关",
    "八达岭",
    "岔道城",
    "小泥河",
    "大泥河",
    "大榆树",
    "白河堡",
    "燕山天池",
    "车坊",
    "黑峪口",
    "盘云岭",
    "昌赤路",
    "骆驼山",
    "郑家窑",
    "镇虏楼",
    "长伸地",
    "巡检司",
    "红沙梁",
    "龙门所",
    "G112",
    "京环线",
    "塘子庙",
    "东万口",
    "白草镇",
    "黑河",
    "X404",
    "三道川",
    "黑龙山",
    "山神庙",
    "老掌沟",
    "小厂镇",
    "沙岭",
    "前坝",
    "五花草甸",
    "葫芦河",
    "石头城",
    "牛群头",
    "沽源",
    "梳妆楼",
    "闪电河",
    "河东村",
    "青年湖",
    "察罕脑儿",
    "小宏城子",
    "水泉淖尔",
    "转佛庙",
    "马神庙",
    "塞北管理区",
    "方元酒店",
    "402",
    "滦河",
    "内蒙古",
    "明安驿",
    "李陵台",
    "黑城子",
    "X502",
    "正蓝旗",
    "四郎城",
    "上都镇",
    "圣元街",
    "四郎城路",
    "上都音高勒",
    "明德门",
    "元上都",
    "上都遗址",
    "县道",
    "国道",
    "公路",
    "土路",
    "水泥路",
    "大堤",
    "桥",
    "河",
    "河谷",
    "水库",
    "村",
    "镇",
    "城",
    "关",
    "岭",
    "山",
    "草甸",
    "草原",
    "沙丘",
    "铁丝网",
    "住宿",
    "宾馆",
    "旅馆",
    "餐馆",
    "小店",
    "买水",
    "水泡",
    "暑热",
    "酷热",
    "搭车",
    "坐车",
    "出租车",
]


@dataclass
class CitationCheck:
    segment_id: str
    page: Any
    quote: str
    note: str
    status: str
    best_score: float
    reason: str


@dataclass
class UnsupportedClaim:
    segment_id: str
    field: str
    claim: str
    reason: str
    pages: str
    suggestion: str


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[`~!@#$%^&*_+=|\\/<>{}\[\]（）()【】《》“”\"'‘’：:；;，,。.!！?？、-]", "", text)
    return text


def display_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(str(item) for item in value if item is not None)
    return str(value)


def compact_one_line(value: Any, limit: int = 120) -> str:
    text = re.sub(r"\s+", " ", display_text(value)).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_pages(path: Path) -> dict[int, dict[str, Any]]:
    pages: dict[int, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            try:
                page = int(row["page"])
            except (KeyError, TypeError, ValueError):
                continue
            pages[page] = row
    return pages


def best_substring_ratio(needle: str, haystack: str) -> tuple[float, str]:
    if not needle or not haystack:
        return 0.0, ""
    if needle in haystack:
        return 1.0, needle

    n = len(needle)
    if n <= 3:
        ratio = difflib.SequenceMatcher(None, needle, haystack).ratio()
        return ratio, haystack[:n]

    min_len = max(1, int(n * 0.75))
    max_len = max(min_len, int(n * 1.35))
    step = max(1, n // 5)
    best_ratio = 0.0
    best_window = ""

    lengths = sorted({n, min_len, max_len, int(n * 0.9), int(n * 1.1)})
    for length in lengths:
        if length <= 0:
            continue
        if length >= len(haystack):
            window = haystack
            ratio = difflib.SequenceMatcher(None, needle, window).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_window = window
            continue
        for start in range(0, len(haystack) - length + 1, step):
            window = haystack[start : start + length]
            ratio = difflib.SequenceMatcher(None, needle, window).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_window = window

    return best_ratio, best_window


def check_quote(segment_id: str, ref: dict[str, Any], pages: dict[int, dict[str, Any]]) -> CitationCheck:
    page = ref.get("page")
    quote = str(ref.get("quote", "") or "").strip()
    note = str(ref.get("note", "") or "").strip()

    missing_parts = []
    if page in (None, ""):
        missing_parts.append("page")
    if not quote:
        missing_parts.append("quote")
    if not note:
        missing_parts.append("note")
    if missing_parts:
        return CitationCheck(segment_id, page, quote, note, "missing_ref_field", 0.0, "缺少字段: " + ", ".join(missing_parts))

    try:
        page_int = int(page)
    except (TypeError, ValueError):
        return CitationCheck(segment_id, page, quote, note, "invalid_page", 0.0, "页码不是整数")

    page_row = pages.get(page_int)
    if not page_row:
        return CitationCheck(segment_id, page, quote, note, "missing_page", 0.0, "OCR 页文本不存在")

    qn = normalize_text(quote)
    pn = normalize_text(page_row.get("text", ""))
    if not qn:
        return CitationCheck(segment_id, page, quote, note, "empty_quote", 0.0, "引文为空")
    if qn in pn:
        return CitationCheck(segment_id, page, quote, note, "found", 1.0, "引文可在对应 OCR 页找到")

    ratio, _ = best_substring_ratio(qn, pn)
    threshold = 0.78 if len(qn) < 30 else 0.72
    if ratio >= threshold:
        return CitationCheck(segment_id, page, quote, note, "approximate", ratio, "引文与对应页 OCR 近似匹配")
    return CitationCheck(segment_id, page, quote, note, "citation_mismatch", ratio, "引文在对应页 OCR 中未找到")


def segment_pages(segment: dict[str, Any]) -> list[int]:
    pages: list[int] = []
    for ref in segment.get("book_refs") or []:
        try:
            pages.append(int(ref.get("page")))
        except (TypeError, ValueError):
            continue
    return sorted(set(pages))


def evidence_for_segment(segment: dict[str, Any], pages: dict[int, dict[str, Any]]) -> str:
    pieces: list[str] = []
    for ref in segment.get("book_refs") or []:
        page = ref.get("page")
        try:
            page_int = int(page)
        except (TypeError, ValueError):
            continue
        row = pages.get(page_int)
        if row:
            pieces.append(str(row.get("text", "") or ""))
        pieces.append(str(ref.get("quote", "") or ""))
        pieces.append(str(ref.get("note", "") or ""))
    return "\n".join(pieces)


def named_places(segment: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for key in ["start", "end"]:
        item = segment.get(key) or {}
        name = item.get("name")
        if name:
            names.append(str(name))
    for item in segment.get("via") or []:
        name = (item or {}).get("name")
        if name:
            names.append(str(name))
    return sorted(set(names), key=len, reverse=True)


def split_claims(value: Any) -> list[str]:
    text = display_text(value).strip()
    if not text:
        return []
    if normalize_text(text) in STOP_VALUES:
        return []

    rough: list[str] = []
    for part in CLAUSE_SPLIT_RE.split(text):
        part = part.strip()
        if not part:
            continue
        if len(part) <= 42:
            rough.append(part)
            continue
        subparts = [p.strip() for p in SOFT_SPLIT_RE.split(part) if p.strip()]
        rough.extend(subparts or [part])

    claims: list[str] = []
    for claim in rough:
        cleaned = claim.strip(" ，,。；;：:")
        if not cleaned:
            continue
        if normalize_text(cleaned) in STOP_VALUES:
            continue
        claims.append(cleaned)
    return claims


def extract_anchors(claim: str, places: list[str]) -> list[str]:
    anchors: list[str] = []
    claim_norm = normalize_text(claim)

    for name in places:
        if name and normalize_text(name) in claim_norm:
            anchors.append(name)

    for keyword in ANCHOR_KEYWORDS:
        if normalize_text(keyword) in claim_norm:
            anchors.append(keyword)

    for code in ROUTE_CODE_RE.findall(claim):
        anchors.append(code.upper().replace(" ", ""))
    for number in NUMBER_RE.findall(claim):
        if number not in {"1", "2", "3"}:
            anchors.append(number)

    deduped: list[str] = []
    seen = set()
    for anchor in anchors:
        key = normalize_text(anchor)
        if key and key not in seen:
            seen.add(key)
            deduped.append(anchor)
    return deduped


def claim_supported(claim: str, evidence_norm: str, places: list[str]) -> tuple[bool, str]:
    claim_norm = normalize_text(claim)
    if not claim_norm or claim_norm in STOP_VALUES:
        return True, "空值或书中未明示"
    if claim_norm in evidence_norm:
        return True, "claim 文本可在引用页全文中直接找到"

    anchors = extract_anchors(claim, places)
    if anchors:
        found = [anchor for anchor in anchors if normalize_text(anchor) in evidence_norm]
        # For route claims, concrete place/road/water/risk anchors should mostly
        # appear on cited pages. A single generic anchor is too weak for support.
        if len(anchors) == 1:
            if found and len(claim_norm) <= 12:
                return True, f"关键锚点可在引用页找到: {found[0]}"
            if found and best_substring_ratio(claim_norm, evidence_norm)[0] >= 0.42:
                return True, f"关键锚点和近似文本支持: {found[0]}"
            return False, "关键锚点未形成足够页内证据: " + "、".join(anchors)
        if len(found) >= max(1, (len(anchors) + 1) // 2):
            return True, "多数关键锚点可在引用页找到: " + "、".join(found)
        return False, "关键锚点缺少页内证据: " + "、".join([a for a in anchors if normalize_text(a) not in evidence_norm])

    # Generic prose without anchors is only audited when it is long enough to
    # carry a distinct factual claim. Short generic labels are treated as low-risk.
    if len(claim_norm) <= 10:
        return True, "短通用描述，无明确可审计锚点"
    ratio, _ = best_substring_ratio(claim_norm, evidence_norm)
    if ratio >= 0.45:
        return True, f"与引用页全文近似匹配，score={ratio:.2f}"
    return False, f"该描述未在引用页形成足够文本支持，best_score={ratio:.2f}"


def audit_claims(segment: dict[str, Any], pages: dict[int, dict[str, Any]]) -> list[UnsupportedClaim]:
    segment_id = str(segment.get("id", ""))
    evidence_text = evidence_for_segment(segment, pages)
    evidence_norm = normalize_text(evidence_text)
    places = named_places(segment)
    pages_text = ",".join(str(p) for p in segment_pages(segment))

    unsupported: list[UnsupportedClaim] = []
    for field in AUDITED_FIELDS:
        value = segment.get(field)
        for claim in split_claims(value):
            supported, reason = claim_supported(claim, evidence_norm, places)
            if supported:
                continue
            unsupported.append(
                UnsupportedClaim(
                    segment_id=segment_id,
                    field=field,
                    claim=claim,
                    reason=reason,
                    pages=pages_text,
                    suggestion=f"补充能支持 `{field}` 中该说法的 book_ref，或把该字段改为书中未明示/needs_review。",
                )
            )
    return unsupported


def quote_too_long(quote: str, limit: int = 120) -> bool:
    return len(re.sub(r"\s+", "", quote or "")) > limit


def make_review_note(prefix: str, detail: str) -> str:
    return f"[evidence_audit] {prefix}: {detail}"


def append_unique_review_notes(segment: dict[str, Any], notes: Iterable[str]) -> None:
    existing = segment.get("review_notes")
    if not isinstance(existing, list):
        existing = [] if existing in (None, "") else [str(existing)]
    seen = set(str(item) for item in existing)
    for note in notes:
        if note and note not in seen:
            existing.append(note)
            seen.add(note)
    segment["review_notes"] = existing


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def status_for_segment(
    citation_checks: list[CitationCheck],
    unsupported: list[UnsupportedClaim],
    pdf_review_pages: list[int],
    missing_book_refs: bool,
    long_quotes: list[str],
) -> str:
    hard_citation_statuses = {"missing_ref_field", "invalid_page", "missing_page", "empty_quote", "citation_mismatch"}
    if missing_book_refs or long_quotes or any(check.status in hard_citation_statuses for check in citation_checks):
        return "fail"
    if unsupported or pdf_review_pages or any(check.status == "approximate" for check in citation_checks):
        return "warning"
    return "pass"


def render_markdown(
    segments: list[dict[str, Any]],
    status_by_segment: dict[str, str],
    citations_by_segment: dict[str, list[CitationCheck]],
    unsupported_by_segment: dict[str, list[UnsupportedClaim]],
    pdf_review_by_segment: dict[str, list[int]],
    long_quotes_by_segment: dict[str, list[str]],
) -> str:
    counts = {key: 0 for key in ["pass", "warning", "fail"]}
    for status in status_by_segment.values():
        counts[status] = counts.get(status, 0) + 1

    all_review_pages = sorted({page for pages in pdf_review_by_segment.values() for page in pages})
    unsupported_fields = sorted(
        {
            f"{claim.segment_id}:{claim.field}"
            for claims in unsupported_by_segment.values()
            for claim in claims
        }
    )

    lines: list[str] = [
        "# 路线证据审计报告",
        "",
        "本报告只检查路线段内字段是否能被该段 `book_refs` 指向的 OCR 页文本支持；不使用坐标或现代地图反推路线。",
        "",
        "## 总览",
        "",
        f"- pass: {counts.get('pass', 0)}",
        f"- warning: {counts.get('warning', 0)}",
        f"- fail: {counts.get('fail', 0)}",
        f"- 需要人工回看页码: {', '.join(map(str, all_review_pages)) if all_review_pages else '无'}",
        f"- 证据不足字段数: {len(unsupported_fields)}",
        "",
        "## 分段审计",
        "",
    ]

    for segment in segments:
        sid = str(segment.get("id", ""))
        status = status_by_segment.get(sid, "fail")
        start = (segment.get("start") or {}).get("name") or ""
        end = (segment.get("end") or {}).get("name") or ""
        title = segment.get("title") or ""
        citations = citations_by_segment.get(sid, [])
        unsupported = unsupported_by_segment.get(sid, [])
        pdf_pages = pdf_review_by_segment.get(sid, [])
        long_quotes = long_quotes_by_segment.get(sid, [])

        lines.extend(
            [
                f"### {sid} {title}",
                "",
                f"- 起点终点: {start} → {end}",
                f"- 证据状态: **{status}**",
            ]
        )

        if citations:
            cite_parts = []
            for check in citations:
                cite_parts.append(f"p{check.page}:{check.status}(score={check.best_score:.2f})")
            lines.append("- 引文页内匹配: " + "; ".join(cite_parts))
        else:
            lines.append("- 引文页内匹配: 无 book_refs")

        if unsupported:
            lines.append("- 证据不足字段: " + ", ".join(sorted({claim.field for claim in unsupported})))
            for claim in unsupported:
                lines.append(
                    f"  - `{claim.field}`: {compact_one_line(claim.claim, 90)}；{claim.reason}"
                )
        else:
            lines.append("- 证据不足字段: 无")

        if pdf_pages:
            lines.append("- 需要人工回看页码: " + ", ".join(map(str, pdf_pages)))
        else:
            lines.append("- 需要人工回看页码: 无")

        suggestions: list[str] = []
        mismatches = [check for check in citations if check.status == "citation_mismatch"]
        missing = [check for check in citations if check.status not in {"found", "approximate"} and check.status != "citation_mismatch"]
        if mismatches:
            suggestions.append("回看 PDF 校正 citation_mismatch 的 quote 或 page。")
        if missing:
            suggestions.append("补齐 book_ref 的 page/quote/note，或删除无法追溯的引用。")
        if long_quotes:
            suggestions.append("缩短超过 120 字的 quote。")
        if unsupported:
            suggestions.append("为证据不足字段补充对应页码短摘；无法补证时改为“书中未明示”或保留 needs_review。")
        if pdf_pages:
            suggestions.append("人工回看 OCR 疑似错误页，确认地名和断点。")
        if not suggestions:
            suggestions.append("当前字段可由 book_refs 指向页文本支撑。")
        lines.append("- 建议如何修改: " + " ".join(suggestions))

        if long_quotes:
            lines.append("- 过长 quote: " + "; ".join(compact_one_line(q, 80) for q in long_quotes))

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def audit(args: argparse.Namespace) -> dict[str, Any]:
    route_path = Path(args.route_segments)
    pages_path = Path(args.book_pages)
    output_path = Path(args.output)
    data_dir = output_path.parent

    segments = load_json(route_path)
    if not isinstance(segments, list):
        raise SystemExit("route_segments must be a JSON array")
    pages = load_pages(pages_path)

    audited_segments = copy.deepcopy(segments)

    citations_by_segment: dict[str, list[CitationCheck]] = {}
    unsupported_by_segment: dict[str, list[UnsupportedClaim]] = {}
    pdf_review_by_segment: dict[str, list[int]] = {}
    long_quotes_by_segment: dict[str, list[str]] = {}
    status_by_segment: dict[str, str] = {}

    for original, audited in zip(segments, audited_segments):
        sid = str(original.get("id", ""))
        refs = original.get("book_refs") or []
        missing_book_refs = not isinstance(refs, list) or len(refs) == 0

        checks = [check_quote(sid, ref, pages) for ref in refs] if isinstance(refs, list) else []
        citations_by_segment[sid] = checks

        long_quotes = [str(ref.get("quote", "") or "") for ref in refs if isinstance(ref, dict) and quote_too_long(str(ref.get("quote", "") or ""))]
        long_quotes_by_segment[sid] = long_quotes

        unsupported = audit_claims(original, pages) if not missing_book_refs else []
        unsupported_by_segment[sid] = unsupported

        review_pages: list[int] = []
        for page in segment_pages(original):
            row = pages.get(page)
            if row and row.get("needs_review"):
                review_pages.append(page)
        pdf_review_by_segment[sid] = sorted(set(review_pages))

        status = status_for_segment(checks, unsupported, review_pages, missing_book_refs, long_quotes)
        status_by_segment[sid] = status

        review_notes: list[str] = []
        if missing_book_refs:
            review_notes.append(make_review_note("missing_book_refs", "该段没有 book_refs，无法审计书中依据。"))
        for check in checks:
            if check.status == "citation_mismatch":
                review_notes.append(make_review_note("citation_mismatch", f"p{check.page} quote 未能在对应 OCR 页找到：{compact_one_line(check.quote, 80)}"))
            elif check.status not in {"found", "approximate"}:
                review_notes.append(make_review_note("citation_issue", f"p{check.page} {check.status}: {check.reason}"))
        for claim in unsupported:
            review_notes.append(make_review_note("unsupported_claim", f"{claim.field}: {compact_one_line(claim.claim, 90)}"))
        if review_pages:
            review_notes.append(make_review_note("needs_pdf_review", "引用页 OCR 标记需复核: " + ", ".join(map(str, review_pages))))
        if long_quotes:
            review_notes.append(make_review_note("quote_too_long", f"{len(long_quotes)} 条 quote 超过 120 字。"))

        if review_notes:
            append_unique_review_notes(audited, review_notes)
            audited["confidence"] = "needs_review"

        audited["evidence_audit"] = {
            "status": status,
            "citation_checks": [
                {
                    "page": check.page,
                    "quote": check.quote,
                    "status": check.status,
                    "best_score": round(check.best_score, 3),
                    "reason": check.reason,
                }
                for check in checks
            ],
            "unsupported_fields": sorted({claim.field for claim in unsupported}),
            "needs_pdf_review_pages": review_pages,
            "quote_too_long_count": len(long_quotes),
        }

    output_path.write_text(
        render_markdown(
            segments,
            status_by_segment,
            citations_by_segment,
            unsupported_by_segment,
            pdf_review_by_segment,
            long_quotes_by_segment,
        ),
        encoding="utf-8",
    )

    unsupported_csv = data_dir / "unsupported_claims.csv"
    mismatch_csv = data_dir / "citation_mismatches.csv"
    if route_path.name == "route_segments.json":
        audited_json = data_dir / "route_segments.evidence_audited.json"
    else:
        audited_json = data_dir / f"{route_path.stem}.audit_augmented.json"

    write_csv(
        unsupported_csv,
        ["segment_id", "field", "claim", "reason", "pages", "suggestion"],
        [
            {
                "segment_id": claim.segment_id,
                "field": claim.field,
                "claim": claim.claim,
                "reason": claim.reason,
                "pages": claim.pages,
                "suggestion": claim.suggestion,
            }
            for claims in unsupported_by_segment.values()
            for claim in claims
        ],
    )

    write_csv(
        mismatch_csv,
        ["segment_id", "page", "quote", "note", "match_status", "best_score", "reason"],
        [
            {
                "segment_id": check.segment_id,
                "page": check.page,
                "quote": check.quote,
                "note": check.note,
                "match_status": check.status,
                "best_score": f"{check.best_score:.3f}",
                "reason": check.reason,
            }
            for checks in citations_by_segment.values()
            for check in checks
            if check.status
            in {
                "missing_ref_field",
                "invalid_page",
                "missing_page",
                "empty_quote",
                "citation_mismatch",
            }
        ],
    )

    audited_json.write_text(
        json.dumps(audited_segments, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    counts = {key: 0 for key in ["pass", "warning", "fail"]}
    for status in status_by_segment.values():
        counts[status] = counts.get(status, 0) + 1
    return {
        "counts": counts,
        "review_pages": sorted({page for pages_list in pdf_review_by_segment.values() for page in pages_list}),
        "unsupported_fields": sorted(
            {
                f"{claim.segment_id}:{claim.field}"
                for claims in unsupported_by_segment.values()
                for claim in claims
            }
        ),
        "output": str(output_path),
        "unsupported_csv": str(unsupported_csv),
        "mismatch_csv": str(mismatch_csv),
        "audited_json": str(audited_json),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit route evidence against cited OCR pages.")
    parser.add_argument("route_segments", help="Path to data/route_segments.json")
    parser.add_argument("--book-pages", required=True, help="Path to data/book_pages.cleaned.jsonl")
    parser.add_argument("--output", required=True, help="Path to data/evidence_audit.md")
    return parser.parse_args()


def main() -> None:
    result = audit(parse_args())
    counts = result["counts"]
    print(f"evidence audit written: {result['output']}")
    print(f"pass={counts.get('pass', 0)} warning={counts.get('warning', 0)} fail={counts.get('fail', 0)}")
    print(f"needs_pdf_review_pages={','.join(map(str, result['review_pages'])) or 'none'}")
    print(f"unsupported_fields={len(result['unsupported_fields'])}")
    print(f"csv={result['unsupported_csv']}")
    print(f"mismatches={result['mismatch_csv']}")
    print(f"audited_json={result['audited_json']}")


if __name__ == "__main__":
    main()
