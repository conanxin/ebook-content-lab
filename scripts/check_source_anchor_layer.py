#!/usr/bin/env python3
"""Validate v0.7-A16 source anchor layer and anchor-first UI order."""

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
    "full_text",
    "raw_text",
    "chapter_text",
]
PROMOTED_STATUSES = {"reviewed", "final", "publish-ready", "publish_ready", "reviewed-draft"}


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


def scan_text(text: str, target: str, findings: list[Finding]) -> None:
    lowered = text.lower()
    hits = [marker for marker in SOURCE_MARKERS if marker.lower() in lowered]
    if hits:
        add_error(findings, target, f"Forbidden source/fulltext markers found: {hits}")


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
            if status in PROMOTED_STATUSES:
                add_error(findings, f"{name}.{label}.status", f"Disallowed promoted status: {status}")
            if data.get("release_phase") != "public-preview":
                add_error(findings, f"{name}.{label}.release_phase", "Expected public-preview")
            if data.get("review_status") != "manual-review-pending":
                add_error(findings, f"{name}.{label}.review_status", "Expected manual-review-pending")
            scan_text(json.dumps(data, ensure_ascii=False), f"{name}.{label}", findings)
    return payloads


def check_content(payloads: dict[str, dict[str, Any]], findings: list[Finding]) -> dict[str, int]:
    overview = payloads.get("book_overview.json", {})
    chapters = payloads.get("chapter_reading_cards.json", {}).get("chapters", [])
    questions = payloads.get("reading_questions.json", {}).get("questions", [])

    if len(chapters) != 25:
        add_error(findings, "chapters", f"Expected 25, got {len(chapters)}")
    if len(questions) != 26:
        add_error(findings, "questions", f"Expected 26, got {len(questions)}")
    if "source_anchor_layer" not in overview:
        add_error(findings, "book_overview.source_anchor_layer", "Missing source anchor layer metadata")

    letters_with_excerpts = 0
    min_excerpts = 99
    total_excerpts = 0
    for index, chapter in enumerate(chapters):
        excerpts = chapter.get("source_excerpts")
        if not isinstance(excerpts, list) or not excerpts:
            add_error(findings, f"chapter[{index}].source_excerpts", "Missing source_excerpts")
            min_excerpts = 0
            continue
        letters_with_excerpts += 1
        min_excerpts = min(min_excerpts, len(excerpts))
        total_excerpts += len(excerpts)
        if len(excerpts) < 2 or len(excerpts) > 4:
            add_error(findings, f"chapter[{index}].source_excerpts", f"Expected 2-4 excerpts, got {len(excerpts)}")
        for excerpt_index, excerpt in enumerate(excerpts):
            if not excerpt.get("text") or not excerpt.get("note"):
                add_error(findings, f"chapter[{index}].source_excerpts[{excerpt_index}]", "Each excerpt needs text and note")
            if len(str(excerpt.get("text", ""))) > 260:
                add_error(findings, f"chapter[{index}].source_excerpts[{excerpt_index}].text", "Excerpt text is too long for anchor layer")
        order = chapter.get("letter_reading_unit", {}).get("reading_order")
        if order != ["source_anchor", "scene", "route", "then_now", "question", "answer"]:
            add_error(findings, f"chapter[{index}].letter_reading_unit.reading_order", f"Unexpected reading order: {order!r}")

    question_anchor_count = sum(1 for question in questions if question.get("source_anchor"))
    if question_anchor_count != 26:
        add_error(findings, "reading_questions.source_anchor", f"Expected 26/26, got {question_anchor_count}")

    return {
        "chapters": len(chapters),
        "questions": len(questions),
        "letters_with_excerpts": letters_with_excerpts,
        "min_excerpts": min_excerpts if min_excerpts != 99 else 0,
        "total_excerpts": total_excerpts,
        "questions_with_source_anchor": question_anchor_count,
    }


def check_page(paths, findings: list[Finding]) -> None:
    page = paths.repo_root / "web" / "src" / "pages" / "ReadingGuideProjectPage.tsx"
    styles = paths.repo_root / "web" / "src" / "styles.css"
    page_text = page.read_text(encoding="utf-8", errors="ignore") if page.exists() else ""
    styles_text = styles.read_text(encoding="utf-8", errors="ignore") if styles.exists() else ""
    for class_name in [
        "source-anchor",
        "source-excerpt-card",
        "source-excerpt-text",
        "source-excerpt-note",
        "scene-explanation-panel",
        "route-structure-panel",
        "then-now-panel",
        "question-answer-panel",
    ]:
        if class_name not in page_text or class_name not in styles_text:
            add_error(findings, class_name, "Source anchor UI class not wired in page and CSS")

    order_markers = [
        "source-anchor",
        "scene-explanation-panel",
        "route-structure-panel",
        "then-now-panel",
        "close-reading-question",
        "close-reading-answer",
    ]
    positions = [page_text.find(marker) for marker in order_markers]
    if any(position == -1 for position in positions):
        add_error(findings, "ReadingGuideProjectPage.tsx", f"Missing order markers: {dict(zip(order_markers, positions))}")
    elif positions != sorted(positions):
        add_error(findings, "ReadingGuideProjectPage.tsx", f"UI order is not anchor-first: {dict(zip(order_markers, positions))}")

    visible_marker_groups = [
        ["原文锚点", "原文选段", "原文摘录"],
        ["场景说明"],
        ["路线结构"],
        ["今昔对照"],
        ["阅读问题"],
        ["参考答案"],
    ]
    for marker_group in visible_marker_groups:
        if not any(marker in page_text for marker in marker_group):
            add_error(findings, "ReadingGuideProjectPage.tsx", f"Missing visible marker group: {marker_group}")
    scan_text(page_text, "ReadingGuideProjectPage.tsx", findings)


def check_manual_review(paths, findings: list[Finding]) -> dict[str, int]:
    rows = read_csv(paths.report_path("manual_review_tasks_v0.7_a4.csv"))
    template_rows = read_csv(paths.report_path("manual_review_decisions_template_v0.7_a7.csv"))
    blank = sum(1 for row in rows if not row.get("manual_result", "").strip())
    template_blank = sum(1 for row in template_rows if not row.get("manual_result", "").strip())
    if len(rows) != 95 or blank != 95:
        add_error(findings, "manual_review_tasks", f"Expected 95 blank results, got rows={len(rows)} blank={blank}")
    if len(template_rows) != 95 or template_blank != 95:
        add_error(findings, "manual_review_decisions_template", f"Expected 95 blank template rows, got rows={len(template_rows)} blank={template_blank}")
    return {"manual_rows": len(rows), "manual_blank": blank, "template_rows": len(template_rows), "template_blank": template_blank}


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
    lines = [
        f"# Source Anchor Validation {version}",
        "",
        f"- Project: `{project}`",
        f"- Status: `{'PASS' if not errors else 'FAIL'}`",
        f"- Errors: `{len(errors)}`",
        "",
        "## Counts",
        "",
    ]
    for key, value in {**counts, **manual}.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Findings", ""])
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
    counts = check_content(payloads, findings)
    manual = check_manual_review(paths, findings)
    check_page(paths, findings)
    check_git_boundaries(paths, findings)
    report_path = paths.report_path(f"source_anchor_validation_{normalize_version(args.version)}.md")
    report_path.write_text(render_report(paths.slug, args.version, counts, manual, findings), encoding="utf-8")
    errors = [finding for finding in findings if finding.severity == "error"]
    print("PASS" if not errors else "FAIL")
    print(f"Errors: {len(errors)}")
    print(f"Report: {report_path}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
