#!/usr/bin/env python3
"""Validate v0.7-A14 coordinates, map UI, and mobile polish."""

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


def valid_lat_lng(coords: Any) -> bool:
    if not isinstance(coords, dict):
        return False
    lat = coords.get("lat")
    lng = coords.get("lng")
    return isinstance(lat, (int, float)) and isinstance(lng, (int, float)) and -90 <= lat <= 90 and -180 <= lng <= 180


def check_content(payloads: dict[str, dict[str, Any]], findings: list[Finding]) -> dict[str, int]:
    overview = payloads.get("book_overview.json", {})
    chapters = payloads.get("chapter_reading_cards.json", {}).get("chapters", [])
    questions = payloads.get("reading_questions.json", {}).get("questions", [])
    place_index = overview.get("place_route_index", [])
    route_timeline = overview.get("route_timeline", [])
    place_then_now = overview.get("place_then_now", [])

    if "旅行人信札" not in json.dumps(payloads, ensure_ascii=False):
        add_error(findings, "public data", "Expected title marker 旅行人信札 not found")
    if len(chapters) != 25:
        add_error(findings, "chapters", f"Expected 25, got {len(chapters)}")
    if len(questions) != 26:
        add_error(findings, "questions", f"Expected 26, got {len(questions)}")
    if len(route_timeline) != 25:
        add_error(findings, "route_timeline", f"Expected 25, got {len(route_timeline)}")
    if len(place_index) != 66:
        add_error(findings, "place_route_index", f"Expected 66, got {len(place_index)}")

    public_coordinate = 0
    approximate_coordinate = 0
    needs_coordinate_review = 0
    for index, item in enumerate(place_index):
        status = item.get("coordinate_status")
        if not status:
            add_error(findings, f"place_route_index[{index}].coordinate_status", "Missing coordinate_status")
            continue
        if status == "public_coordinate":
            public_coordinate += 1
        elif status == "approximate_coordinate":
            approximate_coordinate += 1
        elif status == "needs_coordinate_review":
            needs_coordinate_review += 1
        else:
            add_error(findings, f"place_route_index[{index}].coordinate_status", f"Unexpected status: {status!r}")

        if status in {"public_coordinate", "approximate_coordinate"}:
            if not valid_lat_lng(item.get("coordinates")):
                add_error(findings, f"place_route_index[{index}].coordinates", "Missing or invalid lat/lng")
        if status == "needs_coordinate_review" and not item.get("coordinate_review_note"):
            add_error(findings, f"place_route_index[{index}].coordinate_review_note", "Missing review note")

    ready = public_coordinate + approximate_coordinate
    if ready < 35:
        add_warning(findings, "COORDINATE_COVERAGE_LOW", f"Coordinate ready count below target: {ready}")

    public_source = sum(1 for item in place_then_now if item.get("source_status") == "public_source")
    source_needs = sum(1 for item in place_then_now if item.get("source_status") == "needs_source_review")
    if public_source < 45:
        add_error(findings, "public_source", f"Expected at least 45, got {public_source}")
    if source_needs > 21:
        add_error(findings, "needs_source_review", f"Expected no more than 21, got {source_needs}")

    travel_map = overview.get("travel_map", {})
    nodes = travel_map.get("nodes", []) if isinstance(travel_map, dict) else []
    if len(nodes) != 66:
        add_error(findings, "travel_map.nodes", f"Expected 66, got {len(nodes)}")

    return {
        "chapters": len(chapters),
        "questions": len(questions),
        "route_timeline_count": len(route_timeline),
        "place_route_index_count": len(place_index),
        "public_coordinate_count": public_coordinate,
        "approximate_coordinate_count": approximate_coordinate,
        "needs_coordinate_review_count": needs_coordinate_review,
        "coordinate_ready_count": ready,
        "public_source_count": public_source,
        "needs_source_review_count": source_needs,
    }


def check_page(paths, findings: list[Finding]) -> None:
    page = paths.repo_root / "web" / "src" / "pages" / "ReadingGuideProjectPage.tsx"
    styles = paths.repo_root / "web" / "src" / "styles.css"
    page_text = page.read_text(encoding="utf-8", errors="ignore") if page.exists() else ""
    styles_text = styles.read_text(encoding="utf-8", errors="ignore") if styles.exists() else ""
    for marker in ["旅行路线时间线", "地点路线索引", "原文精读", "路线地图", "纸面路线图"]:
        if marker not in page_text:
            add_error(findings, "ReadingGuideProjectPage.tsx", f"Missing visible marker: {marker}")
    for class_name in [
        "travel-map-section",
        "travel-map-canvas",
        "travel-map-node",
        "travel-map-path",
        "travel-map-label",
        "coordinate-badge",
        "coordinate-public",
        "coordinate-approximate",
        "coordinate-pending",
        "mobile-section-toggle",
        "sticky-reading-nav",
        "back-to-top",
        "compact-card-stack",
        "collapsible-reading-panel",
    ]:
        if class_name not in page_text or class_name not in styles_text:
            add_error(findings, class_name, "A14 UI/mobile class not wired in page and CSS")
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
    return {"task_rows": len(task_rows), "task_blank": task_blank, "template_rows": len(template_rows), "template_blank": template_blank}


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
        f"# Map Mobile Polish Validation {version}",
        "",
        f"- Status: `{status}`",
        f"- Errors: `{len(errors)}`",
        f"- Warnings: `{len(warnings)}`",
        f"- Places: `{metrics.get('place_route_index_count', 0)}`",
        f"- Public coordinates: `{metrics.get('public_coordinate_count', 0)}`",
        f"- Approximate coordinates: `{metrics.get('approximate_coordinate_count', 0)}`",
        f"- Needs coordinate review: `{metrics.get('needs_coordinate_review_count', 0)}`",
        f"- Route timeline nodes: `{metrics.get('route_timeline_count', 0)}`",
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

    report_path = paths.report_path(f"map_mobile_polish_validation_{normalize_version(args.version)}.md")
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
