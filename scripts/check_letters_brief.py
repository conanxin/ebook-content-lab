#!/usr/bin/env python3
"""Validate working/letters_brief.json for a reading-guide project."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from scripts.lib.project_paths import from_project
except ModuleNotFoundError:
    from lib.project_paths import from_project


REQUIRED_TOP_LEVEL = {
    "project",
    "source_type",
    "status",
    "letter_count",
    "section_range",
    "source_artifacts",
    "privacy_boundary",
    "letters",
}

REQUIRED_LETTER_FIELDS = {
    "letter_id",
    "section_id",
    "order",
    "title",
    "char_count",
    "paragraph_count",
    "chunk_count",
    "chunk_ids",
    "brief",
    "places",
    "themes",
    "evidence_refs",
    "review_status",
}

FORBIDDEN_BODY_SECTIONS = {"sec-001", "sec-002", "sec-003", "sec-004", "sec-005", "sec-031"}

PRIVATE_PATTERNS = [
    "private/source",
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
    return version.lower().replace("-", "_").replace(".", ".")


def expected_sections() -> list[str]:
    return [f"sec-{i:03d}" for i in range(6, 31)]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def add_error(findings: list[Finding], path: str, message: str) -> None:
    findings.append(Finding("error", path, message))


def add_warning(findings: list[Finding], path: str, message: str) -> None:
    findings.append(Finding("warning", path, message))


def contains_forbidden_text(value: Any) -> list[str]:
    text = json.dumps(value, ensure_ascii=False)
    lowered = text.lower()
    return [pattern for pattern in PRIVATE_PATTERNS if pattern.lower() in lowered]


def validate(data: dict[str, Any], findings: list[Finding]) -> None:
    missing_top = sorted(REQUIRED_TOP_LEVEL - set(data.keys()))
    for field in missing_top:
        add_error(findings, "$", f"Missing top-level field: {field}")

    letters = data.get("letters")
    if not isinstance(letters, list):
        add_error(findings, "letters", "letters must be a list")
        return

    if data.get("letter_count") != len(letters):
        add_error(
            findings,
            "letter_count",
            f"letter_count={data.get('letter_count')} but len(letters)={len(letters)}",
        )
    if len(letters) != 25:
        add_error(findings, "letters", f"Expected 25 body letters, got {len(letters)}")

    section_ids = [str(letter.get("section_id", "")) for letter in letters]
    expected = expected_sections()
    if section_ids != expected:
        add_error(
            findings,
            "letters[*].section_id",
            f"Expected section coverage {expected[0]}..{expected[-1]} in order, got {section_ids}",
        )

    forbidden_present = sorted(set(section_ids) & FORBIDDEN_BODY_SECTIONS)
    if forbidden_present:
        add_error(
            findings,
            "letters[*].section_id",
            f"Forbidden non-body sections present: {forbidden_present}",
        )

    seen_letter_ids: set[str] = set()
    for index, letter in enumerate(letters, start=1):
        path = f"letters[{index - 1}]"
        missing = sorted(REQUIRED_LETTER_FIELDS - set(letter.keys()))
        for field in missing:
            add_error(findings, path, f"Missing letter field: {field}")

        letter_id = str(letter.get("letter_id", ""))
        if not re.fullmatch(r"letter-\d{3}", letter_id):
            add_error(findings, f"{path}.letter_id", f"Invalid letter_id: {letter_id}")
        if letter_id in seen_letter_ids:
            add_error(findings, f"{path}.letter_id", f"Duplicate letter_id: {letter_id}")
        seen_letter_ids.add(letter_id)

        if letter.get("order") != index:
            add_error(findings, f"{path}.order", f"Expected order {index}, got {letter.get('order')}")

        if not isinstance(letter.get("chunk_ids"), list) or not letter.get("chunk_ids"):
            add_error(findings, f"{path}.chunk_ids", "chunk_ids must be a non-empty list")

        if not isinstance(letter.get("brief"), str) or not letter.get("brief", "").strip():
            add_error(findings, f"{path}.brief", "brief must be a non-empty string")

        if not isinstance(letter.get("places"), list):
            add_error(findings, f"{path}.places", "places must be a list")

        if not isinstance(letter.get("themes"), list):
            add_error(findings, f"{path}.themes", "themes must be a list")

        evidence_refs = letter.get("evidence_refs")
        if not isinstance(evidence_refs, list) or not evidence_refs:
            add_error(findings, f"{path}.evidence_refs", "evidence_refs must be a non-empty list")
        else:
            for ref_index, ref in enumerate(evidence_refs):
                ref_path = f"{path}.evidence_refs[{ref_index}]"
                note = str(ref.get("note", ""))
                if len(note) > 160:
                    add_error(
                        findings,
                        f"{ref_path}.note",
                        f"evidence note too long: {len(note)} chars",
                    )
                forbidden = contains_forbidden_text(ref)
                if forbidden:
                    add_error(
                        findings,
                        ref_path,
                        f"Forbidden private/fulltext markers in evidence ref: {forbidden}",
                    )

        # letter rows should not contain those markers.
        forbidden_letter = contains_forbidden_text(letter)
        if forbidden_letter:
            add_error(
                findings,
                path,
                f"Forbidden private/fulltext markers in letter payload: {forbidden_letter}",
            )

    privacy = data.get("privacy_boundary", {})
    if privacy.get("contains_full_text") is not False:
        add_error(findings, "privacy_boundary.contains_full_text", "Expected false")
    if privacy.get("contains_long_excerpts") is not False:
        add_error(findings, "privacy_boundary.contains_long_excerpts", "Expected false")


def render_report(project: str, version: str, data: dict[str, Any], findings: list[Finding]) -> str:
    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]
    status = "PASS" if not errors else "FAIL"
    lines = [
        f"# Letters Brief Validation {version}",
        "",
        f"- Project: `{project}`",
        f"- Status: `{status}`",
        f"- Errors: `{len(errors)}`",
        f"- Warnings: `{len(warnings)}`",
        f"- Letter count: `{data.get('letter_count')}`",
        f"- Section range: {data.get('section_range', {}).get('start')} → `{data.get('section_range', {}).get('end')}`",
        "",
        "## Checks",
        "",
        "- letters_brief.json exists",
        "- `letter_count == 25`",
        "- section coverage is exactly sec-006 through `sec-030`",
        "- non-body sections are excluded",
        "- required fields are present",
        "- evidence refs are structural and safe",
        "- privacy boundary flags are false for full text and long excerpts",
        "",
    ]
    if findings:
        lines.extend(["## Findings", "", "| severity | path | message |", "|---|---|---|"])
        for finding in findings:
            msg = finding.message.replace("|", "｜")
            lines.append(f"| {finding.severity} | {finding.path} | {msg} |")
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
    brief_path = paths.working_path("letters_brief.json")
    report_path = paths.report_path(f"letters_brief_validation_{normalize_version(args.version)}.md")

    findings: list[Finding] = []
    if not brief_path.exists():
        add_error(findings, str(brief_path), "Missing working/letters_brief.json")
        data: dict[str, Any] = {}
    else:
        data = load_json(brief_path)
        validate(data, findings)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(paths.slug, args.version, data, findings), encoding="utf-8")

    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]
    print("PASS" if not errors else "FAIL")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Report: {report_path}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())