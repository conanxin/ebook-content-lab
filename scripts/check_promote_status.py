#!/usr/bin/env python3
"""Validate status promotion preflight output."""

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


PUBLIC_FILES = [
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


def add(findings: list[Finding], severity: str, path: str | Path, message: str) -> None:
    findings.append(Finding(severity, str(path), message))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_tasks(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def report_value(text: str, key: str) -> str | None:
    pattern = re.compile(rf"^- {re.escape(key)}:\s+`([^`]*)`", re.MULTILINE)
    match = pattern.search(text)
    return match.group(1) if match else None


def scan_forbidden(path: Path, findings: list[Finding]) -> None:
    if not path.exists():
        return
    lowered = path.read_text(encoding="utf-8", errors="replace").lower()
    hits = [pattern for pattern in FORBIDDEN_PATTERNS if pattern.lower() in lowered]
    if hits:
        add(findings, "error", path, f"Forbidden boundary marker count: {len(hits)}")


def render_report(project: str, version: str, findings: list[Finding], details: dict[str, Any]) -> str:
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    status = "PASS" if not errors else "FAIL"
    lines = [
        f"# Promote Status Validation {version}",
        "",
        f"- Project: `{project}`",
        f"- Status: `{status}`",
        f"- Errors: `{len(errors)}`",
        f"- Warnings: `{len(warnings)}`",
        f"- promotionReady: `{details.get('promotionReady')}`",
        f"- blockingReason: `{details.get('blockingReason')}`",
        f"- blankManualResults: `{details.get('blankManualResults')}`",
        f"- publicStatusStillDraft: `{str(details.get('publicStatusStillDraft')).lower()}`",
        f"- webStatusStillDraft: `{str(details.get('webStatusStillDraft')).lower()}`",
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


def check(project: str, version: str) -> tuple[list[Finding], dict[str, Any]]:
    paths = from_project(project)
    normalized = normalize_version(version)
    preflight_path = paths.report_path(f"promote_status_preflight_{normalized}.md")
    validation_path = paths.report_path(f"promote_status_validation_{normalized}.md")
    tasks_path = paths.report_path("manual_review_tasks_v0.7_a4.csv")

    findings: list[Finding] = []
    if not preflight_path.exists():
        add(findings, "error", preflight_path, "Missing preflight report.")
        preflight_text = ""
    else:
        preflight_text = preflight_path.read_text(encoding="utf-8", errors="replace")

    rows = read_tasks(tasks_path) if tasks_path.exists() else []
    if not rows:
        add(findings, "error", tasks_path, "Missing or empty manual review tasks CSV.")

    blank_count = sum(1 for row in rows if not row.get("manual_result", "").strip())
    promotion_ready = report_value(preflight_text, "promotionReady")
    blocking_reason = report_value(preflight_text, "blockingReason")
    blank_reported = report_value(preflight_text, "blankManualResults")
    applied = report_value(preflight_text, "applied")

    if promotion_ready != "false":
        add(findings, "error", preflight_path, f"promotionReady must be false, got {promotion_ready!r}.")
    if blocking_reason != "manual_review_incomplete":
        add(findings, "error", preflight_path, f"blockingReason must be manual_review_incomplete, got {blocking_reason!r}.")
    if applied != "false":
        add(findings, "error", preflight_path, f"applied must be false, got {applied!r}.")
    if blank_reported is None or int(blank_reported) != blank_count:
        add(findings, "error", preflight_path, f"blankManualResults must be {blank_count}, got {blank_reported!r}.")
    if "manual_review_incomplete" not in preflight_text:
        add(findings, "error", preflight_path, "Preflight report must include manual_review_incomplete blocker.")

    public_status_ok = True
    web_status_ok = True
    for name in PUBLIC_FILES:
        public_path = paths.public_path(name)
        web_path = paths.web_project_path(name)
        public_payload = read_json(public_path)
        web_payload = read_json(web_path)
        if public_payload.get("status") != "draft":
            public_status_ok = False
            add(findings, "error", public_path, f"Public status changed to {public_payload.get('status')!r}.")
        if web_payload.get("status") != "draft":
            web_status_ok = False
            add(findings, "error", web_path, f"Web mirror status changed to {web_payload.get('status')!r}.")
        if public_payload != web_payload:
            add(findings, "error", name, "Public JSON and web mirror differ.")

    scan_forbidden(preflight_path, findings)

    details = {
        "promotionReady": promotion_ready,
        "blockingReason": blocking_reason,
        "blankManualResults": blank_count,
        "publicStatusStillDraft": public_status_ok,
        "webStatusStillDraft": web_status_ok,
    }
    validation_path.write_text(render_report(paths.slug, version, findings, details), encoding="utf-8")
    return findings, details | {"validationPath": str(validation_path)}


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
    print(f"promotionReady: {details.get('promotionReady')}")
    print(f"blockingReason: {details.get('blockingReason')}")
    print(f"blankManualResults: {details.get('blankManualResults')}")
    print(f"Report: {details.get('validationPath')}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
