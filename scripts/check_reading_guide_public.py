#!/usr/bin/env python3
"""Validate public reading-guide JSON files and web mirrors."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from scripts.lib.project_paths import from_project
except ModuleNotFoundError:
    from lib.project_paths import from_project


SCHEMA_VERSION = "reading-guide.v0.2"
STATUS = "draft"

FILES = [
    "book_overview.json",
    "chapter_reading_cards.json",
    "key_concepts.json",
    "quote_index.json",
    "reading_questions.json",
]

FORBIDDEN_PATTERNS = [
    "private/",
    "private\\",
    "private/source",
    "/mnt/",
    "D:/",
    "D:\\",
    "book.epub",
    "book.md",
    "book_sections.jsonl",
    "book_chunks.jsonl",
    "full_text",
    "raw_text",
    "chapter_text",
]


@dataclass(frozen=True)
class Finding:
    severity: str
    path: str
    message: str


def normalize_version(version: str) -> str:
    return version.lower().replace("-", "_")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def add_error(findings: list[Finding], path: str, message: str) -> None:
    findings.append(Finding("error", path, message))


def add_warning(findings: list[Finding], path: str, message: str) -> None:
    findings.append(Finding("warning", path, message))


def json_text(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def scan_forbidden(data: Any, path: str, findings: list[Finding]) -> None:
    lowered = json_text(data).lower()
    hits = [p for p in FORBIDDEN_PATTERNS if p.lower() in lowered]
    if hits:
        add_error(findings, path, f"Forbidden private/fulltext markers found: {hits}")


def expected_sections() -> list[str]:
    return [f"sec-{i:03d}" for i in range(6, 31)]


def check_common(name: str, data: dict[str, Any], findings: list[Finding]) -> None:
    if data.get("schema_version") != SCHEMA_VERSION:
        add_error(findings, name, f"schema_version must be {SCHEMA_VERSION}, got {data.get('schema_version')!r}")
    if data.get("status") != STATUS:
        add_error(findings, name, f"status must be {STATUS}, got {data.get('status')!r}")
    book = data.get("book")
    if not isinstance(book, dict):
        add_error(findings, f"{name}.book", "book must be a dict")
    else:
        for field in ["title", "author", "language", "source_type"]:
            if not book.get(field):
                add_error(findings, f"{name}.book.{field}", f"missing book field: {field}")
    scan_forbidden(data, name, findings)


def check_book_overview(data: dict[str, Any], findings: list[Finding]) -> None:
    required = [
        "one_sentence_summary",
        "reading_purpose",
        "structure_overview",
        "how_to_use",
        "limitations",
        "evidence_refs",
    ]
    for field in required:
        if field not in data:
            add_error(findings, f"book_overview.{field}", f"missing field: {field}")

    structure = data.get("structure_overview", {})
    if not isinstance(structure, dict):
        add_error(findings, "book_overview.structure_overview", "must be a dict")
    elif structure.get("body_letter_count") != 25:
        add_error(
            findings,
            "book_overview.structure_overview.body_letter_count",
            f"expected 25, got {structure.get('body_letter_count')}",
        )

    if not isinstance(data.get("how_to_use"), list) or not data.get("how_to_use"):
        add_error(findings, "book_overview.how_to_use", "must be a non-empty list")
    if not isinstance(data.get("limitations"), list) or not data.get("limitations"):
        add_error(findings, "book_overview.limitations", "must be a non-empty list")


def check_chapter_cards(data: dict[str, Any], findings: list[Finding]) -> None:
    chapters = data.get("chapters")
    if not isinstance(chapters, list):
        add_error(findings, "chapter_reading_cards.chapters", "chapters must be a list")
        return
    if len(chapters) != 25:
        add_error(findings, "chapter_reading_cards.chapters", f"expected 25 chapters, got {len(chapters)}")

    section_ids = [str(ch.get("section_id", "")) for ch in chapters]
    if section_ids != expected_sections():
        add_error(findings, "chapter_reading_cards.chapters.section_id", f"expected sec-006..sec-030 in order, got {section_ids}")

    required = [
        "chapter_id",
        "letter_id",
        "section_id",
        "order",
        "title",
        "summary",
        "places",
        "themes",
        "char_count",
        "paragraph_count",
        "chunk_count",
        "evidence_refs",
        "review_status",
    ]
    for idx, chapter in enumerate(chapters):
        for field in required:
            if field not in chapter:
                add_error(findings, f"chapter_reading_cards.chapters[{idx}].{field}", f"missing field: {field}")
        if chapter.get("review_status") != "auto_structural_draft":
            add_warning(
                findings,
                f"chapter_reading_cards.chapters[{idx}].review_status",
                f"unexpected review_status: {chapter.get('review_status')!r}",
            )


def check_key_concepts(data: dict[str, Any], findings: list[Finding]) -> None:
    concepts = data.get("concepts")
    if not isinstance(concepts, list):
        add_error(findings, "key_concepts.concepts", "concepts must be a list")
        return
    if not concepts:
        add_error(findings, "key_concepts.concepts", "concepts must not be empty in v0.7-A3")

    required = ["concept_id", "label", "description", "related_letters", "evidence_refs", "review_status"]
    for idx, concept in enumerate(concepts):
        for field in required:
            if field not in concept:
                add_error(findings, f"key_concepts.concepts[{idx}].{field}", f"missing field: {field}")
        if not isinstance(concept.get("related_letters"), list) or not concept.get("related_letters"):
            add_error(findings, f"key_concepts.concepts[{idx}].related_letters", "must be a non-empty list")


def check_quote_index(data: dict[str, Any], findings: list[Finding]) -> None:
    if data.get("quote_mode") != "structural_no_quote":
        add_error(findings, "quote_index.quote_mode", f"expected structural_no_quote, got {data.get('quote_mode')!r}")

    quotes = data.get("quotes")
    if not isinstance(quotes, list):
        add_error(findings, "quote_index.quotes", "quotes must be a list")
        return
    if len(quotes) != 25:
        add_error(findings, "quote_index.quotes", f"expected 25 structural quote entries, got {len(quotes)}")

    for idx, quote in enumerate(quotes):
        if quote.get("quote_mode") != "structural_no_quote":
            add_error(findings, f"quote_index.quotes[{idx}].quote_mode", "must be structural_no_quote")
        q = quote.get("quote", "")
        if q:
            add_error(findings, f"quote_index.quotes[{idx}].quote", "quote must be empty in structural_no_quote mode")
        if len(str(q)) > 80:
            add_error(findings, f"quote_index.quotes[{idx}].quote", f"quote too long: {len(str(q))}")


def check_reading_questions(data: dict[str, Any], findings: list[Finding]) -> None:
    questions = data.get("questions")
    if not isinstance(questions, list):
        add_error(findings, "reading_questions.questions", "questions must be a list")
        return
    if len(questions) < 26:
        add_error(findings, "reading_questions.questions", f"expected at least 26 questions, got {len(questions)}")

    required = ["question_id", "scope", "question", "basis", "review_status"]
    for idx, question in enumerate(questions):
        for field in required:
            if field not in question:
                add_error(findings, f"reading_questions.questions[{idx}].{field}", f"missing field: {field}")
        q = str(question.get("question", ""))
        if not q:
            add_error(findings, f"reading_questions.questions[{idx}].question", "question must be non-empty")
        if len(q) > 180:
            add_warning(findings, f"reading_questions.questions[{idx}].question", f"question is long: {len(q)} chars")


def check_mirror(name: str, public_data: dict[str, Any], web_data: dict[str, Any], findings: list[Finding]) -> None:
    if public_data != web_data:
        add_error(findings, name, "public JSON and web mirror JSON differ")


def render_report(project: str, version: str, payloads: dict[str, dict[str, Any]], findings: list[Finding]) -> str:
    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]
    status = "PASS" if not errors else "FAIL"

    lines = [
        f"# Reading Guide Public Validation {version}",
        "",
        f"- Project: `{project}`",
        f"- Status: `{status}`",
        f"- Errors: `{len(errors)}`",
        f"- Warnings: `{len(warnings)}`",
        f"- Schema version: `{SCHEMA_VERSION}`",
        "",
        "## Counts",
        "",
        f"- Chapters: `{len(payloads.get('chapter_reading_cards.json', {}).get('chapters', []))}`",
        f"- Concepts: `{len(payloads.get('key_concepts.json', {}).get('concepts', []))}`",
        f"- Quote structural entries: `{len(payloads.get('quote_index.json', {}).get('quotes', []))}`",
        f"- Questions: `{len(payloads.get('reading_questions.json', {}).get('questions', []))}`",
        "",
        "## Checks",
        "",
        "- 5 project public JSON files exist",
        "- 5 web mirror JSON files exist",
        "- schema version is `reading-guide.v0.2`",
        "- status remains `draft`",
        "- 25 chapter cards cover `sec-006` through `sec-030`",
        "- quote index uses `structural_no_quote`",
        "- no private path or full text markers are present",
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
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    paths = from_project(args.project)
    findings: list[Finding] = []
    payloads: dict[str, dict[str, Any]] = {}

    for name in FILES:
        public_path = paths.public_path(name)
        web_path = paths.web_project_path(name)

        if not public_path.exists():
            add_error(findings, name, f"missing public file: {public_path}")
            continue
        if not web_path.exists():
            add_error(findings, name, f"missing web mirror file: {web_path}")
            continue

        public_data = load_json(public_path)
        web_data = load_json(web_path)
        payloads[name] = public_data

        check_mirror(name, public_data, web_data, findings)
        check_common(name, public_data, findings)

    if "book_overview.json" in payloads:
        check_book_overview(payloads["book_overview.json"], findings)
    if "chapter_reading_cards.json" in payloads:
        check_chapter_cards(payloads["chapter_reading_cards.json"], findings)
    if "key_concepts.json" in payloads:
        check_key_concepts(payloads["key_concepts.json"], findings)
    if "quote_index.json" in payloads:
        check_quote_index(payloads["quote_index.json"], findings)
    if "reading_questions.json" in payloads:
        check_reading_questions(payloads["reading_questions.json"], findings)

    report_path = paths.report_path(f"reading_guide_public_validation_{normalize_version(args.version)}.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(paths.slug, args.version, payloads, findings), encoding="utf-8")

    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]
    print("PASS" if not errors else "FAIL")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Report: {report_path}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
