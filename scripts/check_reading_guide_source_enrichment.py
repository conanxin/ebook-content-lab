#!/usr/bin/env python3
"""Validate v0.7-A11 source-informed reading-guide enrichment."""

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

FORBIDDEN_MARKERS = [
    "private/",
    "private\\",
    "/mnt/",
    "D:/",
    "D:\\",
    "book.md",
    "book_sections",
    "book_chunks",
]

PROMOTED_STATUSES = {"reviewed", "final", "publish-ready", "publish_ready", "reviewed-draft"}


@dataclass(frozen=True)
class Finding:
    severity: str
    target: str
    message: str


def normalize_version(version: str) -> str:
    return version.lower().replace("-", "_")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def add_error(findings: list[Finding], target: str, message: str) -> None:
    findings.append(Finding("error", target, message))


def add_warning(findings: list[Finding], target: str, message: str) -> None:
    findings.append(Finding("warning", target, message))


def scan_value(value: str, target: str, findings: list[Finding]) -> None:
    lowered = value.lower()
    hits = [marker for marker in FORBIDDEN_MARKERS if marker.lower() in lowered]
    if hits:
        add_error(findings, target, f"Forbidden source marker found: {hits}")


def scan_json(data: Any, target: str, findings: list[Finding]) -> None:
    scan_value(json.dumps(data, ensure_ascii=False), target, findings)


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


def check_public_payloads(paths, findings: list[Finding]) -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    for name in PUBLIC_FILES:
        public_path = paths.public_path(name)
        web_path = paths.web_project_path(name)
        if not public_path.exists() or not web_path.exists():
            add_error(findings, name, "Public JSON or web mirror missing")
            continue
        public_data = load_json(public_path)
        web_data = load_json(web_path)
        payloads[name] = public_data
        if public_data != web_data:
            add_error(findings, name, "Public JSON and web mirror differ")
        for label, data in [("public", public_data), ("web", web_data)]:
            if data.get("status") != "draft":
                add_error(findings, f"{name}.{label}.status", f"Expected draft, got {data.get('status')!r}")
            if str(data.get("status", "")).lower() in PROMOTED_STATUSES:
                add_error(findings, f"{name}.{label}.status", "Promoted status is not allowed in A11")
            if data.get("release_phase") != "public-preview":
                add_error(findings, f"{name}.{label}.release_phase", "Expected public-preview")
            if data.get("review_status") != "manual-review-pending":
                add_error(findings, f"{name}.{label}.review_status", "Expected manual-review-pending")
            if "旅行人信札" not in json.dumps(data, ensure_ascii=False):
                add_error(findings, f"{name}.{label}", "Title marker missing")
            if "待定书名" in json.dumps(data, ensure_ascii=False) or "第二本电子书阅读导读" in json.dumps(data, ensure_ascii=False):
                add_error(findings, f"{name}.{label}", "Old placeholder naming still present")
            scan_json(data, f"{name}.{label}", findings)
    return payloads


def check_chapters(payloads: dict[str, dict[str, Any]], findings: list[Finding]) -> dict[str, int]:
    chapters = payloads.get("chapter_reading_cards.json", {}).get("chapters", [])
    counts = {
        "chapters": len(chapters),
        "source_summaries": 0,
        "excerpts": 0,
        "scene_notes": 0,
        "then_now": 0,
        "needs_source_review_chapters": 0,
    }
    if len(chapters) != 25:
        add_error(findings, "chapters", f"Expected 25 chapters, got {len(chapters)}")
    for index, chapter in enumerate(chapters):
        if chapter.get("source_informed_summary"):
            counts["source_summaries"] += 1
        else:
            add_error(findings, f"chapter[{index}]", "Missing source-informed summary")
        if chapter.get("original_excerpt"):
            counts["excerpts"] += 1
        else:
            add_error(findings, f"chapter[{index}]", "Missing original excerpt or source clue")
        if chapter.get("original_scene_notes"):
            counts["scene_notes"] += 1
        else:
            add_error(findings, f"chapter[{index}]", "Missing original scene notes")
        route_now = chapter.get("route_now") or []
        if chapter.get("route_then") and chapter.get("then_now_comparison") and route_now:
            counts["then_now"] += 1
        else:
            add_error(findings, f"chapter[{index}]", "Missing then/now comparison")
        if chapter.get("needs_source_review") or any(item.get("source_status") == "needs_source_review" for item in route_now):
            counts["needs_source_review_chapters"] += 1
    return counts


def check_questions(payloads: dict[str, dict[str, Any]], findings: list[Finding]) -> dict[str, int]:
    questions = payloads.get("reading_questions.json", {}).get("questions", [])
    counts = {"questions": len(questions), "enhanced_answers": 0}
    if len(questions) != 26:
        add_error(findings, "questions", f"Expected 26 questions, got {len(questions)}")
    for index, question in enumerate(questions):
        if question.get("answer_hint_expanded") or question.get("answer_hint"):
            counts["enhanced_answers"] += 1
        else:
            add_error(findings, f"question[{index}]", "Missing enhanced answer")
        basis = str(question.get("basis") or "")
        if "Derived from" in basis:
            add_error(findings, f"question[{index}].basis", "English debug basis still present")
    return counts


