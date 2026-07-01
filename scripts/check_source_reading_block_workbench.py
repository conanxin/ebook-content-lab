#!/usr/bin/env python3
"""Validate the A21 source reading block workbench."""

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


VERSION = "v0.7-A21"

EXPECTED_TASKS = 125
EXPECTED_LETTERS = 25
EXPECTED_MANUAL_REVIEW_ROWS = 95

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
    "v0.7_a21_source_reading_block_workbench_plan.md",
    "source_reading_block_workbench_v0.7_a21.md",
    "source_reading_block_review_tasks_v0.7_a21.csv",
    "source_reading_block_decisions_template_v0.7_a21.csv",
    "source_reading_block_review_summary_v0.7_a21.json",
    "source_reading_block_review_usage_v0.7_a21.md",
]

REQUIRED_TASK_FIELDS = [
    "block_task_id",
    "letter_id",
    "section_id",
    "chapter_title",
    "block_index",
    "current_placement",
    "block_text",
    "block_length",
    "guide_note",
    "reading_role",
    "source_scope",
    "review_priority",
    "review_question",
    "suggested_checks",
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


def check_file_exists_and_markers(path: Path, findings: list[Finding]) -> None:
    if not path.exists():
        add_error(findings, path, "missing expected A21 file")
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    lowered = text.lower()
    hits = [marker for marker in FORBIDDEN_MARKERS if marker.lower() in lowered]
    if hits:
        add_error(findings, path, f"forbidden markers found: {hits}")


def count_blank_manual_results(csv_path: Path) -> tuple[int, int]:
    rows = read_csv(csv_path)
    blank = sum(1 for row in rows if not (row.get("manual_result") or "").strip())
    return len(rows), blank


def block_id(block: dict[str, Any], letter_id: str, index: int) -> str:
    return str(block.get("block_id") or f"{letter_id}-reading-block-{index:02d}")


def public_block_counts(chapters: dict[str, Any]) -> tuple[int, int, int]:
    total = 0
    core = 0
    extra = 0
    for chapter in chapters.get("chapters", []):
        total += len(chapter.get("source_reading_blocks") or [])
        core += len(chapter.get("core_source_reading_blocks") or [])
        extra += len(chapter.get("extra_source_reading_blocks") or [])
    return total, core, extra


def validate(project: str, version: str) -> tuple[dict[str, Any], list[Finding]]:
    paths = from_project(project)
    findings: list[Finding] = []

    for name in EXPECTED_FILES:
        check_file_exists_and_markers(paths.report_path(name), findings)

    tasks_path = paths.report_path("source_reading_block_review_tasks_v0.7_a21.csv")
    template_path = paths.report_path("source_reading_block_decisions_template_v0.7_a21.csv")
    summary_path = paths.report_path("source_reading_block_review_summary_v0.7_a21.json")
    tasks = read_csv(tasks_path) if tasks_path.exists() else []
    template = read_csv(template_path) if template_path.exists() else []
    summary = read_json(summary_path) if summary_path.exists() else {}

    if len(tasks) != EXPECTED_TASKS:
        add_error(findings, tasks_path, f"expected {EXPECTED_TASKS} task rows, got {len(tasks)}")
    if len(template) != EXPECTED_TASKS:
        add_error(findings, template_path, f"expected {EXPECTED_TASKS} template rows, got {len(template)}")
    if summary.get("totalBlockTasks") != EXPECTED_TASKS:
        add_error(findings, summary_path, f"expected totalBlockTasks={EXPECTED_TASKS}, got {summary.get('totalBlockTasks')!r}")

    task_ids = [row.get("block_task_id", "") for row in tasks]
    if len(task_ids) != len(set(task_ids)):
        add_error(findings, tasks_path, "block_task_id values must be unique")

    letters = {row.get("letter_id") for row in tasks if row.get("letter_id")}
    if len(letters) != EXPECTED_LETTERS:
        add_error(findings, tasks_path, f"expected {EXPECTED_LETTERS} letters covered, got {len(letters)}")
    per_letter = Counter(row.get("letter_id", "") for row in tasks)
    low_letters = {letter: count for letter, count in per_letter.items() if count < 5}
    if low_letters:
        add_error(findings, tasks_path, f"letters with fewer than 5 block tasks: {low_letters}")

    priority_counts = Counter(row.get("review_priority", "") for row in tasks)
    placement_counts = Counter(row.get("current_placement", "") for row in tasks)
    if priority_counts.get("P0", 0) < EXPECTED_LETTERS:
        add_error(findings, tasks_path, f"expected at least {EXPECTED_LETTERS} P0 tasks, got {priority_counts.get('P0', 0)}")

    for row_index, row in enumerate(tasks):
        path_label = f"{tasks_path}:{row_index + 2}"
        for field in REQUIRED_TASK_FIELDS:
            if not (row.get(field) or "").strip():
                add_error(findings, path_label, f"missing field: {field}")
        for blank_field in ["review_result", "replacement_strategy", "review_notes", "reviewer", "reviewed_at"]:
            if (row.get(blank_field) or "").strip():
                add_error(findings, path_label, f"{blank_field} must be blank")
        if row.get("current_placement") not in {"core", "extra", "source"}:
            add_error(findings, path_label, f"invalid current_placement: {row.get('current_placement')!r}")
        if row.get("review_priority") not in {"P0", "P1", "P2"}:
            add_error(findings, path_label, f"invalid review_priority: {row.get('review_priority')!r}")
        try:
            length = int(row.get("block_length", ""))
        except ValueError:
            add_error(findings, path_label, f"block_length must be an integer, got {row.get('block_length')!r}")
        else:
            if length != len(row.get("block_text", "")):
                add_error(findings, path_label, "block_length does not match block_text length")

    template_ids = [row.get("block_task_id", "") for row in template]
    if template_ids != task_ids:
        add_error(findings, template_path, "template block_task_id order must match tasks CSV")
    for row_index, row in enumerate(template):
        path_label = f"{template_path}:{row_index + 2}"
        for blank_field in ["review_result", "replacement_strategy", "review_notes", "reviewer", "reviewed_at"]:
            if (row.get(blank_field) or "").strip():
                add_error(findings, path_label, f"{blank_field} must be blank")

    if summary.get("lettersCovered") != EXPECTED_LETTERS:
        add_error(findings, summary_path, f"expected lettersCovered={EXPECTED_LETTERS}, got {summary.get('lettersCovered')!r}")
    if summary.get("blankReviewResults") != EXPECTED_TASKS:
        add_error(findings, summary_path, f"expected blankReviewResults={EXPECTED_TASKS}, got {summary.get('blankReviewResults')!r}")
    if summary.get("readyForBlockApply") is not False:
        add_error(findings, summary_path, "readyForBlockApply must be false")
    if summary.get("status") != "review-workbench-only":
        add_error(findings, summary_path, f"expected status=review-workbench-only, got {summary.get('status')!r}")

    book = read_json(paths.book_overview_json)
    web_book = read_json(paths.web_book_overview_json)
    chapters = read_json(paths.chapter_reading_cards_json)
    total_blocks, core_blocks, extra_blocks = public_block_counts(chapters)

    if total_blocks != EXPECTED_TASKS:
        add_error(findings, paths.chapter_reading_cards_json, f"expected {EXPECTED_TASKS} public source reading blocks, got {total_blocks}")
    if placement_counts.get("core", 0) != core_blocks:
        add_error(findings, tasks_path, f"core task count {placement_counts.get('core', 0)} does not match public core block count {core_blocks}")
    if placement_counts.get("extra", 0) != extra_blocks:
        add_error(findings, tasks_path, f"extra task count {placement_counts.get('extra', 0)} does not match public extra block count {extra_blocks}")

    if book.get("status") != "draft":
        add_error(findings, paths.book_overview_json, f"public status must remain draft, got {book.get('status')!r}")
    if book.get("release_phase") != "public-preview":
        add_error(findings, paths.book_overview_json, f"release_phase must remain public-preview, got {book.get('release_phase')!r}")
    if book.get("review_status") != "manual-review-pending":
        add_error(findings, paths.book_overview_json, f"review_status must remain manual-review-pending, got {book.get('review_status')!r}")
    if web_book.get("status") != "draft":
        add_error(findings, paths.web_book_overview_json, f"web mirror status must remain draft, got {web_book.get('status')!r}")
    if web_book.get("release_phase") != "public-preview":
        add_error(findings, paths.web_book_overview_json, f"web mirror release_phase must remain public-preview, got {web_book.get('release_phase')!r}")
    if web_book.get("review_status") != "manual-review-pending":
        add_error(findings, paths.web_book_overview_json, f"web mirror review_status must remain manual-review-pending, got {web_book.get('review_status')!r}")

    manual_total, manual_blank = count_blank_manual_results(paths.report_path("manual_review_tasks_v0.7_a4.csv"))
    if manual_total != EXPECTED_MANUAL_REVIEW_ROWS or manual_blank != EXPECTED_MANUAL_REVIEW_ROWS:
        add_error(
            findings,
            "manual_review_tasks_v0.7_a4.csv",
            f"expected {EXPECTED_MANUAL_REVIEW_ROWS} blank manual results, got total={manual_total}, blank={manual_blank}",
        )
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
        add_error(findings, "git-diff", f"A21 must not dirty forbidden paths: {dirty_forbidden}")

    stats = {
        "task_count": len(tasks),
        "template_count": len(template),
        "letters_covered": len(letters),
        "p0": priority_counts.get("P0", 0),
        "p1": priority_counts.get("P1", 0),
        "p2": priority_counts.get("P2", 0),
        "core": placement_counts.get("core", 0),
        "extra": placement_counts.get("extra", 0),
        "blank_review_results": sum(1 for row in tasks if not (row.get("review_result") or "").strip()),
        "blank_replacement_strategy": sum(1 for row in tasks if not (row.get("replacement_strategy") or "").strip()),
        "manual_blank": manual_blank,
        "ready_for_block_apply": summary.get("readyForBlockApply"),
        "status": book.get("status"),
        "release_phase": book.get("release_phase"),
        "review_status": book.get("review_status"),
        "total_public_blocks": total_blocks,
    }
    return stats, findings


def render_report(project: str, version: str, stats: dict[str, Any], findings: list[Finding]) -> str:
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    lines = [
        f"# Source Reading Block Workbench Validation {version}",
        "",
        f"- Project: `{project}`",
        f"- Status: `{'PASS' if not errors else 'FAIL'}`",
        f"- Errors: `{len(errors)}`",
        f"- Warnings: `{len(warnings)}`",
        "",
        "## Counts",
        "",
        f"- source reading block review tasks: `{stats['task_count']}`",
        f"- decisions template rows: `{stats['template_count']}`",
        f"- letters covered: `{stats['letters_covered']}`",
        f"- current core/extra tasks: `{stats['core']}` / `{stats['extra']}`",
        f"- P0/P1/P2: `{stats['p0']}` / `{stats['p1']}` / `{stats['p2']}`",
        f"- blank review results: `{stats['blank_review_results']}`",
        f"- blank replacement strategies: `{stats['blank_replacement_strategy']}`",
        f"- A4 manual review blank: `{stats['manual_blank']}`",
        "",
        "## State",
        "",
        f"- status: `{stats['status']}`",
        f"- release_phase: `{stats['release_phase']}`",
        f"- review_status: `{stats['review_status']}`",
        "- readinessForPromotion: `false`",
        f"- readyForBlockApply: `{str(stats['ready_for_block_apply']).lower()}`",
        "",
    ]
    if findings:
        lines.extend(["## Findings", "", "| severity | path | message |", "|---|---|---|"])
        for finding in findings:
            lines.append(f"| `{finding.severity}` | `{finding.path}` | {finding.message.replace('|', '/') } |")
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
    report_path = paths.report_path("source_reading_block_workbench_validation_v0.7_a21.md")
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
