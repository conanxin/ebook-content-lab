#!/usr/bin/env python3
"""Validate v0.7-A17 immersive reading rhythm optimization."""

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
    if "旅行人信札" not in json.dumps(payloads, ensure_ascii=False):
        add_error(findings, "public data", "Expected title marker 旅行人信札")
    if len(chapters) != 25:
        add_error(findings, "chapters", f"Expected 25, got {len(chapters)}")
    if len(questions) != 26:
        add_error(findings, "questions", f"Expected 26, got {len(questions)}")
    if overview.get("immersive_reading", {}).get("default_mode") != "quick":
        add_error(findings, "book_overview.immersive_reading", "Missing quick default mode")

    source_excerpts_coverage = 0
    core_coverage = 0
    extra_coverage = 0
    reading_flow_coverage = 0
    navigation_coverage = 0
    reading_modes_coverage = 0
    for index, chapter in enumerate(chapters):
        source_excerpts = chapter.get("source_excerpts") or []
        core = chapter.get("core_source_excerpts") or []
        extra = chapter.get("extra_source_excerpts") or []
        if len(source_excerpts) >= 4:
            source_excerpts_coverage += 1
        else:
            add_error(findings, f"chapter[{index}].source_excerpts", f"Expected at least 4, got {len(source_excerpts)}")
        if 1 <= len(core) <= 2:
            core_coverage += 1
        else:
            add_error(findings, f"chapter[{index}].core_source_excerpts", f"Expected 1-2, got {len(core)}")
        if extra:
            extra_coverage += 1
        else:
            add_error(findings, f"chapter[{index}].extra_source_excerpts", "Missing folded extra excerpts")
        flow = chapter.get("reading_flow") or {}
        if flow.get("default_mode") == "quick" and flow.get("available_modes") == ["quick", "deep"]:
            reading_flow_coverage += 1
        else:
            add_error(findings, f"chapter[{index}].reading_flow", "Missing quick/deep reading flow")
        nav = chapter.get("navigation") or {}
        if "previous_letter_id" in nav and "next_letter_id" in nav and nav.get("position_label"):
            navigation_coverage += 1
        else:
            add_error(findings, f"chapter[{index}].navigation", "Missing previous/next navigation")
        modes = chapter.get("reading_modes") or {}
        if modes.get("quick_summary") and modes.get("deep_reading_prompt") and modes.get("mobile_hint"):
            reading_modes_coverage += 1
        else:
            add_error(findings, f"chapter[{index}].reading_modes", "Missing reading mode copy")

    question_mode_coverage = sum(
        1
        for question in questions
        if question.get("quick_answer")
        and question.get("deep_answer")
        and question.get("linked_letter_navigation")
        and question.get("source_anchor")
    )
    if question_mode_coverage != 26:
        add_error(findings, "questions quick/deep", f"Expected 26/26, got {question_mode_coverage}")

    return {
        "chapters": len(chapters),
        "questions": len(questions),
        "source_excerpts_coverage": source_excerpts_coverage,
        "source_excerpts_total": sum(len(chapter.get("source_excerpts") or []) for chapter in chapters),
        "core_source_excerpts_coverage": core_coverage,
        "extra_source_excerpts_coverage": extra_coverage,
        "reading_flow_coverage": reading_flow_coverage,
        "navigation_coverage": navigation_coverage,
        "reading_modes_coverage": reading_modes_coverage,
        "question_quick_deep_coverage": question_mode_coverage,
    }


def check_page(paths, findings: list[Finding]) -> None:
    page = paths.repo_root / "web" / "src" / "pages" / "ReadingGuideProjectPage.tsx"
    styles = paths.repo_root / "web" / "src" / "styles.css"
    page_text = page.read_text(encoding="utf-8", errors="ignore") if page.exists() else ""
    styles_text = styles.read_text(encoding="utf-8", errors="ignore") if styles.exists() else ""
    for marker in ["快速浏览", "精读模式", "上一封", "下一封", "展开精读"]:
        if marker not in page_text:
            add_error(findings, "ReadingGuideProjectPage.tsx", f"Missing visible marker: {marker}")
    for class_name in [
        "reading-mode-toggle",
        "reading-mode-quick",
        "reading-mode-deep",
        "mode-chip",
        "mode-chip-active",
        "letter-navigation",
        "letter-prev-next",
        "letter-nav-button",
        "core-source-excerpts",
        "extra-source-excerpts",
    ]:
        if class_name not in page_text or class_name not in styles_text:
            add_error(findings, class_name, "A17 UI class not wired in page and CSS")
    scan_text(page_text, "ReadingGuideProjectPage.tsx", findings)


def check_manual(paths, findings: list[Finding]) -> dict[str, int]:
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
        f"# Immersive Reading Flow Validation {version}",
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
    manual = check_manual(paths, findings)
    check_page(paths, findings)
    check_git_boundaries(paths, findings)
    report_path = paths.report_path(f"immersive_reading_flow_validation_{normalize_version(args.version)}.md")
    report_path.write_text(render_report(paths.slug, args.version, counts, manual, findings), encoding="utf-8")
    errors = [finding for finding in findings if finding.severity == "error"]
    print("PASS" if not errors else "FAIL")
    print(f"Errors: {len(errors)}")
    print(f"Report: {report_path}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
