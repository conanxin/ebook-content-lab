#!/usr/bin/env python3
"""Validate the reading-guide public preview publishing boundary."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
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

BANNED_STATUSES = {"reviewed", "final", "publish-ready", "publish_ready", "reviewed-draft"}
FORBIDDEN_MARKERS = [
    "private/",
    "private\\",
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
    target: str
    message: str


def normalize_version(version: str) -> str:
    return version.lower().replace("-", "_")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def add_error(findings: list[Finding], target: str, message: str) -> None:
    findings.append(Finding("error", target, message))


def add_warning(findings: list[Finding], target: str, message: str) -> None:
    findings.append(Finding("warning", target, message))


def json_text(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def scan_forbidden(data: Any, target: str, findings: list[Finding]) -> None:
    text = json_text(data)
    lowered = text.lower()
    hits = [marker for marker in FORBIDDEN_MARKERS if marker.lower() in lowered]
    if hits:
        add_error(findings, target, f"Forbidden source markers found: {hits}")

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")
        elif isinstance(value, str) and len(value) > 900:
            add_error(findings, path, f"Long text value found: {len(value)} characters")

    walk(data, target)


def read_manual_review_rows(tasks_csv: Path) -> list[dict[str, str]]:
    with tasks_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def git_changed_paths(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def check_public_files(paths, findings: list[Finding]) -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    for name in PUBLIC_FILES:
        public_path = paths.public_path(name)
        web_path = paths.web_project_path(name)
        if not public_path.exists():
            add_error(findings, name, f"Missing public file: {public_path}")
            continue
        if not web_path.exists():
            add_error(findings, name, f"Missing web mirror file: {web_path}")
            continue
        public_data = load_json(public_path)
        web_data = load_json(web_path)
        payloads[name] = public_data

        if public_data != web_data:
            add_error(findings, name, "Project public JSON and web mirror JSON differ")

        for label, data in [("public", public_data), ("web", web_data)]:
            status = str(data.get("status", "")).lower()
            if status != "draft":
                add_error(findings, f"{name}.{label}.status", f"Expected draft, got {data.get('status')!r}")
            if status in BANNED_STATUSES:
                add_error(findings, f"{name}.{label}.status", f"Disallowed promoted status: {status}")
            if data.get("release_phase") != "public-preview":
                add_error(findings, f"{name}.{label}.release_phase", "Expected public-preview")
            if data.get("visibility") != "public":
                add_error(findings, f"{name}.{label}.visibility", "Expected public")
            if data.get("review_status") != "manual-review-pending":
                add_error(findings, f"{name}.{label}.review_status", "Expected manual-review-pending")
            scan_forbidden(data, f"{name}.{label}", findings)

    return payloads


def check_counts(payloads: dict[str, dict[str, Any]], findings: list[Finding]) -> dict[str, int]:
    counts = {
        "chapters": len(payloads.get("chapter_reading_cards.json", {}).get("chapters", [])),
        "concepts": len(payloads.get("key_concepts.json", {}).get("concepts", [])),
        "quotes": len(payloads.get("quote_index.json", {}).get("quotes", [])),
        "questions": len(payloads.get("reading_questions.json", {}).get("questions", [])),
    }
    expected = {"chapters": 25, "concepts": 5, "quotes": 25, "questions": 26}
    for key, expected_count in expected.items():
        if counts[key] != expected_count:
            add_error(findings, key, f"Expected {expected_count}, got {counts[key]}")
    if payloads.get("quote_index.json", {}).get("quote_mode") != "structural_no_quote":
        add_error(findings, "quote_index.quote_mode", "Expected structural_no_quote")
    return counts


def check_route_and_page(paths, findings: list[Finding]) -> None:
    if not paths.web_index_json.exists():
        add_error(findings, "web index", "Missing web/public/projects/index.json")
    else:
        index = load_json(paths.web_index_json)
        projects = index.get("projects", []) if isinstance(index, dict) else []
        if paths.slug not in {project.get("slug") for project in projects}:
            add_error(findings, "web index", f"{paths.slug} not listed in projects index")

    project_page = paths.repo_root / "web" / "src" / "pages" / "ProjectPage.tsx"
    reading_page = paths.repo_root / "web" / "src" / "pages" / "ReadingGuideProjectPage.tsx"
    if not project_page.exists():
        add_error(findings, "ProjectPage.tsx", "Missing project router page")
    elif "reading-guide" not in project_page.read_text(encoding="utf-8", errors="ignore"):
        add_error(findings, "ProjectPage.tsx", "reading-guide route branch not found")

    if not reading_page.exists():
        add_error(findings, "ReadingGuideProjectPage.tsx", "Missing reading-guide page")
        return

    page_text = reading_page.read_text(encoding="utf-8", errors="ignore")
    for marker in ["Draft", "Public Preview", "Manual review pending"]:
        if marker not in page_text:
            add_error(findings, "ReadingGuideProjectPage.tsx", f"Missing visible marker: {marker}")
    for marker in ["chapters", "concepts", "questions", "structural_no_quote"]:
        if marker not in page_text:
            add_warning(findings, "ReadingGuideProjectPage.tsx", f"Expected data marker not found: {marker}")


def check_manual_review(paths, findings: list[Finding]) -> dict[str, Any]:
    tasks_csv = paths.report_path("manual_review_tasks_v0.7_a4.csv")
    if not tasks_csv.exists():
        add_error(findings, "manual review", "Missing A4 manual review CSV")
        return {"total": 0, "blank": 0, "readinessForPromotion": False}
    rows = read_manual_review_rows(tasks_csv)
    blank = sum(1 for row in rows if not row.get("manual_result", "").strip())
    if len(rows) != 95:
        add_error(findings, "manual review", f"Expected 95 tasks, got {len(rows)}")
    if blank != 95:
        add_error(findings, "manual review", f"Expected 95 blank manual_result values, got {blank}")
    return {"total": len(rows), "blank": blank, "readinessForPromotion": False}


def check_git_boundaries(paths, findings: list[Finding]) -> None:
    changed = git_changed_paths(paths.repo_root)
    disallowed_prefixes = [
        "projects/dadou-shangdu/",
        "web/public/projects/dadou-shangdu/",
        "projects/second-reading-guide/private/",
        "web/node_modules/",
    ]
    disallowed_exact = {
        "web/package-lock.json",
        "projects/second-reading-guide/reports/manual_review_tasks_v0.7_a4.csv",
        "projects/second-reading-guide/reports/manual_review_decisions_template_v0.7_a7.csv",
    }
    for path in changed:
        if path in disallowed_exact or any(path.startswith(prefix) for prefix in disallowed_prefixes):
            add_error(findings, "git boundary", f"Disallowed changed path: {path}")


def render_report(project: str, version: str, counts: dict[str, int], review: dict[str, Any], findings: list[Finding]) -> str:
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    status = "PASS" if not errors else "FAIL"
    lines = [
        f"# Public Preview Publish Validation {version}",
        "",
        f"- Project: `{project}`",
        f"- Status: `{status}`",
        f"- Errors: `{len(errors)}`",
        f"- Warnings: `{len(warnings)}`",
        f"- Public status: `draft`",
        f"- Release phase: `public-preview`",
        f"- Review status: `manual-review-pending`",
        f"- Readiness for promotion: `{str(review.get('readinessForPromotion', False)).lower()}`",
        "",
        "## Counts",
        "",
        f"- Chapter cards: `{counts.get('chapters', 0)}`",
        f"- Key concepts: `{counts.get('concepts', 0)}`",
        f"- Structural quote entries: `{counts.get('quotes', 0)}`",
        f"- Reading questions: `{counts.get('questions', 0)}`",
        f"- Manual review tasks: `{review.get('total', 0)}`",
        f"- Blank manual results: `{review.get('blank', 0)}`",
        "",
        "## Findings",
        "",
    ]
    if findings:
        lines.extend(["| severity | target | message |", "|---|---|---|"])
        for finding in findings:
            lines.append(f"| `{finding.severity}` | `{finding.target}` | {finding.message.replace('|', '｜')} |")
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
    findings: list[Finding] = []

    payloads = check_public_files(paths, findings)
    counts = check_counts(payloads, findings)
    check_route_and_page(paths, findings)
    review = check_manual_review(paths, findings)
    check_git_boundaries(paths, findings)

    report_path = paths.report_path(f"public_preview_publish_validation_{normalize_version(args.version)}.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(paths.slug, args.version, counts, review, findings), encoding="utf-8")

    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    print("PASS" if not errors else "FAIL")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Report: {report_path}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
