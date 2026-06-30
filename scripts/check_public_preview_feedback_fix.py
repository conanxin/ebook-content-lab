#!/usr/bin/env python3
"""Validate the A10 public preview feedback fix for the reading-guide project."""

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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def add_error(findings: list[Finding], target: str, message: str) -> None:
    findings.append(Finding("error", target, message))


def add_warning(findings: list[Finding], target: str, message: str) -> None:
    findings.append(Finding("warning", target, message))


def json_text(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def scan_text(value: str, target: str, findings: list[Finding]) -> None:
    lowered = value.lower()
    hits = [marker for marker in SOURCE_MARKERS if marker.lower() in lowered]
    if hits:
        add_error(findings, target, f"Forbidden source markers found: {hits}")
    if len(value) > 900:
        add_error(findings, target, f"Long text value found: {len(value)} characters")


def scan_json(data: Any, target: str, findings: list[Finding]) -> None:
    lowered = json_text(data).lower()
    hits = [marker for marker in SOURCE_MARKERS if marker.lower() in lowered]
    if hits:
        add_error(findings, target, f"Forbidden source markers found: {hits}")

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")
        elif isinstance(value, str):
            scan_text(value, path, findings)

    walk(data, target)


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


def check_names(paths, findings: list[Finding]) -> None:
    project_paths = [
        paths.project_json,
        paths.web_project_path("project.json"),
        paths.web_index_json,
        paths.book_overview_json,
        paths.web_book_overview_json,
    ]
    for path in project_paths:
        if not path.exists():
            add_error(findings, str(path), "Required metadata file missing")
            continue
        text = path.read_text(encoding="utf-8")
        if "旅行人信札" not in text:
            add_error(findings, str(path), "Expected title marker not found")
        if "待定书名" in text:
            add_error(findings, str(path), "Old placeholder book title still present")

    project_text = paths.project_json.read_text(encoding="utf-8") if paths.project_json.exists() else ""
    web_project_text = paths.web_project_path("project.json").read_text(encoding="utf-8") if paths.web_project_path("project.json").exists() else ""
    index_text = paths.web_index_json.read_text(encoding="utf-8") if paths.web_index_json.exists() else ""
    for label, text in [("project", project_text), ("web project", web_project_text), ("web index", index_text)]:
        if "第二本电子书阅读导读" in text:
            add_error(findings, label, "Old project title still present")


def check_public_data(paths, findings: list[Finding]) -> dict[str, int]:
    payloads: dict[str, dict[str, Any]] = {}
    for name in PUBLIC_FILES:
        public_path = paths.public_path(name)
        web_path = paths.web_project_path(name)
        if not public_path.exists() or not web_path.exists():
            add_error(findings, name, "Public file or web mirror missing")
            continue
        public_data = load_json(public_path)
        web_data = load_json(web_path)
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

    chapters = payloads.get("chapter_reading_cards.json", {}).get("chapters", [])
    questions = payloads.get("reading_questions.json", {}).get("questions", [])
    chapter_enhanced = 0
    for index, chapter in enumerate(chapters):
        has_summary = bool(str(chapter.get("letter_summary") or "").strip())
        has_focus = bool(str(chapter.get("reading_focus") or "").strip())
        has_route = bool(str(chapter.get("route_note") or "").strip())
        if has_summary or has_focus:
            chapter_enhanced += 1
        if not (has_summary and has_focus and has_route):
            add_error(findings, f"chapter[{index}]", "Chapter card missing summary, focus, or route note")

    question_answers = 0
    for index, question in enumerate(questions):
        answer = question.get("answer_hint") or question.get("reference_answer") or question.get("guide_answer")
        if str(answer or "").strip():
            question_answers += 1
        else:
            add_error(findings, f"question[{index}]", "Question missing answer hint")
        basis = str(question.get("basis") or "")
        if "Derived from" in basis:
            add_error(findings, f"question[{index}].basis", "English debug basis text still present")

    if len(chapters) != 25:
        add_error(findings, "chapters", f"Expected 25, got {len(chapters)}")
    if len(questions) != 26:
        add_error(findings, "questions", f"Expected 26, got {len(questions)}")

    return {
        "chapters": len(chapters),
        "chapter_enhanced": chapter_enhanced,
        "questions": len(questions),
        "question_answers": question_answers,
    }


def check_page(paths, findings: list[Finding]) -> None:
    page = paths.repo_root / "web" / "src" / "pages" / "ReadingGuideProjectPage.tsx"
    styles = paths.repo_root / "web" / "src" / "styles.css"
    if not page.exists():
        add_error(findings, "ReadingGuideProjectPage.tsx", "Missing page")
        return
    page_text = page.read_text(encoding="utf-8", errors="ignore")
    styles_text = styles.read_text(encoding="utf-8", errors="ignore") if styles.exists() else ""

    for marker in ["旅行人信札", "Draft", "Public Preview", "Manual review pending", "参考回答"]:
        if marker not in page_text:
            add_error(findings, "ReadingGuideProjectPage.tsx", f"Missing visible marker: {marker}")
    for old in ["待定书名", "第二本电子书阅读导读"]:
        if old in page_text:
            add_error(findings, "ReadingGuideProjectPage.tsx", f"Old text still present: {old}")
    for class_name in [
        "letter-envelope-card",
        "letter-stamp",
        "letter-route",
        "letter-flap",
        "letter-body",
        "letter-answer",
    ]:
        if class_name not in page_text or class_name not in styles_text:
            add_error(findings, class_name, "Envelope UI class not wired in page and CSS")
    lowered = page_text.lower()
    hits = [marker for marker in SOURCE_MARKERS if marker.lower() in lowered]
    if hits:
        add_error(findings, "ReadingGuideProjectPage.tsx", f"Forbidden source markers found: {hits}")


def check_manual_review(paths, findings: list[Finding]) -> dict[str, Any]:
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
        "readinessForPromotion": False,
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
            add_error(findings, "git boundary", f"Disallowed changed path: {path}")


def render_report(project: str, version: str, counts: dict[str, int], review: dict[str, Any], findings: list[Finding]) -> str:
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    status = "PASS" if not errors else "FAIL"
    lines = [
        f"# Public Preview Feedback Fix Validation {version}",
        "",
        f"- Project: `{project}`",
        f"- Status: `{status}`",
        f"- Errors: `{len(errors)}`",
        f"- Warnings: `{len(warnings)}`",
        f"- Chapter cards: `{counts.get('chapters', 0)}`",
        f"- Chapter cards with enhanced guide fields: `{counts.get('chapter_enhanced', 0)}`",
        f"- Reading questions: `{counts.get('questions', 0)}`",
        f"- Reading questions with answer hints: `{counts.get('question_answers', 0)}`",
        f"- Manual review blank results: `{review.get('task_blank', 0)}`",
        f"- Readiness for promotion: `{str(review.get('readinessForPromotion', False)).lower()}`",
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
    check_names(paths, findings)
    counts = check_public_data(paths, findings)
    check_page(paths, findings)
    review = check_manual_review(paths, findings)
    check_git_boundaries(paths, findings)

    report_path = paths.report_path(f"public_preview_feedback_fix_validation_{normalize_version(args.version)}.md")
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
