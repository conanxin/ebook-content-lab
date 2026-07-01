#!/usr/bin/env python3
"""Validate v0.7-A15 letter-first page redesign and content organization."""

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
SOURCE_MARKERS = [
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


@dataclass(frozen=True)
class Finding:
    severity: str
    target: str
    message: str


def normalize_version(version: str) -> str:
    return version.lower().replace("-", "_")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def add_error(findings: list[Finding], target: str, message: str) -> None:
    findings.append(Finding("error", target, message))


def add_warning(findings: list[Finding], target: str, message: str) -> None:
    findings.append(Finding("warning", target, message))


def scan_text(text: str, target: str, findings: list[Finding]) -> None:
    lowered = text.lower()
    hits = [marker for marker in SOURCE_MARKERS if marker.lower() in lowered]
    if hits:
        add_error(findings, target, f"Forbidden source markers found: {hits}")


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
        if not public_path.exists() or not web_path.exists():
            add_error(findings, name, "Public file or web mirror missing")
            continue
        public_data = read_json(public_path)
        web_data = read_json(web_path)
        payloads[name] = public_data
        if public_data != web_data:
            add_error(findings, name, "Project public JSON and web mirror differ")
        for label, data in [("public", public_data), ("web", web_data)]:
            status = str(data.get("status", "")).lower()
            if status != "draft":
                add_error(findings, f"{name}.{label}.status", f"Expected draft, got {data.get('status')!r}")
            if status in BANNED_STATUSES:
                add_error(findings, f"{name}.{label}.status", f"Disallowed promoted status: {status}")
            if data.get("release_phase") != "public-preview":
                add_error(findings, f"{name}.{label}.release_phase", "Expected public-preview")
            if data.get("review_status") != "manual-review-pending":
                add_error(findings, f"{name}.{label}.review_status", "Expected manual-review-pending")
            scan_text(json.dumps(data, ensure_ascii=False), f"{name}.{label}", findings)
    return payloads


def check_content(payloads: dict[str, dict[str, Any]], findings: list[Finding]) -> dict[str, int]:
    overview = payloads.get("book_overview.json", {})
    chapter_data = payloads.get("chapter_reading_cards.json", {})
    question_data = payloads.get("reading_questions.json", {})
    chapters = chapter_data.get("chapters", [])
    questions = question_data.get("questions", [])
    place_index = overview.get("place_route_index", [])
    route_timeline = overview.get("route_timeline", [])
    places = overview.get("place_then_now", [])

    if "旅行人信札" not in json.dumps(payloads, ensure_ascii=False):
        add_error(findings, "public data", "Expected title marker 旅行人信札")
    if len(chapters) != 25:
        add_error(findings, "chapters", f"Expected 25, got {len(chapters)}")
    if len(questions) != 26:
        add_error(findings, "questions", f"Expected 26, got {len(questions)}")
    if len(route_timeline) != 25:
        add_error(findings, "route_timeline", f"Expected 25, got {len(route_timeline)}")
    if len(place_index) != 66:
        add_error(findings, "place_route_index", f"Expected 66, got {len(place_index)}")
    if overview.get("page_redesign", {}).get("mode") != "letter-reading-flow":
        add_error(findings, "book_overview.page_redesign.mode", "Expected letter-reading-flow")

    letter_units = 0
    source_clue_ready = 0
    embedded_places_ready = 0
    question_answer_ready = 0
    close_flow_ready = 0
    for index, chapter in enumerate(chapters):
        unit = chapter.get("letter_reading_unit")
        if not isinstance(unit, dict):
            add_error(findings, f"chapter[{index}].letter_reading_unit", "Missing letter reading unit")
            continue
        letter_units += 1
        if len(unit.get("source_clues") or []) >= 3:
            source_clue_ready += 1
        else:
            add_error(findings, f"chapter[{index}].source_clues", "Expected at least 3 source clues")
        if unit.get("embedded_places"):
            embedded_places_ready += 1
        else:
            add_error(findings, f"chapter[{index}].embedded_places", "Missing embedded places")
        qa = unit.get("question_answer") or {}
        if qa.get("question") and qa.get("reference_answer"):
            question_answer_ready += 1
        else:
            add_error(findings, f"chapter[{index}].question_answer", "Missing visible question answer")
        flow = unit.get("close_reading_flow") or {}
        if flow.get("what_it_says") and flow.get("why_it_matters") and flow.get("reading_steps"):
            close_flow_ready += 1
        else:
            add_error(findings, f"chapter[{index}].close_reading_flow", "Missing close reading flow fields")

    question_answer_count = sum(
        1
        for question in questions
        if question.get("close_reading_answer")
        or question.get("answer_hint_expanded")
        or question.get("answer_hint")
        or question.get("reference_answer")
        or question.get("guide_answer")
    )
    if question_answer_count != 26:
        add_error(findings, "reading question answers", f"Expected 26/26, got {question_answer_count}")

    public_source = sum(1 for item in places if item.get("source_status") == "public_source")
    needs_source_review = sum(1 for item in places if item.get("source_status") == "needs_source_review")
    if public_source < 45:
        add_error(findings, "public_source", f"Expected at least 45, got {public_source}")
    if needs_source_review > 21:
        add_error(findings, "needs_source_review", f"Expected no more than 21, got {needs_source_review}")

    return {
        "chapters": len(chapters),
        "questions": len(questions),
        "letter_units": letter_units,
        "source_clue_ready": source_clue_ready,
        "embedded_places_ready": embedded_places_ready,
        "question_answer_ready": question_answer_ready,
        "close_flow_ready": close_flow_ready,
        "question_answer_count": question_answer_count,
        "place_route_index_count": len(place_index),
        "public_source_count": public_source,
        "needs_source_review_count": needs_source_review,
    }


def check_page(paths, findings: list[Finding]) -> None:
    page = paths.repo_root / "web" / "src" / "pages" / "ReadingGuideProjectPage.tsx"
    styles = paths.repo_root / "web" / "src" / "styles.css"
    page_text = page.read_text(encoding="utf-8", errors="ignore") if page.exists() else ""
    styles_text = styles.read_text(encoding="utf-8", errors="ignore") if styles.exists() else ""
    for marker in [
        "25封书信连续阅读",
        "旅行路线时间线",
        "地点路线索引",
        "原文精读",
        "昔日旅程与今日景点",
        "原文摘录与阅读线索",
        "参考回答",
    ]:
        if marker not in page_text:
            add_error(findings, "ReadingGuideProjectPage.tsx", f"Missing visible marker: {marker}")
    for class_name in [
        "letter-reading-flow",
        "letter-reading-unit",
        "letter-unit-header",
        "letter-info-strip",
        "source-clue-list",
        "source-clue-card",
        "embedded-place-list",
        "embedded-place-card",
        "question-answer-panel",
        "secondary-reading-details",
        "reading-guide-nav",
        "sticky-reading-nav",
        "route-timeline-section",
        "place-route-index",
        "travel-map-section",
        "close-reading-panel",
        "collapsible-reading-panel",
        "back-to-top",
    ]:
        if class_name not in page_text or class_name not in styles_text:
            add_error(findings, class_name, "A15 page class not wired in page and CSS")
    if "@media (max-width" not in styles_text:
        add_error(findings, "styles.css", "Missing mobile media query")
    scan_text(page_text, "ReadingGuideProjectPage.tsx", findings)


def check_manual_review(paths, findings: list[Finding]) -> dict[str, int]:
    tasks = paths.report_path("manual_review_tasks_v0.7_a4.csv")
    template = paths.report_path("manual_review_decisions_template_v0.7_a7.csv")
    task_rows = read_csv(tasks) if tasks.exists() else []
    template_rows = read_csv(template) if template.exists() else []
    task_blank = sum(1 for row in task_rows if not row.get("manual_result", "").strip())
    template_blank = sum(1 for row in template_rows if not row.get("manual_result", "").strip())
    if len(task_rows) != 95 or task_blank != 95:
        add_error(findings, "manual_review_tasks", f"Expected 95 blank results, got rows={len(task_rows)} blank={task_blank}")
    if len(template_rows) != 95 or template_blank != 95:
        add_error(findings, "manual_review_decisions_template", f"Expected 95 blank template results, got rows={len(template_rows)} blank={template_blank}")
    return {
        "task_rows": len(task_rows),
        "task_blank": task_blank,
        "template_rows": len(template_rows),
        "template_blank": template_blank,
    }


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
            add_error(findings, "git boundary", f"Blocked path changed: {path}")


def render_report(project: str, version: str, counts: dict[str, int], manual: dict[str, int], findings: list[Finding]) -> str:
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    lines = [
        f"# Letter Reading Flow Validation {version}",
        "",
        f"- Project: `{project}`",
        f"- Status: `{'PASS' if not errors else 'FAIL'}`",
        f"- Errors: `{len(errors)}`",
        f"- Warnings: `{len(warnings)}`",
        "",
        "## Counts",
        "",
    ]
    for key, value in {**counts, **manual}.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- status must remain `draft`",
            "- release_phase must remain `public-preview`",
            "- review_status must remain `manual-review-pending`",
            "- manual review results remain blank",
            "",
        ]
    )
    if findings:
        lines.extend(["## Findings", "", "| severity | target | message |", "|---|---|---|"])
        for finding in findings:
            lines.append(f"| `{finding.severity}` | `{finding.target}` | {finding.message.replace('|', '｜')} |")
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
    findings: list[Finding] = []
    payloads = check_public_files(paths, findings)
    counts = check_content(payloads, findings)
    manual = check_manual_review(paths, findings)
    check_page(paths, findings)
    check_git_boundaries(paths, findings)

    report_path = paths.report_path(f"letter_reading_flow_validation_{normalize_version(args.version)}.md")
    report_path.write_text(render_report(paths.slug, args.version, counts, manual, findings), encoding="utf-8")
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    print("PASS" if not errors else "FAIL")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Report: {report_path}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
