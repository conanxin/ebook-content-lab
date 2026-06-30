#!/usr/bin/env python3
"""Run a safe status promotion preflight for a reading-guide project.

Default behavior is dry-run. Public JSON and web mirror JSON are changed only
with --apply plus an exact confirmation string, and only if all readiness
checks pass.
"""

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


SCHEMA_VERSION = "reading-guide.v0.2"
CURRENT_STATUS = "draft"
ALLOWED_MANUAL_RESULTS = {"", "pass", "needs_fix", "blocked", "deferred"}
PUBLIC_FILES = [
    "book_overview.json",
    "chapter_reading_cards.json",
    "key_concepts.json",
    "quote_index.json",
    "reading_questions.json",
]
PRIVATE_OR_BODY_MARKERS = [
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


@dataclass
class Preflight:
    project: str
    version: str
    current_status: str | None
    target_status: str
    mode: str
    promotion_ready: bool
    applied: bool
    manual_review_total_tasks: int
    blank_manual_results: int
    priority_readiness: dict[str, dict[str, int]]
    blockers: list[str]
    public_web_mirror_consistent: bool
    boundary_ok: bool


def normalize_version(version: str) -> str:
    return version.lower().replace("-", "_")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_manual_tasks(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def scan_text_file(path: Path) -> list[str]:
    if not path.exists():
        return []
    lowered = path.read_text(encoding="utf-8", errors="replace").lower()
    return [marker for marker in PRIVATE_OR_BODY_MARKERS if marker.lower() in lowered]


def public_paths(paths: Any) -> list[Path]:
    return [paths.public_path(name) for name in PUBLIC_FILES]


def web_paths(paths: Any) -> list[Path]:
    return [paths.web_project_path(name) for name in PUBLIC_FILES]


def display_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def summarize_priority(rows: list[dict[str, str]]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for priority in ["P0", "P1", "P2"]:
        values = [row.get("manual_result", "").strip() for row in rows if row.get("priority") == priority]
        counts = Counter(values)
        result[priority] = {
            "total": len(values),
            "blank": counts.get("", 0),
            "pass": counts.get("pass", 0),
            "needs_fix": counts.get("needs_fix", 0),
            "blocked": counts.get("blocked", 0),
            "deferred": counts.get("deferred", 0),
            "invalid": sum(1 for value in values if value not in ALLOWED_MANUAL_RESULTS),
        }
    return result


def evaluate(project: str, version: str, target_status: str) -> tuple[Any, Preflight, list[dict[str, Any]]]:
    paths = from_project(project)
    normalized = normalize_version("v0.7-A4")
    tasks_path = paths.report_path(f"manual_review_tasks_{normalized}.csv")
    summary_path = paths.report_path(f"manual_review_summary_{normalized}.json")

    blockers: list[str] = []
    files: list[dict[str, Any]] = []

    public_payloads: dict[str, dict[str, Any]] = {}
    web_payloads: dict[str, dict[str, Any]] = {}
    for name in PUBLIC_FILES:
        public_path = paths.public_path(name)
        web_path = paths.web_project_path(name)
        if not public_path.exists():
            blockers.append(f"missing_public_file:{name}")
            continue
        if not web_path.exists():
            blockers.append(f"missing_web_mirror_file:{name}")
            continue
        public_payloads[name] = read_json(public_path)
        web_payloads[name] = read_json(web_path)

    current_status = public_payloads.get("book_overview.json", {}).get("status")
    if current_status != CURRENT_STATUS:
        blockers.append("current_status_not_draft")

    for name, payload in public_payloads.items():
        if payload.get("schema_version") != SCHEMA_VERSION:
            blockers.append(f"schema_version_mismatch:{name}")
        if payload.get("status") != CURRENT_STATUS:
            blockers.append(f"public_status_not_draft:{name}")

    public_web_mirror_consistent = True
    for name, payload in public_payloads.items():
        mirror = web_payloads.get(name)
        if mirror != payload:
            public_web_mirror_consistent = False
            blockers.append(f"web_mirror_mismatch:{name}")
        if mirror and mirror.get("status") != CURRENT_STATUS:
            blockers.append(f"web_status_not_draft:{name}")

    if not tasks_path.exists():
        blockers.append("missing_manual_review_csv")
        rows: list[dict[str, str]] = []
    else:
        rows = read_manual_tasks(tasks_path)

    if not summary_path.exists():
        blockers.append("missing_manual_review_summary")
        summary: dict[str, Any] = {}
    else:
        summary = read_json(summary_path)

    if summary.get("totalTasks") != len(rows):
        blockers.append("manual_review_summary_mismatch")

    priority_readiness = summarize_priority(rows)
    blank_manual_results = sum(1 for row in rows if not row.get("manual_result", "").strip())

    p0_p1 = [row for row in rows if row.get("priority") in {"P0", "P1"}]
    if any(not row.get("manual_result", "").strip() for row in p0_p1):
        blockers.append("manual_review_incomplete")
    if any(row.get("manual_result", "").strip() != "pass" for row in p0_p1):
        blockers.append("p0_p1_not_all_pass")

    p2 = [row for row in rows if row.get("priority") == "P2"]
    for row in p2:
        value = row.get("manual_result", "").strip()
        if value not in {"pass", "deferred"}:
            blockers.append("p2_not_pass_or_deferred")
            break
        if value == "deferred" and not row.get("notes", "").strip():
            blockers.append("p2_deferred_without_notes")
            break

    for row in rows:
        value = row.get("manual_result", "").strip()
        if value not in ALLOWED_MANUAL_RESULTS:
            blockers.append("illegal_manual_result")
            break
        if value in {"needs_fix", "blocked"}:
            blockers.append(f"manual_review_{value}")
            break

    boundary_ok = True
    scan_targets = public_paths(paths) + web_paths(paths) + [tasks_path, summary_path]
    for path in scan_targets:
        hits = scan_text_file(path)
        files.append({"path": display_path(path, paths.repo_root), "forbidden_hits": hits})
        if hits:
            boundary_ok = False
            blockers.append(f"boundary_marker_found:{path.name}")

    unique_blockers = list(dict.fromkeys(blockers))
    promotion_ready = not unique_blockers
    preflight = Preflight(
        project=paths.slug,
        version=version,
        current_status=current_status,
        target_status=target_status,
        mode="dry-run",
        promotion_ready=promotion_ready,
        applied=False,
        manual_review_total_tasks=len(rows),
        blank_manual_results=blank_manual_results,
        priority_readiness=priority_readiness,
        blockers=unique_blockers,
        public_web_mirror_consistent=public_web_mirror_consistent,
        boundary_ok=boundary_ok,
    )
    return paths, preflight, files


def render_report(preflight: Preflight, files: list[dict[str, Any]]) -> str:
    blocking_reason = "none"
    if "manual_review_incomplete" in preflight.blockers:
        blocking_reason = "manual_review_incomplete"
    elif preflight.blockers:
        blocking_reason = preflight.blockers[0]

    lines = [
        "# Promote Status Preflight v0.7-A5",
        "",
        f"- Project: `{preflight.project}`",
        f"- Current status: `{preflight.current_status}`",
        f"- Target status: `{preflight.target_status}`",
        f"- Mode: `{preflight.mode}`",
        f"- promotionReady: `{str(preflight.promotion_ready).lower()}`",
        f"- blockingReason: `{blocking_reason}`",
        f"- applied: `{str(preflight.applied).lower()}`",
        f"- manualReviewTotalTasks: `{preflight.manual_review_total_tasks}`",
        f"- blankManualResults: `{preflight.blank_manual_results}`",
        f"- publicWebMirrorConsistent: `{str(preflight.public_web_mirror_consistent).lower()}`",
        f"- boundaryOk: `{str(preflight.boundary_ok).lower()}`",
        "",
        "## Priority Readiness",
        "",
        "| priority | total | blank | pass | needs_fix | blocked | deferred | invalid |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for priority, counts in preflight.priority_readiness.items():
        lines.append(
            f"| `{priority}` | {counts['total']} | {counts['blank']} | {counts['pass']} | "
            f"{counts['needs_fix']} | {counts['blocked']} | {counts['deferred']} | {counts['invalid']} |"
        )

    lines.extend(["", "## Blockers", ""])
    if preflight.blockers:
        for blocker in preflight.blockers:
            lines.append(f"- `{blocker}`")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Boundary Checks",
            "",
            "| file | forbidden marker count |",
            "|---|---:|",
        ]
    )
    for item in files:
        lines.append(f"| `{item['path']}` | {len(item['forbidden_hits'])} |")

    lines.extend(
        [
            "",
            "## Final Decision",
            "",
            "Promotion is blocked until manual review results are completed and pass the readiness rules.",
            "",
        ]
    )
    return "\n".join(lines)


def apply_status(paths: Any, target_status: str, confirm: str) -> None:
    expected = f"PROMOTE {paths.slug} FROM {CURRENT_STATUS} TO {target_status}"
    if confirm != expected:
        raise SystemExit(f"Missing exact confirmation: {expected}")
    for path in public_paths(paths) + web_paths(paths):
        payload = read_json(path)
        payload["status"] = target_status
        write_json(path, payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--target-status", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-promote", default="")
    args = parser.parse_args()

    paths, preflight, files = evaluate(args.project, args.version, args.target_status)
    normalized = normalize_version(args.version)
    report_path = paths.report_path(f"promote_status_preflight_{normalized}.md")

    if args.apply:
        preflight.mode = "apply"
        if not preflight.promotion_ready:
            preflight.applied = False
        else:
            apply_status(paths, args.target_status, args.confirm_promote)
            preflight.applied = True
    else:
        preflight.mode = "dry-run"
        preflight.applied = False

    report_path.write_text(render_report(preflight, files), encoding="utf-8")

    print(f"promotionReady: {str(preflight.promotion_ready).lower()}")
    print(f"applied: {str(preflight.applied).lower()}")
    print(f"blankManualResults: {preflight.blank_manual_results}")
    print(f"blockers: {preflight.blockers}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