def check_overview(payloads: dict[str, dict[str, Any]], findings: list[Finding]) -> dict[str, int]:
    overview = payloads.get("book_overview.json", {})
    place_rows = overview.get("place_then_now") or []
    source_covered = sum(1 for row in place_rows if row.get("source_status") == "public_source")
    needs_review = sum(1 for row in place_rows if row.get("source_status") == "needs_source_review")
    if not place_rows:
        add_error(findings, "book_overview.place_then_now", "Missing place then/now data")
    return {"source_covered_places": source_covered, "needs_source_review_places": needs_review}


def check_page(paths, findings: list[Finding]) -> None:
    page = paths.repo_root / "web" / "src" / "pages" / "ReadingGuideProjectPage.tsx"
    if not page.exists():
        add_error(findings, "ReadingGuideProjectPage.tsx", "Missing page")
        return
    text = page.read_text(encoding="utf-8", errors="ignore")
    for marker in ["昔日旅程与今日景点", "原文摘录与阅读线索", "旅行人信札"]:
        if marker not in text:
            add_error(findings, "ReadingGuideProjectPage.tsx", f"Missing visible section marker: {marker}")
    for marker in ["待定书名", "第二本电子书阅读导读"]:
        if marker in text:
            add_error(findings, "ReadingGuideProjectPage.tsx", f"Old naming still present: {marker}")
    scan_value(text, "ReadingGuideProjectPage.tsx", findings)


def check_manual_review(paths, findings: list[Finding]) -> dict[str, int]:
    task_rows = read_csv(paths.report_path("manual_review_tasks_v0.7_a4.csv"))
    template_rows = read_csv(paths.report_path("manual_review_decisions_template_v0.7_a7.csv"))
    task_blank = sum(1 for row in task_rows if not row.get("manual_result", "").strip())
    template_blank = sum(1 for row in template_rows if not row.get("manual_result", "").strip())
    if len(task_rows) != 95 or task_blank != 95:
        add_error(findings, "manual_review_tasks", f"Expected 95 blank results, got rows={len(task_rows)} blank={task_blank}")
    if len(template_rows) != 95 or template_blank != 95:
        add_error(findings, "manual_review_decisions_template", f"Expected 95 blank template results, got rows={len(template_rows)} blank={template_blank}")
    return {"manual_rows": len(task_rows), "manual_blank": task_blank}


def check_git_boundaries(paths, findings: list[Finding]) -> None:
    changed = git_changed_paths(paths.repo_root)
    blocked_prefixes = [
        "projects/second-reading-guide/private/",
        "projects/dadou-shangdu/",
        "web/public/projects/dadou-shangdu/",
        "web/node_modules/",
    ]
    blocked_exact = {
        "web/package-lock.json",
        "projects/second-reading-guide/reports/manual_review_tasks_v0.7_a4.csv",
        "projects/second-reading-guide/reports/manual_review_decisions_template_v0.7_a7.csv",
    }
    for path in changed:
        if path in blocked_exact or any(path.startswith(prefix) for prefix in blocked_prefixes):
            add_error(findings, "git boundary", f"Disallowed changed path: {path}")


def render_report(project: str, version: str, counts: dict[str, int], findings: list[Finding]) -> str:
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    status = "PASS" if not errors else "FAIL"
    lines = [
        f"# Source Enrichment Validation {version}",
        "",
        f"- Project: `{project}`",
        f"- Status: `{status}`",
        f"- Errors: `{len(errors)}`",
        f"- Warnings: `{len(warnings)}`",
        f"- Chapter cards: `{counts.get('chapters', 0)}`",
        f"- Source-informed summary coverage: `{counts.get('source_summaries', 0)}`",
        f"- Original excerpt / clue coverage: `{counts.get('excerpts', 0)}`",
        f"- Original scene notes coverage: `{counts.get('scene_notes', 0)}`",
        f"- Then/now comparison coverage: `{counts.get('then_now', 0)}`",
        f"- Reading questions: `{counts.get('questions', 0)}`",
        f"- Enhanced answer coverage: `{counts.get('enhanced_answers', 0)}`",
        f"- Places with public source coverage: `{counts.get('source_covered_places', 0)}`",
        f"- Places needing source review: `{counts.get('needs_source_review_places', 0)}`",
        f"- Manual review blank results: `{counts.get('manual_blank', 0)}`",
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
    payloads = check_public_payloads(paths, findings)
    counts: dict[str, int] = {}
    counts.update(check_chapters(payloads, findings))
    counts.update(check_questions(payloads, findings))
    counts.update(check_overview(payloads, findings))
    counts.update(check_manual_review(paths, findings))
    check_page(paths, findings)
    check_git_boundaries(paths, findings)

    report_path = paths.report_path(f"source_enrichment_validation_{normalize_version(args.version)}.md")
    report_path.write_text(render_report(paths.slug, args.version, counts, findings), encoding="utf-8")
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    print("PASS" if not errors else "FAIL")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Report: {report_path}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
