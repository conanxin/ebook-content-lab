#!/usr/bin/env python3
"""Validate dry-run import of manual review decisions."""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

try:
    from scripts.lib.project_paths import from_project
except ModuleNotFoundError:
    from lib.project_paths import from_project


FORBIDDEN_MARKERS = [
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


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def report_value(text: str, key: str) -> str | None:
    match = re.search(rf"^- {re.escape(key)}:\s+`([^`]*)`", text, re.MULTILINE)
    return match.group(1) if match else None


def scan_file(path: Path, findings: list[Finding]) -> None:
    if not path.exists():
        add(findings, "error", path, "Missing expected file.")
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    lowered = text.lower()
    hits = [marker for marker in FORBIDDEN_MARKERS if marker.lower() in lowered]
    if hits:
        add(findings, "error", path, f"Forbidden marker count: {len(hits)}")
    for idx, line in enumerate(text.splitlines(), start=1):
        if len(line) > 1000:
            add(findings, "error", path, f"Line {idx} is over 1000 characters; review for long excerpt risk.")


def render_report(project: str, version: str, details: dict[str, int | bool | str], findings: list[Finding]) -> str:
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    status = "PASS" if not errors else "FAIL"
    lines = [
        f"# Manual Review Decisions Import Validation {version}",
        "",
        f"- Project: `{project}`",
        f"- Status: `{status}`",
        f"- Errors: `{len(errors)}`",
        f"- Warnings: `{len(warnings)}`",
        f"- decisionsRows: `{details['decisionsRows']}`",
        f"- blankDecisions: `{details['blankDecisions']}`",
        f"- usableDecisions: `{details['usableDecisions']}`",
        f"- wouldUpdate: `{details['wouldUpdate']}`",
        f"- applied: `{details['applied']}`",
        f"- a4BlankManualResults: `{details['a4BlankManualResults']}`",
        "",
        "## Findings",
        "",
    ]
    if findings:
        lines.extend(["| severity | path | message |", "|---|---|---|"])
        for finding in findings:
            lines.append(f"| `{finding.severity}` | `{finding.path}` | {finding.message.replace('|', ' ')} |")
    else:
        lines.append("No findings.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    paths = from_project(args.project)
    normalized = normalize_version(args.version)
    import_report = paths.report_path(f"manual_review_decisions_import_dry_run_{normalized}.md")
    validation_path = paths.report_path(f"manual_review_decisions_import_validation_{normalized}.md")
    template_path = paths.report_path("manual_review_decisions_template_v0.7_a7.csv")
    a4_path = paths.report_path("manual_review_tasks_v0.7_a4.csv")

    findings: list[Finding] = []
    scan_file(import_report, findings)
    scan_file(template_path, findings)

    report_text = import_report.read_text(encoding="utf-8", errors="replace") if import_report.exists() else ""
    template_rows = read_rows(template_path) if template_path.exists() else []
    a4_rows = read_rows(a4_path) if a4_path.exists() else []

    decisions_rows = len(template_rows)
    blank_decisions = sum(1 for row in template_rows if not row.get("manual_result", "").strip())
    a4_blank = sum(1 for row in a4_rows if not row.get("manual_result", "").strip())
    usable = report_value(report_text, "usableDecisions")
    would_update = report_value(report_text, "wouldUpdate")
    applied = report_value(report_text, "applied")
    blank_reported = report_value(report_text, "blankDecisions")

    if decisions_rows != 95:
        add(findings, "error", template_path, f"Expected 95 decisions rows, got {decisions_rows}.")
    if blank_decisions != decisions_rows:
        add(findings, "error", template_path, "Decision template manual_result values must all be blank.")
    if a4_blank != 95:
        add(findings, "error", a4_path, f"A4 CSV should still have 95 blank manual_result values, got {a4_blank}.")
    if usable != "0":
        add(findings, "error", import_report, f"usableDecisions must be 0, got {usable!r}.")
    if would_update != "0":
        add(findings, "error", import_report, f"wouldUpdate must be 0, got {would_update!r}.")
    if applied != "false":
        add(findings, "error", import_report, f"applied must be false, got {applied!r}.")
    if blank_reported is None or int(blank_reported) != blank_decisions:
        add(findings, "error", import_report, f"blankDecisions must be {blank_decisions}, got {blank_reported!r}.")

    public_status = read_json(paths.book_overview_json).get("status")
    web_status = read_json(paths.web_book_overview_json).get("status")
    if public_status != "draft":
        add(findings, "error", paths.book_overview_json, f"Public status must remain draft, got {public_status!r}.")
    if web_status != "draft":
        add(findings, "error", paths.web_book_overview_json, f"Web mirror status must remain draft, got {web_status!r}.")

    details = {
        "decisionsRows": decisions_rows,
        "blankDecisions": blank_decisions,
        "usableDecisions": int(usable or -1),
        "wouldUpdate": int(would_update or -1),
        "applied": applied or "missing",
        "a4BlankManualResults": a4_blank,
    }
    validation_path.write_text(render_report(paths.slug, args.version, details, findings), encoding="utf-8")

    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    print("PASS" if not errors else "FAIL")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"decisionsRows: {decisions_rows}")
    print(f"blankDecisions: {blank_decisions}")
    print(f"usableDecisions: {usable}")
    print(f"wouldUpdate: {would_update}")
    print(f"applied: {applied}")
    print(f"Report: {validation_path}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
