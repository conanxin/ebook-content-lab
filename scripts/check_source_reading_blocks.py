#!/usr/bin/env python3
"""Validate the v0.7-A20 source reading blocks."""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from scripts.lib.project_paths import from_project
except ModuleNotFoundError:
    from lib.project_paths import from_project


VERSION = "v0.7-A20"

PLACEHOLDER_MARKERS = [
    "用于定位本封信的场景和语气",
    "不作为全文替代",
    "结构证据",
    "structural_no_quote",
    "Structural reference only",
    "No source quote is published",
    "Derived from title",
    "Derived from letter order",
    "基于标题、地点线索、结构摘要",
]

FORBIDDEN_PUBLIC_MARKERS = [
    "private/",
    "private\\",
    "/mnt/",
    "D:/",
    "D:\\",
    "book.epub",
    "book.md",
    "book_sections",
    "book_chunks",
]


@dataclass(frozen=True)
class Finding:
    severity: str
    path: str
    message: str


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def add_error(findings: list[Finding], path: str | Path, message: str) -> None:
    findings.append(Finding("error", str(path), message))


def add_warning(findings: list[Finding], path: str | Path, message: str) -> None:
    findings.append(Finding("warning", str(path), message))


def json_blob(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def text_in_section(block_text: str, section_text: str) -> bool:
    if block_text and block_text in section_text:
        return True
    return bool(normalize_text(block_text) and normalize_text(block_text) in normalize_text(section_text))


def count_blank_manual_results(csv_path: Path) -> tuple[int, int]:
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return len(rows), sum(1 for row in rows if not (row.get("manual_result") or "").strip())


def csv_all_blank(path: Path, field: str) -> bool:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return all(not (row.get(field) or "").strip() for row in rows)


def validate(project: str, version: str) -> tuple[dict[str, Any], list[Finding]]:
    paths = from_project(project)
    findings: list[Finding] = []

    book = read_json(paths.book_overview_json)
    chapters_payload = read_json(paths.chapter_reading_cards_json)
    questions_payload = read_json(paths.reading_questions_json)
    web_book = read_json(paths.web_book_overview_json)
    web_chapters = read_json(paths.web_chapter_reading_cards_json)
    web_questions = read_json(paths.web_reading_questions_json)

    if book != web_book:
        add_error(findings, paths.web_book_overview_json, "web book_overview mirror differs")
    if chapters_payload != web_chapters:
        add_error(findings, paths.web_chapter_reading_cards_json, "web chapter_reading_cards mirror differs")
    if questions_payload != web_questions:
        add_error(findings, paths.web_reading_questions_json, "web reading_questions mirror differs")

    sections = {row.get("section_id"): row.get("text", "") for row in load_jsonl(paths.private_dir / "book_sections.jsonl")}
    chapters = chapters_payload.get("chapters", [])
    questions = questions_payload.get("questions", [])

    if len(chapters) != 25:
        add_error(findings, "chapter_reading_cards.chapters", f"expected 25 chapters, got {len(chapters)}")

    source_excerpt_lengths: list[int] = []
    block_lengths: list[int] = []
    core_coverage = 0
    extra_coverage = 0
    total_blocks = 0
    min_blocks = 999

    for chapter_index, chapter in enumerate(chapters):
        section_id = chapter.get("section_id")
        section_text = sections.get(section_id, "")
        blocks = chapter.get("source_reading_blocks") or []
        core = chapter.get("core_source_reading_blocks") or []
        extra = chapter.get("extra_source_reading_blocks") or []
        source_excerpts = chapter.get("source_excerpts") or []
        source_excerpt_lengths.extend(len(item.get("text", "")) for item in source_excerpts if item.get("text"))

        if len(blocks) < 5:
            add_error(findings, f"chapters[{chapter_index}].source_reading_blocks", f"expected >=5 blocks, got {len(blocks)}")
        if len(core) < 2:
            add_error(findings, f"chapters[{chapter_index}].core_source_reading_blocks", f"expected >=2 core blocks, got {len(core)}")
        else:
            core_coverage += 1
        if len(extra) < 3:
            add_error(findings, f"chapters[{chapter_index}].extra_source_reading_blocks", f"expected >=3 extra blocks, got {len(extra)}")
        else:
            extra_coverage += 1

        min_blocks = min(min_blocks, len(blocks))
        total_blocks += len(blocks)
        for block_index, block in enumerate(blocks):
            text = block.get("text") or ""
            guide_note = block.get("guide_note") or ""
            block_lengths.append(len(text))
            for field in ["block_id", "text", "guide_note", "reading_role", "source_scope", "section_id", "review_status"]:
                if not block.get(field):
                    add_error(findings, f"chapters[{chapter_index}].source_reading_blocks[{block_index}].{field}", f"missing {field}")
            if block.get("section_id") != section_id:
                add_error(findings, f"chapters[{chapter_index}].source_reading_blocks[{block_index}].section_id", "section mismatch")
            if len(text) < 70:
                add_error(findings, f"chapters[{chapter_index}].source_reading_blocks[{block_index}].text", f"block too short: {len(text)}")
            if len(text) > 340:
                add_warning(findings, f"chapters[{chapter_index}].source_reading_blocks[{block_index}].text", f"block near long limit: {len(text)}")
            if not guide_note:
                add_error(findings, f"chapters[{chapter_index}].source_reading_blocks[{block_index}].guide_note", "guide_note is empty")
            if any(marker in text for marker in PLACEHOLDER_MARKERS):
                add_error(findings, f"chapters[{chapter_index}].source_reading_blocks[{block_index}].text", "placeholder marker found")
            if not text_in_section(text, section_text):
                add_error(findings, f"chapters[{chapter_index}].source_reading_blocks[{block_index}].text", "block text not found in matching section text")

    avg_block_length = round(sum(block_lengths) / len(block_lengths), 1) if block_lengths else 0
    avg_excerpt_length = round(sum(source_excerpt_lengths) / len(source_excerpt_lengths), 1) if source_excerpt_lengths else 0
    if avg_block_length < max(90, avg_excerpt_length + 35):
        add_error(findings, "source_reading_blocks.average_length", f"average block length {avg_block_length} is not clearly above excerpt average {avg_excerpt_length}")

    question_anchor_coverage = sum(1 for question in questions if question.get("source_anchor"))
    if len(questions) != 26:
        add_error(findings, "reading_questions.questions", f"expected 26 questions, got {len(questions)}")
    if question_anchor_coverage != 26:
        add_error(findings, "reading_questions.source_anchor", f"expected 26 source anchors, got {question_anchor_coverage}")

    public_blob = "\n".join(
        [
            json_blob(book),
            json_blob(chapters_payload),
            json_blob(questions_payload),
            json_blob(web_book),
            json_blob(web_chapters),
            json_blob(web_questions),
        ]
    )
    for marker in FORBIDDEN_PUBLIC_MARKERS:
        if marker.lower() in public_blob.lower():
            add_error(findings, "public-json", f"forbidden public marker found: {marker}")

    page_text = (paths.repo_root / "web" / "src" / "pages" / "ReadingGuideProjectPage.tsx").read_text(encoding="utf-8")
    if "原文节选" not in page_text and "原文阅读片段" not in page_text:
        add_error(findings, "ReadingGuideProjectPage.tsx", "page must contain 原文节选 or 原文阅读片段")
    if "source-reading-block" not in page_text:
        add_error(findings, "ReadingGuideProjectPage.tsx", "page must render source reading block UI")

    if book.get("status") != "draft":
        add_error(findings, paths.book_overview_json, f"status must remain draft, got {book.get('status')!r}")
    if book.get("release_phase") != "public-preview":
        add_error(findings, paths.book_overview_json, f"release_phase must remain public-preview, got {book.get('release_phase')!r}")
    if book.get("review_status") != "manual-review-pending":
        add_error(findings, paths.book_overview_json, f"review_status must remain manual-review-pending, got {book.get('review_status')!r}")

    manual_total, manual_blank = count_blank_manual_results(paths.report_path("manual_review_tasks_v0.7_a4.csv"))
    if manual_total != 95 or manual_blank != 95:
        add_error(findings, "manual_review_tasks_v0.7_a4.csv", f"expected 95 blank manual results, got total={manual_total}, blank={manual_blank}")
    if not csv_all_blank(paths.report_path("manual_review_decisions_template_v0.7_a7.csv"), "manual_result"):
        add_error(findings, "manual_review_decisions_template_v0.7_a7.csv", "A7 decisions template must remain blank")

    stats = {
        "total_blocks": total_blocks,
        "core_coverage": core_coverage,
        "extra_coverage": extra_coverage,
        "min_blocks": 0 if min_blocks == 999 else min_blocks,
        "average_block_length": avg_block_length,
        "average_excerpt_length": avg_excerpt_length,
        "question_anchor_coverage": question_anchor_coverage,
        "manual_blank": manual_blank,
        "status": book.get("status"),
        "release_phase": book.get("release_phase"),
        "review_status": book.get("review_status"),
    }
    return stats, findings


def render_report(project: str, version: str, stats: dict[str, Any], findings: list[Finding]) -> str:
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    lines = [
        f"# Source Reading Blocks Validation {version}",
        "",
        f"- Project: `{project}`",
        f"- Status: `{'PASS' if not errors else 'FAIL'}`",
        f"- Errors: `{len(errors)}`",
        f"- Warnings: `{len(warnings)}`",
        "",
        "## Counts",
        "",
        f"- source_reading_blocks total: `{stats['total_blocks']}`",
        f"- core_source_reading_blocks coverage: `{stats['core_coverage']}`",
        f"- extra_source_reading_blocks coverage: `{stats['extra_coverage']}`",
        f"- min blocks per letter: `{stats['min_blocks']}`",
        f"- average block length: `{stats['average_block_length']}`",
        f"- average short excerpt length: `{stats['average_excerpt_length']}`",
        f"- reading question source_anchor coverage: `{stats['question_anchor_coverage']}`",
        f"- manual review blank: `{stats['manual_blank']}`",
        "",
        "## State",
        "",
        f"- status: `{stats['status']}`",
        f"- release_phase: `{stats['release_phase']}`",
        f"- review_status: `{stats['review_status']}`",
        "- readinessForPromotion: `false`",
        "",
    ]
    if findings:
        lines.extend(["## Findings", "", "| severity | path | message |", "|---|---|---|"])
        for finding in findings:
            lines.append(f"| `{finding.severity}` | `{finding.path}` | {finding.message.replace('|', '｜')} |")
        lines.append("")
    else:
        lines.extend(["## Findings", "", "No findings.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", default=VERSION)
    args = parser.parse_args()

    paths = from_project(args.project)
    stats, findings = validate(args.project, args.version)
    report_path = paths.report_path("source_reading_blocks_validation_v0.7_a20.md")
    report_path.write_text(render_report(paths.slug, args.version, stats, findings), encoding="utf-8")
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    print("PASS" if not errors else "FAIL")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"total_blocks: {stats['total_blocks']}")
    print(f"core_coverage: {stats['core_coverage']}")
    print(f"extra_coverage: {stats['extra_coverage']}")
    print(f"average_block_length: {stats['average_block_length']}")
    print(f"Report: {report_path}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
