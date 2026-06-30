#!/usr/bin/env python3
"""Report and validate manual review progress."""

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


ALLOWED_RESULTS = {"", "pass", "needs_fix", "blocked", "deferred"}
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


def read_rows(path: Path, findings: list[Finding]) -> list[dict[str, str]]:
    if not path.exists():
        add(findings, "error", path, "Missing manual review CSV.")
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def read_json(path: Path, findings: list[Finding]) -> dict[str, Any]:
    if not path.exists():
        add(findings, "error", path, "Missing summary JSON.")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def scan_forbidden(path: Path, findings: list[Finding]) -> None:
    if not path.exists():
        return
    lowered = path.read_text(encoding="utf-8", errors="replace").lower()
    hits = [marker for marker in FORBIDDEN_MARKERS if marker.lower() in lowered]
    if hits:
        add(findings, "error", path, f"Forbidden marker count: {len(hits)}")


def progress(rows: list[dict[str, str]]) -> dict[str, Any]:
    values = [row.get("manual_result", "").strip() for row in rows]
    counts = Counter(values)
    priority: dict[str, dict[str, int]] = {}
    for label in ["P0", "P1", "P2"]:
        scoped = [row.get("manual_result", "").strip() for row in rows if row.get("priority") == label]
        scoped_counts = Counter(scoped)
        priority[label] = {
            "total": len(scoped),
            "blank": scoped_counts.get("", 0),
            "pass": scoped_counts.get("pass", 0),
            "needs_fix": scoped_counts.get("needs_fix", 0),
            "blocked": scoped_counts.get("blocked", 0),
            "deferred": scoped_counts.get("deferred", 0),
            "invalid": sum(1 for value in scoped if value not in ALLOWED_RESULTS),
        }

    p0_p1 = [row for row in rows if row.get("priority") in {"P0", "P1"}]
    p0_p1_ready = bool(p0_p1) and all(row.get("manual_result", "").strip() == "pass" for row in p0_p1)
    p2_rows = [row for row in rows if row.get("priority") == "P2"]
    p2_ready = all(
        row.get("manual_result", "").strip() == "pass"
        or (row.get("manual_result", "").strip() == "deferred" and row.get("notes", "").strip())
        for row in p2_rows
    )
    invalid_values = [value for value in values if value not in ALLOWED_RESULTS]
    blockers = []
    if counts.get("", 0):
        blockers.append("manual_review_incomplete")
    if invalid_values:
        blockers.append("invalid_manual_result")
    if any(value in {"needs_fix", "blocked"} for value in values):
        blockers.append("manual_review_blocker")
    if not p0_p1_ready:
        blockers.append("p0_p1_not_ready")
    if not p2_ready:
        blockers.append("p2_not_ready")

    readiness = not blockers
    reason = "none" if readiness else ("manual_review_incomplete" if "manual_review_incomplete" in blockers else blockers[0])

    return {
        "totalTasks": len(rows),
        "blankManualResults": counts.get("", 0),
        "pass": counts.get("pass", 0),
        "needsFix": counts.get("needs_fix", 0),
        "blocked": counts.get("blocked", 0),
        "deferred": counts.get("deferred", 0),
        "invalid": len(invalid_values),
        "priorityCompletion": priority,
        "p0p1Blockers": [row["task_id"] for row in rows if row.get("priority") in {"P0", "P1"} and row.get("manual_result", "").strip() != "pass"],
        "readinessForPromotion": readiness,
        "reason": reason,
        "blockers": blockers,
    }


def render_progress(project: str, version: str, data: dict[str, Any]) -> str:
    lines = [
        f"# Manual Review Progress {version}",
        "",
        f"- Project: `{project}`",
        f"- totalTasks: `{data['totalTasks']}`",
        f"- blankManualResults: `{data['blankManualResults']}`",
        f"- pass: `{data['pass']}`",
        f"- needsFix: `{data['needsFix']}`",
        f"- blocked: `{data['blocked']}`",
        f"- deferred: `{data['deferred']}`",
        f"- readinessForPromotion: `{str(data['readinessForPromotion']).lower()}`",
        f"- reason: `{data['reason']}`",
        "",
        "## Priority Completion",
        "",
        "| priority | total | blank | pass | needs_fix | blocked | deferred | invalid |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for priority, counts in data["priorityCompletion"].items():
        lines.append(
            f"| `{priority}` | {counts['total']} | {counts['blank']} | {counts['pass']} | "
            f"{counts['needs_fix']} | {counts['blocked']} | {counts['deferred']} | {counts['invalid']} |"
        )
    lines.extend(["", "## Blockers", ""])
    for blocker in data["blockers"] or ["none"]:
        lines.append(f"- `{blocker}`")
    lines.append("")
    return "\n".join(lines)


def render_validation(project: str, version: str, data: dict[str, Any], findings: list[Finding]) -> str:
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    status = "PASS" if not errors else "FAIL"
    lines = [
        f"# Manual Review Progress Validation {version}",
        "",
        f"- Project: `{project}`",
        f"- Status: `{status}`",
        f"- Errors: `{len(errors)}`",
        f"- Warnings: `{len(warnings)}`",
        f"- totalTasks: `{data['totalTasks']}`",
        f"- blankManualResults: `{data['blankManualResults']}`",
        f"- readinessForPromotion: `{str(data['readinessForPromotion']).lower()}`",
        f"- reason: `{data['reason']}`",
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
    tasks_path = paths.report_path("manual_review_tasks_v0.7_a4.csv")
    summary_path = paths.report_path("manual_review_summary_v0.7_a4.json")
    progress_path = paths.report_path(f"manual_review_progress_{normalized}.md")
    validation_path = paths.report_path(f"manual_review_progress_validation_{normalized}.md")

    findings: list[Finding] = []
    rows = read_rows(tasks_path, findings)
    summary = read_json(summary_path, findings)
    data = progress(rows)

    if summary.get("totalTasks") != len(rows):
        add(findings, "error", summary_path, f"Summary totalTasks does not match CSV rows: {summary.get('totalTasks')} vs {len(rows)}.")
    if data["blankManualResults"] != sum(1 for row in rows if not row.get("manual_result", "").strip()):
        add(findings, "error", tasks_path, "Blank result count mismatch.")
    if data["readinessForPromotion"]:
        add(findings, "error", tasks_path, "Current A6 state should not be ready for promotion.")
    if data["reason"] != "manual_review_incomplete":
        add(findings, "error", tasks_path, f"Expected reason manual_review_incomplete, got {data['reason']}.")
    if any(row.get("manual_result", "").strip() for row in rows):
        add(findings, "error", tasks_path, "A6 should not contain real manual_result updates.")

    for path in [tasks_path, summary_path]:
        scan_forbidden(path, findings)

    progress_path.write_text(render_progress(paths.slug, args.version, data), encoding="utf-8")
    validation_path.write_text(render_validation(paths.slug, args.version, data, findings), encoding="utf-8")

    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    print("PASS" if not errors else "FAIL")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"totalTasks: {data['totalTasks']}")
    print(f"blankManualResults: {data['blankManualResults']}")
    print(f"readinessForPromotion: {str(data['readinessForPromotion']).lower()}")
    print(f"reason: {data['reason']}")
    print(f"Progress: {progress_path}")
    print(f"Validation: {validation_path}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
