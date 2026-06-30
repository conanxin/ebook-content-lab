#!/usr/bin/env python3
"""Validate reading-guide manual review tasks."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from scripts.lib.project_paths import from_project
except ModuleNotFoundError:
    from lib.project_paths import from_project


REQUIRED_COLUMNS = [
    "task_id",
    "priority",
    "category",
    "target_id",
    "target_title",
    "review_question",
    "source_file",
    "manual_result",
    "notes",
]

ALLOWED_PRIORITIES = {"P0", "P1", "P2"}

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


def add(findings: list[Finding], severity: str, path: Path | str, message: str) -> None:
    findings.append(Finding(severity, str(path), message))


def read_tasks(path: Path, findings: list[Finding]) -> list[dict[str, str]]:
    if not path.exists():
        add(findings, "error", path, "Missing manual review CSV.")
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        if fieldnames != REQUIRED_COLUMNS:
            add(findings, "error", path, f"Unexpected CSV columns: {fieldnames}")
        return [dict(row) for row in reader]


def read_json(path: Path, findings: list[Finding]) -> dict[str, Any]:
    if not path.exists():
        add(findings, "error", path, "Missing summary JSON.")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        add(findings, "error", path, f"Invalid JSON: {exc}")
        return {}


def scan_forbidden(path: Path, findings: list[Finding]) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    lowered = text.lower()
    hits = [pattern for pattern in FORBIDDEN_PATTERNS if pattern.lower() in lowered]
    if hits:
        add(findings, "error", path, f"Forbidden marker found: {hits}")


def validate_rows(rows: list[dict[str, str]], findings: list[Finding], csv_path: Path) -> None:
    seen: set[str] = set()
    for idx, row in enumerate(rows, start=2):
        task_id = row.get("task_id", "")
        if not task_id:
            add(findings, "error", f"{csv_path}:{idx}", "task_id is required.")
        elif task_id in seen:
            add(findings, "error", f"{csv_path}:{idx}", f"duplicate task_id: {task_id}")
        seen.add(task_id)

        priority = row.get("priority", "")
        if priority not in ALLOWED_PRIORITIES:
            add(findings, "error", f"{csv_path}:{idx}", f"invalid priority: {priority!r}")

        for field in ["category", "target_id", "review_question"]:
            if not row.get(field):
                add(findings, "error", f"{csv_path}:{idx}", f"{field} is required.")

        if row.get("manual_result"):
            add(findings, "error", f"{csv_path}:{idx}", "manual_result must be blank before human review.")


def validate_summary(rows: list[dict[str, str]], summary: dict[str, Any], findings: list[Finding], summary_path: Path) -> None:
    total = len(rows)
    priority_counts = Counter(row["priority"] for row in rows)
    category_counts = Counter(row["category"] for row in rows)

    if summary.get("totalTasks") != total:
        add(findings, "error", summary_path, f"totalTasks {summary.get('totalTasks')} does not match CSV rows {total}.")

    summary_priority = summary.get("priorityCounts", {})
    if sum(int(value) for value in summary_priority.values()) != total:
        add(findings, "error", summary_path, "priorityCounts do not sum to totalTasks.")
    for key, value in priority_counts.items():
        if int(summary_priority.get(key, -1)) != value:
            add(findings, "error", summary_path, f"priorityCounts.{key} expected {value}, got {summary_priority.get(key)}.")

    summary_category = summary.get("categoryCounts", {})
    if sum(int(value) for value in summary_category.values()) != total:
        add(findings, "error", summary_path, "categoryCounts do not sum to totalTasks.")
    for key, value in category_counts.items():
        if int(summary_category.get(key, -1)) != value:
            add(findings, "error", summary_path, f"categoryCounts.{key} expected {value}, got {summary_category.get(key)}.")


def validate_coverage(rows: list[dict[str, str]], findings: list[Finding]) -> None:
    by_category: dict[str, set[str]] = {}
    for row in rows:
        by_category.setdefault(row["category"], set()).add(row["target_id"])

    required_p0_categories = {
        "public_boundary",
        "schema_status",
        "web_mirror",
        "quote_policy",
        "book_overview",
    }
    actual_p0 = {row["category"] for row in rows if row["priority"] == "P0"}
    missing_p0 = sorted(required_p0_categories - actual_p0)
    if missing_p0:
        add(findings, "error", "manual-review-p0", f"Missing required P0 categories: {missing_p0}")

    chapter_tasks = by_category.get("chapter_card", set())
    if len(chapter_tasks) != 25:
        add(findings, "error", "manual-review-coverage", f"Expected 25 chapter card tasks, got {len(chapter_tasks)}.")

    concept_tasks = by_category.get("key_concept", set())
    if len(concept_tasks) != 5:
        add(findings, "error", "manual-review-coverage", f"Expected 5 concept tasks, got {len(concept_tasks)}.")

    question_tasks = by_category.get("reading_question", set())
    if len(question_tasks) != 26:
        add(findings, "error", "manual-review-coverage", f"Expected 26 question tasks, got {len(question_tasks)}.")

    quote_tasks = by_category.get("quote_structural_entry", set())
    if len(quote_tasks) != 25:
        add(findings, "error", "manual-review-coverage", f"Expected 25 quote structural entry tasks, got {len(quote_tasks)}.")

    sample_tasks = [row for row in rows if row["priority"] == "P0" and row["category"] == "chapter_card_sample"]
    if len(sample_tasks) < 5:
        add(findings, "error", "manual-review-p0", f"Expected at least 5 P0 chapter card sample tasks, got {len(sample_tasks)}.")


def render_report(project: str, version: str, rows: list[dict[str, str]], summary: dict[str, Any], findings: list[Finding]) -> str:
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    status = "PASS" if not errors else "FAIL"
    priority_counts = Counter(row["priority"] for row in rows)
    category_counts = Counter(row["category"] for row in rows)

    lines = [
        f"# Manual Review Validation {version}",
        "",
        f"- Project: `{project}`",
        f"- Status: `{status}`",
        f"- Errors: `{len(errors)}`",
        f"- Warnings: `{len(warnings)}`",
        f"- CSV rows: `{len(rows)}`",
        f"- Summary totalTasks: `{summary.get('totalTasks')}`",
        "",
        "## Priority Counts",
        "",
        "| priority | count |",
        "|---|---:|",
    ]
    for priority, count in sorted(priority_counts.items()):
        lines.append(f"| `{priority}` | {count} |")

    lines.extend(["", "## Category Counts", "", "| category | count |", "|---|---:|"])
    for category, count in sorted(category_counts.items()):
        lines.append(f"| `{category}` | {count} |")

    if findings:
        lines.extend(["", "## Findings", "", "| severity | path | message |", "|---|---|---|"])
        for finding in findings:
            lines.append(f"| `{finding.severity}` | `{finding.path}` | {finding.message.replace('|', ' ')} |")
    else:
        lines.extend(["", "## Findings", "", "No findings."])

    lines.append("")
    return "\n".join(lines)


def check(project: str, version: str) -> tuple[list[Finding], dict[str, Any]]:
    paths = from_project(project)
    normalized = normalize_version(version)
    csv_path = paths.report_path(f"manual_review_tasks_{normalized}.csv")
    summary_path = paths.report_path(f"manual_review_summary_{normalized}.json")
    dashboard_path = paths.report_path(f"manual_review_dashboard_{normalized}.md")
    validation_path = paths.report_path(f"manual_review_validation_{normalized}.md")

    findings: list[Finding] = []
    rows = read_tasks(csv_path, findings)
    summary = read_json(summary_path, findings)

    if not dashboard_path.exists():
        add(findings, "error", dashboard_path, "Missing manual review dashboard.")

    validate_rows(rows, findings, csv_path)
    validate_summary(rows, summary, findings, summary_path)
    validate_coverage(rows, findings)

    for path in [csv_path, summary_path, dashboard_path]:
        scan_forbidden(path, findings)

    validation_path.write_text(render_report(paths.slug, version, rows, summary, findings), encoding="utf-8")

    return findings, {"rows": rows, "summary": summary, "validation_path": str(validation_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    findings, result = check(args.project, args.version)
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    print("PASS" if not errors else "FAIL")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Rows: {len(result['rows'])}")
    print(f"Report: {result['validation_path']}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
