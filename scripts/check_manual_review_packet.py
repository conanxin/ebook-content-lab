#!/usr/bin/env python3
"""Validate manual review packets and decision template."""

from __future__ import annotations

import argparse
import csv
import json
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


def read_tasks(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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


def render_report(project: str, version: str, details: dict[str, int | bool], findings: list[Finding]) -> str:
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    status = "PASS" if not errors else "FAIL"
    lines = [
        f"# Manual Review Packet Validation {version}",
        "",
        f"- Project: `{project}`",
        f"- Status: `{status}`",
        f"- Errors: `{len(errors)}`",
        f"- Warnings: `{len(warnings)}`",
        f"- P0 packet tasks: `{details['p0PacketTasks']}`",
        f"- all packet tasks: `{details['allPacketTasks']}`",
        f"- decisions template rows: `{details['templateRows']}`",
        f"- templateManualResultsBlank: `{str(details['templateManualResultsBlank']).lower()}`",
        f"- a4CsvManualResultsBlank: `{str(details['a4CsvManualResultsBlank']).lower()}`",
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


def check(project: str, version: str) -> tuple[list[Finding], dict[str, int | bool | str]]:
    paths = from_project(project)
    normalized = normalize_version(version)
    a4_csv = paths.report_path("manual_review_tasks_v0.7_a4.csv")
    p0_path = paths.report_path(f"manual_review_packet_p0_{normalized}.md")
    all_path = paths.report_path(f"manual_review_packet_all_{normalized}.md")
    template_path = paths.report_path(f"manual_review_decisions_template_{normalized}.csv")
    validation_path = paths.report_path(f"manual_review_packet_validation_{normalized}.md")

    findings: list[Finding] = []
    a4_rows = read_tasks(a4_csv)
    template_rows = read_tasks(template_path) if template_path.exists() else []
    a4_ids = [row["task_id"] for row in a4_rows]
    template_ids = [row.get("task_id", "") for row in template_rows]

    for path in [p0_path, all_path, template_path]:
        scan_file(path, findings)

    if len(template_rows) != len(a4_rows):
        add(findings, "error", template_path, f"Template rows {len(template_rows)} do not match A4 rows {len(a4_rows)}.")
    if template_ids != a4_ids:
        add(findings, "error", template_path, "Template task_id order does not match A4 CSV.")

    template_blank = all(not row.get("manual_result", "").strip() for row in template_rows)
    if not template_blank:
        add(findings, "error", template_path, "Template manual_result values must all be blank.")

    a4_blank = all(not row.get("manual_result", "").strip() for row in a4_rows)
    if not a4_blank:
        add(findings, "error", a4_csv, "A4 CSV manual_result values must remain blank in A7.")

    p0_text = p0_path.read_text(encoding="utf-8", errors="replace") if p0_path.exists() else ""
    all_text = all_path.read_text(encoding="utf-8", errors="replace") if all_path.exists() else ""
    p0_ids = [row["task_id"] for row in a4_rows if row["priority"] == "P0"]
    missing_p0 = [task_id for task_id in p0_ids if task_id not in p0_text]
    if missing_p0:
        add(findings, "error", p0_path, f"P0 packet missing task ids: {missing_p0}")

    missing_all = [task_id for task_id in a4_ids if task_id not in all_text]
    if missing_all:
        add(findings, "error", all_path, f"All packet missing task ids: {missing_all[:10]}")

    public_status = read_json(paths.book_overview_json).get("status")
    web_status = read_json(paths.web_book_overview_json).get("status")
    if public_status != "draft":
        add(findings, "error", paths.book_overview_json, f"Public status must remain draft, got {public_status!r}.")
    if web_status != "draft":
        add(findings, "error", paths.web_book_overview_json, f"Web status must remain draft, got {web_status!r}.")

    details: dict[str, int | bool | str] = {
        "p0PacketTasks": len(p0_ids) - len(missing_p0),
        "allPacketTasks": len(a4_ids) - len(missing_all),
        "templateRows": len(template_rows),
        "templateManualResultsBlank": template_blank,
        "a4CsvManualResultsBlank": a4_blank,
        "validationPath": str(validation_path),
    }
    validation_path.write_text(render_report(paths.slug, version, details, findings), encoding="utf-8")
    return findings, details


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    findings, details = check(args.project, args.version)
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    print("PASS" if not errors else "FAIL")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"P0 packet tasks: {details['p0PacketTasks']}")
    print(f"All packet tasks: {details['allPacketTasks']}")
    print(f"Template rows: {details['templateRows']}")
    print(f"Template results blank: {details['templateManualResultsBlank']}")
    print(f"Report: {details['validationPath']}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
