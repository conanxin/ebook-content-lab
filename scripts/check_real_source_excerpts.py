#!/usr/bin/env python3
"""Validate the v0.7-A18 real source excerpt layer."""

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


VERSION = "v0.7-A18"

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

FINAL_STATUS_MARKERS = {"reviewed", "final", "publish-ready"}


@dataclass(frozen=True)
class Finding:
    severity: str
    path: str
    message: str


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def add_error(findings: list[Finding], path: str, message: str) -> None:
    findings.append(Finding("error", path, message))


def add_warning(findings: list[Finding], path: str, message: str) -> None:
    findings.append(Finding("warning", path, message))


def json_blob(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def excerpt_in_source(excerpt: str, section_text: str, chunk_texts: list[str]) -> bool:
    if excerpt and excerpt in section_text:
        return True
    normalized_excerpt = normalize_text(excerpt)
    if normalized_excerpt and normalized_excerpt in normalize_text(section_text):
        return True
    for chunk_text in chunk_texts:
        if excerpt and excerpt in chunk_text:
            return True
        if normalized_excerpt and normalized_excerpt in normalize_text(chunk_text):
            return True
    return False


def count_blank_manual_results(csv_path: Path) -> tuple[int, int]:
    with csv_path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    blank = sum(1 for row in rows if not (row.get("manual_result") or "").strip())
    return len(rows), blank


def decisions_template_blank(csv_path: Path) -> bool:
    with csv_path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    return all(not (row.get("manual_result") or "").strip() for row in rows)


def validate(project: str, version: str) -> tuple[dict[str, Any], list[Finding]]:
    paths = from_project(project)
    findings: list[Finding] = []

    book = read_json(paths.book_overview_json)
    chapters_payload = read_json(paths.chapter_reading_cards_json)
    questions = read_json(paths.reading_questions_json)
    web_book = read_json(paths.web_book_overview_json)
    web_chapters = read_json(paths.web_chapter_reading_cards_json)
    web_questions = read_json(paths.web_reading_questions_json)

    sections = {row.get("section_id"): row for row in load_jsonl(paths.private_dir / "book_sections.jsonl")}
    chunks_by_section: dict[str, list[str]] = {}
    for row in load_jsonl(paths.private_dir / "book_chunks.jsonl"):
        chunks_by_section.setdefault(row.get("section_id"), []).append(row.get("text", ""))

    if book != web_book:
        add_error(findings, "web/book_overview.json", "web mirror differs from project public JSON")
    if chapters_payload != web_chapters:
        add_error(findings, "web/chapter_reading_cards.json", "web mirror differs from project public JSON")
    if questions != web_questions:
        add_error(findings, "web/reading_questions.json", "web mirror differs from project public JSON")

    if book.get("status") != "draft":
        add_error(findings, "book_overview.status", f"expected draft, got {book.get('status')!r}")
    if book.get("release_phase") != "public-preview":
        add_error(findings, "book_overview.release_phase", f"expected public-preview, got {book.get('release_phase')!r}")
    if book.get("review_status") != "manual-review-pending":
        add_error(findings, "book_overview.review_status", f"expected manual-review-pending, got {book.get('review_status')!r}")

    status_blob = json_blob(book).lower()
    for marker in FINAL_STATUS_MARKERS:
        if f'"status": "{marker}"' in status_blob or f'"review_status": "{marker}"' in status_blob:
            add_error(findings, "book_overview", f"final/promotion marker found: {marker}")

    public_blob = "\n".join(
        [
            json_blob(book),
            json_blob(chapters_payload),
            json_blob(questions),
            json_blob(web_book),
            json_blob(web_chapters),
            json_blob(web_questions),
        ]
    )
    for marker in FORBIDDEN_PUBLIC_MARKERS:
        if marker.lower() in public_blob.lower():
            add_error(findings, "public-json", f"forbidden marker found: {marker}")

    chapters = chapters_payload.get("chapters", [])
    if len(chapters) != 25:
        add_error(findings, "chapter_reading_cards.chapters", f"expected 25 chapters, got {len(chapters)}")

    source_total = 0
    core_coverage = 0
    extra_coverage = 0
    min_per_letter = 999
    placeholder_hits = 0
    real_lookup_failures = 0

    for idx, chapter in enumerate(chapters):
        section_id = chapter.get("section_id")
        section = sections.get(section_id)
        section_text = section.get("text", "") if section else ""
        chunk_texts = chunks_by_section.get(section_id, [])
        excerpts = chapter.get("source_excerpts") or []
        core = chapter.get("core_source_excerpts") or []
        extra = chapter.get("extra_source_excerpts") or []

        if len(excerpts) < 4:
            add_error(findings, f"chapters[{idx}].source_excerpts", f"expected >=4 excerpts, got {len(excerpts)}")
        if len(core) < 2:
            add_error(findings, f"chapters[{idx}].core_source_excerpts", f"expected >=2 core excerpts, got {len(core)}")
        else:
            core_coverage += 1
        if len(extra) < 2:
            add_error(findings, f"chapters[{idx}].extra_source_excerpts", f"expected >=2 extra excerpts, got {len(extra)}")
        else:
            extra_coverage += 1

        min_per_letter = min(min_per_letter, len(excerpts))
        source_total += len(excerpts)

        for excerpt_idx, excerpt in enumerate(excerpts):
            text = excerpt.get("text") or ""
            note = excerpt.get("note") or ""
            if not text:
                add_error(findings, f"chapters[{idx}].source_excerpts[{excerpt_idx}].text", "text is empty")
            if not note:
                add_error(findings, f"chapters[{idx}].source_excerpts[{excerpt_idx}].note", "note is empty")
            for field in ["excerpt_type", "section_id", "review_status"]:
                if not excerpt.get(field):
                    add_error(findings, f"chapters[{idx}].source_excerpts[{excerpt_idx}].{field}", f"missing {field}")
            if excerpt.get("section_id") != section_id:
                add_error(findings, f"chapters[{idx}].source_excerpts[{excerpt_idx}].section_id", "section_id mismatch")
            if any(marker in text for marker in PLACEHOLDER_MARKERS):
                placeholder_hits += 1
                add_error(findings, f"chapters[{idx}].source_excerpts[{excerpt_idx}].text", "placeholder marker found in excerpt text")
            if not excerpt_in_source(text, section_text, chunk_texts):
                real_lookup_failures += 1
                add_error(findings, f"chapters[{idx}].source_excerpts[{excerpt_idx}].text", "excerpt text not found in matching section/chunk")

    question_anchor_coverage = sum(1 for question in questions.get("questions", []) if question.get("source_anchor"))
    if len(questions.get("questions", [])) != 26:
        add_error(findings, "reading_questions.questions", f"expected 26 questions, got {len(questions.get('questions', []))}")
    if question_anchor_coverage != 26:
        add_error(findings, "reading_questions.source_anchor", f"expected 26 source anchors, got {question_anchor_coverage}")

    if "原文选段" not in public_blob and "原文摘录" not in public_blob:
        add_error(findings, "public-json", "reader-facing label 原文选段/原文摘录 not found")

    page_path = paths.repo_root / "web" / "src" / "pages" / "ReadingGuideProjectPage.tsx"
    page_text = page_path.read_text(encoding="utf-8")
    if "原文选段" not in page_text and "原文摘录" not in page_text:
        add_error(findings, str(page_path), "page UI does not contain 原文选段/原文摘录")
    for marker in ["用于定位本封信的场景和语气", "原文锚点待复核", "Structural reference only", "No source quote is published"]:
        if marker in page_text:
            add_error(findings, str(page_path), f"placeholder UI marker found: {marker}")

    tasks_total, manual_blank = count_blank_manual_results(paths.report_path("manual_review_tasks_v0.7_a4.csv"))
    if tasks_total != 95 or manual_blank != 95:
        add_error(findings, "manual_review_tasks_v0.7_a4.csv", f"expected 95 blank manual results, got total={tasks_total}, blank={manual_blank}")
    if not decisions_template_blank(paths.report_path("manual_review_decisions_template_v0.7_a7.csv")):
        add_error(findings, "manual_review_decisions_template_v0.7_a7.csv", "decisions template is not blank")

    stats = {
        "source_total": source_total,
        "core_coverage": core_coverage,
        "extra_coverage": extra_coverage,
        "min_per_letter": 0 if min_per_letter == 999 else min_per_letter,
        "placeholder_hits": placeholder_hits,
        "real_lookup_failures": real_lookup_failures,
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
        f"# Real Source Excerpts Validation {version}",
        "",
        f"- Project: `{project}`",
        f"- Status: `{'PASS' if not errors else 'FAIL'}`",
        f"- Errors: `{len(errors)}`",
        f"- Warnings: `{len(warnings)}`",
        "",
        "## Counts",
        "",
        f"- source_excerpts total: `{stats['source_total']}`",
        f"- core_source_excerpts coverage: `{stats['core_coverage']}`",
        f"- extra_source_excerpts coverage: `{stats['extra_coverage']}`",
        f"- min excerpts per letter: `{stats['min_per_letter']}`",
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
        "## Boundary Checks",
        "",
        "- public/web JSON mirror consistency checked",
        "- private/local path markers checked",
        "- source excerpt lookup checked against matching private section/chunk text",
        "- placeholder excerpt text markers checked",
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
    report_path = paths.report_path("real_source_excerpts_validation_v0.7_a18.md")
    report_path.write_text(render_report(paths.slug, args.version, stats, findings), encoding="utf-8")

    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    print("PASS" if not errors else "FAIL")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Report: {report_path}")
    print(json.dumps(stats, ensure_ascii=False, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
