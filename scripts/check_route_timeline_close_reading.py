#!/usr/bin/env python3
"""Validate v0.7-A13 route timeline and close-reading experience."""

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

BANNED_PROMOTED_STATUSES = {"reviewed", "final", "publish-ready", "publish_ready", "reviewed-draft"}
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


def scan_json(data: Any, target: str, findings: list[Finding]) -> None:
    scan_text(json.dumps(data, ensure_ascii=False), target, findings)


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
            if status in BANNED_PROMOTED_STATUSES:
                add_error(findings, f"{name}.{label}.status", f"Disallowed promoted status: {status}")
            if data.get("release_phase") != "public-preview":
                add_error(findings, f"{name}.{label}.release_phase", "Expected public-preview")
            if data.get("review_status") != "manual-review-pending":
                add_error(findings, f"{name}.{label}.review_status", "Expected manual-review-pending")
            scan_json(data, f"{name}.{label}", findings)
    return payloads


def check_content(payloads: dict[str, dict[str, Any]], findings: list[Finding]) -> dict[str, int]:
    overview = payloads.get("book_overview.json", {})
    chapters = payloads.get("chapter_reading_cards.json", {}).get("chapters", [])
    questions = payloads.get("reading_questions.json", {}).get("questions", [])
    places = overview.get("place_then_now", [])
    route_timeline = overview.get("route_timeline", [])
    place_route_index = overview.get("place_route_index", [])

    if "旅行人信札" not in json.dumps(payloads, ensure_ascii=False):
        add_error(findings, "public data", "Expected title marker 旅行人信札 not found")
    if len(chapters) != 25:
        add_error(findings, "chapters", f"Expected 25, got {len(chapters)}")
    if len(questions) != 26:
        add_error(findings, "questions", f"Expected 26, got {len(questions)}")
    if len(route_timeline) != 25:
        add_error(findings, "route_timeline", f"Expected 25 nodes, got {len(route_timeline)}")
    if not place_route_index:
        add_error(findings, "place_route_index", "Missing place route index")

    close_count = sum(1 for chapter in chapters if chapter.get("close_reading"))
    steps_count = sum(1 for chapter in chapters if chapter.get("reading_steps"))
    linked_chapter_count = sum(1 for chapter in chapters if chapter.get("linked_questions"))
    question_link_count = sum(
        1
        for question in questions
        if question.get("linked_letters") or question.get("route_context") or question.get("close_reading_answer")
    )
    public_source_count = sum(1 for item in places if item.get("source_status") == "public_source")
    needs_source_review_count = sum(1 for item in places if item.get("source_status") == "needs_source_review")

    if close_count != 25:
        add_error(findings, "close_reading", f"Expected 25/25, got {close_count}")
    if steps_count != 25:
        add_error(findings, "reading_steps", f"Expected 25/25, got {steps_count}")
    if question_link_count != 26:
        add_error(findings, "reading question linkage", f"Expected 26/26, got {question_link_count}")
    if linked_chapter_count < 25:
        add_error(findings, "chapter linked questions", f"Expected 25 linked chapter cards, got {linked_chapter_count}")
    if public_source_count < 45:
        add_error(findings, "public_source", f"Expected at least A12 count 45, got {public_source_count}")
    if needs_source_review_count > 21:
        add_error(findings, "needs_source_review", f"Expected no more than A12 count 21, got {needs_source_review_count}")

    for index, node in enumerate(route_timeline):
        for field in ["letter_id", "letter_number", "title", "primary_places", "source_status_summary", "linked_question_ids"]:
            if field not in node:
                add_error(findings, f"route_timeline[{index}].{field}", "Missing timeline field")
    for index, chapter in enumerate(chapters):
        close = chapter.get("close_reading") or {}
        for field in ["excerpt_focus", "why_it_matters", "scene_to_notice", "place_to_notice", "then_now_prompt", "question_bridge", "answer_bridge"]:
            if not close.get(field):
                add_error(findings, f"chapter[{index}].close_reading.{field}", "Missing close-reading field")
        if not isinstance(chapter.get("reading_steps"), list) or len(chapter.get("reading_steps") or []) < 3:
            add_error(findings, f"chapter[{index}].reading_steps", "Expected at least 3 reading steps")

    return {
        "chapters": len(chapters),
        "questions": len(questions),
        "route_timeline_count": len(route_timeline),
        "place_route_index_count": len(place_route_index),
        "close_reading_count": close_count,
        "reading_steps_count": steps_count,
        "linked_questions_count": question_link_count,
        "public_source_count": public_source_count,
        "needs_source_review_count": needs_source_review_count,
    }


