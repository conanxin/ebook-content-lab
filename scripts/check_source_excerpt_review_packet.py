#!/usr/bin/env python3
"""Validate the v0.7-A19 source excerpt review packet."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from scripts.lib.project_paths import from_project
except ModuleNotFoundError:
    from lib.project_paths import from_project


VERSION = "v0.7-A19"

FORBIDDEN_MARKERS = [
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

EXPECTED_FILES = [
    "v0.7_a19_source_excerpt_review_plan.md",
    "source_excerpt_review_packet_v0.7_a19.md",
    "source_excerpt_review_tasks_v0.7_a19.csv",
    "source_excerpt_review_decisions_template_v0.7_a19.csv",
    "source_excerpt_review_summary_v0.7_a19.json",
]


@dataclass(frozen=True)
class Finding:
    severity: str
    path: str
    message: str


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def add_error(findings: list[Finding], path: str | Path, message: str) -> None:
    findings.append(Finding("error", str(path), message))


def add_warning(findings: list[Finding], path: str | Path, message: str) -> None:
    findings.append(Finding("warning", str(path), message))


def git_diff_names(repo_root: Path, paths: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--", *paths],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def count_blank_manual_results(csv_path: Path) -> tuple[int, int]:
    rows = read_csv(csv_path)
    blank = sum(1 for row in rows if not (row.get("manual_result") or "").strip())
    return len(rows), blank


def check_file_exists_and_markers(path: Path, findings: list[Finding]) -> None:
    if not path.exists():
        add_error(findings, path, "missing expected A19 file")
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    lowered = text.lower()
    hits = [marker for marker in FORBIDDEN_MARKERS if marker.lower() in lowered]
    if hits:
        add_error(findings, path, f"forbidden markers found: {hits}")


def validate(project: str, version: str) -> tuple[dict[str, Any], list[Finding]]:
    paths = from_project(project)
    findings: list[Finding] = []

    for name in EXPECTED_FILES:
        check_file_exists_and_markers(paths.report_path(name), findings)

    tasks_path = paths.report_path("source_excerpt_review_tasks_v0.7_a19.csv")
    template_path = paths.report_path("source_excerpt_review_decisions_template_v0.7_a19.csv")
    summary_path = paths.report_path("source_excerpt_review_summary_v0.7_a19.json")
    tasks = read_csv(tasks_path) if tasks_path.exists() else []
    template = read_csv(template_path) if template_path.exists() else []
    summary = read_json(summary_path) if summary_path.exists() else {}

    if len(tasks) != 100:
        add_error(findings, tasks_path, f"expected 100 task rows, got {len(tasks)}")
    if len(template) != 100:
        add_error(findings, template_path, f"expected 100 template rows, got {len(template)}")
    if summary.get("totalExcerptTasks") != 100:
        add_error(findings, summary_path, f"expected totalExcerptTasks=100, got {summary.get('totalExcerptTasks')!r}")

    task_ids = [row.get("excerpt_task_id", "") for row in tasks]
    if len(task_ids) != len(set(task_ids)):
        add_error(findings, tasks_path, "excerpt_task_id values must be unique")

    letters = {row.get("letter_id") for row in tasks if row.get("letter_id")}
    if len(letters) != 25:
        add_error(findings, tasks_path, f"expected 25 letters covered, got {len(letters)}")
    per_letter = Counter(row.get("letter_id", "") for row in tasks)
    low_letters = {letter: count for letter, count in per_letter.items() if count < 4}
    if low_letters:
        add_error(findings, tasks_path, f"letters with fewer than 4 excerpt tasks: {low_letters}")

    priority_counts = Counter(row.get("review_priority", "") for row in tasks)
    if priority_counts.get("P0", 0) < 25:
        add_error(findings, tasks_path, f"expected at least 25 P0 tasks, got {priority_counts.get('P0', 0)}")

    for row_index, row in enumerate(tasks):
        for field in [
            "excerpt_task_id",
            "letter_id",
            "section_id",
            "chapter_title",
            "excerpt_index",
            "placement",
            "excerpt_text",
            "excerpt_note",
            "excerpt_type",
            "review_priority",
            "review_question",
            "suggested_checks",
        ]:
            if not (row.get(field) or "").strip():
                add_error(findings, f"{tasks_path}:{row_index + 2}", f"missing field: {field}")
        for blank_field in ["review_result", "review_notes", "reviewer", "reviewed_at"]:
            if (row.get(blank_field) or "").strip():
                add_error(findings, f"{tasks_path}:{row_index + 2}", f"{blank_field} must be blank")
        if row.get("placement") not in {"core", "extra", "source"}:
            add_error(findings, f"{tasks_path}:{row_index + 2}", f"invalid placement: {row.get('placement')!r}")
        if row.get("review_priority") not in {"P0", "P1", "P2"}:
            add_error(findings, f"{tasks_path}:{row_index + 2}", f"invalid review_priority: {row.get('review_priority')!r}")

    template_ids = [row.get("excerpt_task_id", "") for row in template]
    if template_ids != task_ids:
        add_error(findings, template_path, "template excerpt_task_id order must match tasks CSV")
    for row_index, row in enumerate(template):
        for blank_field in ["review_result", "review_notes", "reviewer", "reviewed_at"]:
            if (row.get(blank_field) or "").strip():
                add_error(findings, f"{template_path}:{row_index + 2}", f"{blank_field} must be blank")

    if summary.get("lettersCovered") != 25:
        add_error(findings, summary_path, f"expected lettersCovered=25, got {summary.get('lettersCovered')!r}")
    if summary.get("blankReviewResults") != 100:
        add_error(findings, summary_path, f"expected blankReviewResults=100, got {summary.get('blankReviewResults')!r}")
    if summary.get("readyForExcerptApply") is not False:
        add_error(findings, summary_path, "readyForExcerptApply must be false")
    if summary.get("status") != "review-packet-only":
        add_error(findings, summary_path, f"expected status=review-packet-only, got {summary.get('status')!r}")

    book = read_json(paths.book_overview_json)
    web_book = read_json(paths.web_book_overview_json)
    if book.get("status") != "draft":
        add_error(findings, paths.book_overview_json, f"public status must remain draft, got {book.get('status')!r}")
    if book.get("release_phase") != "public-preview":
        add_error(findings, paths.book_overview_json, f"release_phase must remain public-preview, got {book.get('release_phase')!r}")
    if book.get("review_status") != "manual-review-pending":
        add_error(findings, paths.book_overview_json, f"review_status must remain manual-review-pending, got {book.get('review_status')!r}")
    if web_book.get("status") != "draft":
        add_error(findings, paths.web_book_overview_json, f"web mirror status must remain draft, got {web_book.get('status')!r}")

    manual_total, manual_blank = count_blank_manual_results(paths.report_path("manual_review_tasks_v0.7_a4.csv"))
    if manual_total != 95 or manual_blank != 95:
        add_error(findings, "manual_review_tasks_v0.7_a4.csv", f"expected 95 blank manual results, got total={manual_total}, blank={manual_blank}")
    a7_template = read_csv(paths.report_path("manual_review_decisions_template_v0.7_a7.csv"))
    if not all(not (row.get("manual_result") or "").strip() for row in a7_template):
        add_error(findings, "manual_review_decisions_template_v0.7_a7.csv", "A7 decisions template must remain blank")

    dirty_forbidden = git_diff_names(
        paths.repo_root,
        [
            "projects/second-reading-guide/public",
            "web/public/projects/second-reading-guide",
            "web/src",
            "projects/second-reading-guide/reports/manual_review_tasks_v0.7_a4.csv",
            "projects/second-reading-guide/reports/manual_review_decisions_template_v0.7_a7.csv",
            "projects/second-reading-guide/private",
            "projects/dadou-shangdu",
            "web/public/projects/dadou-shangdu",
            "web/package-lock.json",
        ],
    )
    if dirty_forbidden:
        add_error(findings, "git-diff", f"A19 must not dirty forbidden paths: {dirty_forbidden}")

    stats = {
        "task_count": len(tasks),
        "template_count": len(template),
        "letters_covered": len(letters),
        "p0": priority_counts.get("P0", 0),
        "p1": priority_counts.get("P1", 0),
        "p2": priority_counts.get("P2", 0),
        "blank_review_results": sum(1 for row in tasks if not (row.get("review_result") or "").strip()),
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
        f"# Source Excerpt Review Validation {version}",
        "",
        f"- Project: `{project}`",
        f"- Status: `{'PASS' if not errors else 'FAIL'}`",
        f"- Errors: `{len(errors)}`",
        f"- Warnings: `{len(warnings)}`",
        "",
        "## Counts",
        "",
        f"- excerpt review tasks: `{stats['task_count']}`",
        f"- decisions template rows: `{stats['template_count']}`",
        f"- letters covered: `{stats['letters_covered']}`",
        f"- P0/P1/P2: `{stats['p0']}` / `{stats['p1']}` / `{stats['p2']}`",
        f"- blank review results: `{stats['blank_review_results']}`",
        f"- A4 manual review blank: `{stats['manual_blank']}`",
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
    report_path = paths.report_path("source_excerpt_review_validation_v0.7_a19.md")
    report_path.write_text(render_report(paths.slug, args.version, stats, findings), encoding="utf-8")
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    print("PASS" if not errors else "FAIL")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Tasks: {stats['task_count']}")
    print(f"Letters covered: {stats['letters_covered']}")
    print(f"P0/P1/P2: {stats['p0']}/{stats['p1']}/{stats['p2']}")
    print(f"Report: {report_path}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
