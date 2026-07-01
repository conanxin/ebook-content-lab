#!/usr/bin/env python3
"""Validate the A22 source reading block decisions import dry-run."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from scripts.lib.project_paths import from_project
except ModuleNotFoundError:
    from lib.project_paths import from_project


EXPECTED_ROWS = 125
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
    "v0.7_a22_source_reading_block_decisions_import_plan.md",
    "source_reading_block_decisions_import_dry_run_v0.7_a22.md",
    "source_reading_block_decisions_import_usage_v0.7_a22.md",
]


@dataclass(frozen=True)
class Finding:
    severity: str
    path: str
    message: str


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def add_error(findings: list[Finding], path: str | Path, message: str) -> None:
    findings.append(Finding("error", str(path), message))


def add_warning(findings: list[Finding], path: str | Path, message: str) -> None:
    findings.append(Finding("warning", str(path), message))


def report_value(text: str, key: str) -> str | None:
    match = re.search(rf"^- {re.escape(key)}:\s+`([^`]*)`", text, re.MULTILINE)
    return match.group(1) if match else None


def scan_file(path: Path, findings: list[Finding]) -> None:
    if not path.exists():
        add_error(findings, path, "missing expected A22 file")
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    lowered = text.lower()
    hits = [marker for marker in FORBIDDEN_MARKERS if marker.lower() in lowered]
    if hits:
        add_error(findings, path, f"forbidden markers found: {hits}")


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


def validate(project: str, version: str) -> tuple[dict[str, Any], list[Finding]]:
    paths = from_project(project)
    findings: list[Finding] = []

    for name in EXPECTED_FILES:
        scan_file(paths.report_path(name), findings)

    import_report = paths.report_path("source_reading_block_decisions_import_dry_run_v0.7_a22.md")
    template_path = paths.report_path("source_reading_block_decisions_template_v0.7_a21.csv")
    tasks_path = paths.report_path("source_reading_block_review_tasks_v0.7_a21.csv")
    a4_path = paths.report_path("manual_review_tasks_v0.7_a4.csv")
    a7_path = paths.report_path("manual_review_decisions_template_v0.7_a7.csv")

    scan_file(template_path, findings)
    scan_file(tasks_path, findings)

    report_text = import_report.read_text(encoding="utf-8", errors="replace") if import_report.exists() else ""
    template_rows = read_csv(template_path) if template_path.exists() else []
    task_rows = read_csv(tasks_path) if tasks_path.exists() else []
    a7_rows = read_csv(a7_path) if a7_path.exists() else []

    decisions_rows = len(template_rows)
    blank_decisions = sum(1 for row in template_rows if not (row.get("review_result") or "").strip())
    blank_strategies = sum(1 for row in template_rows if not (row.get("replacement_strategy") or "").strip())
    blank_notes = sum(1 for row in template_rows if not (row.get("review_notes") or "").strip())
    task_count = len(task_rows)
    manual_total, manual_blank = count_blank_manual_results(a4_path)

    report_total = report_value(report_text, "totalDecisionRows")
    report_blank = report_value(report_text, "blankDecisions")
    report_usable = report_value(report_text, "usableDecisions")
    report_invalid = report_value(report_text, "invalidDecisions")
    report_would_update = report_value(report_text, "wouldUpdate")
    report_applied = report_value(report_text, "applied")
    final_decision = report_value(report_text, "finalDecision")

    if decisions_rows != EXPECTED_ROWS:
        add_error(findings, template_path, f"expected {EXPECTED_ROWS} decisions rows, got {decisions_rows}")
    if task_count != EXPECTED_ROWS:
        add_error(findings, tasks_path, f"expected {EXPECTED_ROWS} A21 task rows, got {task_count}")
    if blank_decisions != EXPECTED_ROWS:
        add_error(findings, template_path, f"review_result values must all be blank, got {blank_decisions} blank")
    if blank_strategies != EXPECTED_ROWS:
        add_error(findings, template_path, f"replacement_strategy values must all be blank, got {blank_strategies} blank")
    if blank_notes != EXPECTED_ROWS:
        add_error(findings, template_path, f"review_notes values must all be blank, got {blank_notes} blank")

    if report_total != str(decisions_rows):
        add_error(findings, import_report, f"totalDecisionRows must be {decisions_rows}, got {report_total!r}")
    if report_blank != str(blank_decisions):
        add_error(findings, import_report, f"blankDecisions must be {blank_decisions}, got {report_blank!r}")
    if report_usable != "0":
        add_error(findings, import_report, f"usableDecisions must be 0, got {report_usable!r}")
    if report_invalid != "0":
        add_error(findings, import_report, f"invalidDecisions must be 0, got {report_invalid!r}")
    if report_would_update != "0":
        add_error(findings, import_report, f"wouldUpdate must be 0, got {report_would_update!r}")
    if report_applied != "false":
        add_error(findings, import_report, f"applied must be false, got {report_applied!r}")
    if final_decision != "dry_run_no_updates":
        add_error(findings, import_report, f"finalDecision must be dry_run_no_updates, got {final_decision!r}")

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
    if web_book.get("release_phase") != "public-preview":
        add_error(findings, paths.web_book_overview_json, f"web mirror release_phase must remain public-preview, got {web_book.get('release_phase')!r}")
    if web_book.get("review_status") != "manual-review-pending":
        add_error(findings, paths.web_book_overview_json, f"web mirror review_status must remain manual-review-pending, got {web_book.get('review_status')!r}")

    if manual_total != EXPECTED_MANUAL_REVIEW_ROWS or manual_blank != EXPECTED_MANUAL_REVIEW_ROWS:
        add_error(
            findings,
            a4_path,
            f"expected {EXPECTED_MANUAL_REVIEW_ROWS} blank manual review rows, got total={manual_total}, blank={manual_blank}",
        )
    if not all(not (row.get("manual_result") or "").strip() for row in a7_rows):
        add_error(findings, a7_path, "A7 decisions template manual_result must remain blank")

    dirty_forbidden = git_diff_names(
        paths.repo_root,
        [
            "projects/second-reading-guide/public",
            "web/public/projects/second-reading-guide",
            "web/src",
            "projects/second-reading-guide/reports/source_reading_block_decisions_template_v0.7_a21.csv",
            "projects/second-reading-guide/reports/source_reading_block_review_tasks_v0.7_a21.csv",
            "projects/second-reading-guide/reports/manual_review_tasks_v0.7_a4.csv",
            "projects/second-reading-guide/reports/manual_review_decisions_template_v0.7_a7.csv",
            "projects/second-reading-guide/private",
            "projects/dadou-shangdu",
            "web/public/projects/dadou-shangdu",
            "web/package-lock.json",
        ],
    )
    if dirty_forbidden:
        add_error(findings, "git-diff", f"A22 must not dirty forbidden paths: {dirty_forbidden}")

    stats = {
        "decisions_rows": decisions_rows,
        "blank_decisions": blank_decisions,
        "blank_strategies": blank_strategies,
        "blank_notes": blank_notes,
        "usable_decisions": int(report_usable or -1),
        "invalid_decisions": int(report_invalid or -1),
        "would_update": int(report_would_update or -1),
        "applied": report_applied or "missing",
        "ready_for_block_apply": False,
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
        f"# Source Reading Block Decisions Import Validation {version}",
        "",
        f"- Project: `{project}`",
        f"- Status: `{'PASS' if not errors else 'FAIL'}`",
        f"- Errors: `{len(errors)}`",
        f"- Warnings: `{len(warnings)}`",
        "",
        "## Counts",
        "",
        f"- decisions rows: `{stats['decisions_rows']}`",
        f"- blank decisions: `{stats['blank_decisions']}`",
        f"- blank replacement strategies: `{stats['blank_strategies']}`",
        f"- blank review notes: `{stats['blank_notes']}`",
        f"- usable decisions: `{stats['usable_decisions']}`",
        f"- invalid decisions: `{stats['invalid_decisions']}`",
        f"- wouldUpdate: `{stats['would_update']}`",
        f"- applied: `{stats['applied']}`",
        f"- readyForBlockApply: `{str(stats['ready_for_block_apply']).lower()}`",
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
            lines.append(f"| `{finding.severity}` | `{finding.path}` | {finding.message.replace('|', '/') } |")
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
    stats, findings = validate(args.project, args.version)
    report_path = paths.report_path("source_reading_block_decisions_import_validation_v0.7_a22.md")
    report_path.write_text(render_report(paths.slug, args.version, stats, findings), encoding="utf-8")

    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    print("PASS" if not errors else "FAIL")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"decisionsRows: {stats['decisions_rows']}")
    print(f"blankDecisions: {stats['blank_decisions']}")
    print(f"usableDecisions: {stats['usable_decisions']}")
    print(f"invalidDecisions: {stats['invalid_decisions']}")
    print(f"wouldUpdate: {stats['would_update']}")
    print(f"applied: {stats['applied']}")
    print(f"Report: {report_path}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