def check_page(paths, findings: list[Finding]) -> None:
    page = paths.repo_root / "web" / "src" / "pages" / "ReadingGuideProjectPage.tsx"
    styles = paths.repo_root / "web" / "src" / "styles.css"
    page_text = page.read_text(encoding="utf-8", errors="ignore") if page.exists() else ""
    styles_text = styles.read_text(encoding="utf-8", errors="ignore") if styles.exists() else ""

    for marker in ["旅行路线时间线", "地点路线索引", "原文精读", "昔日旅程与今日景点", "原文摘录与阅读线索"]:
        if marker not in page_text:
            add_error(findings, "ReadingGuideProjectPage.tsx", f"Missing visible marker: {marker}")
    for class_name in [
        "reading-guide-nav",
        "section-anchor-list",
        "reading-flow-panel",
        "filter-chip-row",
        "reading-mode-toggle",
        "route-timeline-section",
        "route-timeline",
        "route-timeline-node",
        "route-timeline-marker",
        "route-timeline-places",
        "route-timeline-link",
        "paper-map-section",
        "paper-map-node",
        "paper-map-route",
        "place-route-index",
        "place-route-index-item",
        "close-reading-panel",
        "close-reading-excerpt",
        "close-reading-explanation",
        "close-reading-steps",
        "close-reading-question",
        "close-reading-answer",
    ]:
        if class_name not in page_text or class_name not in styles_text:
            add_error(findings, class_name, "A13 UI class not wired in page and CSS")
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
            add_error(findings, path, "Disallowed changed path")


def render_report(version: str, metrics: dict[str, int], manual: dict[str, int], findings: list[Finding]) -> str:
    errors = [item for item in findings if item.severity == "error"]
    warnings = [item for item in findings if item.severity == "warning"]
    status = "PASS" if not errors else "FAIL"
    lines = [
        f"# Route Timeline Close Reading Validation {version}",
        "",
        f"- Status: `{status}`",
        f"- Errors: `{len(errors)}`",
        f"- Warnings: `{len(warnings)}`",
        f"- Route timeline nodes: `{metrics.get('route_timeline_count', 0)}`",
        f"- Place route index places: `{metrics.get('place_route_index_count', 0)}`",
        f"- Close reading coverage: `{metrics.get('close_reading_count', 0)}`",
        f"- Reading steps coverage: `{metrics.get('reading_steps_count', 0)}`",
        f"- Linked questions coverage: `{metrics.get('linked_questions_count', 0)}`",
        f"- Public-source places: `{metrics.get('public_source_count', 0)}`",
        f"- Needs-source-review places: `{metrics.get('needs_source_review_count', 0)}`",
        f"- Manual-review blank results: `{manual.get('task_blank', 0)}`",
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
    metrics = check_content(payloads, findings)
    check_page(paths, findings)
    manual = check_manual_review(paths, findings)
    check_git_boundaries(paths, findings)

    report_path = paths.report_path(f"route_timeline_close_reading_validation_{normalize_version(args.version)}.md")
    report_path.write_text(render_report(args.version, metrics, manual, findings), encoding="utf-8")

    errors = [item for item in findings if item.severity == "error"]
    warnings = [item for item in findings if item.severity == "warning"]
    print("PASS" if not errors else "FAIL")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Report: {report_path}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
