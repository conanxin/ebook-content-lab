#!/usr/bin/env python3
"""Import human-filled manual review decisions into the authoritative A4 CSV.

Default mode is dry-run. Applying changes requires --apply and an exact
confirmation string.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.lib.project_paths import from_project
except ModuleNotFoundError:
    from lib.project_paths import from_project


REQUIRED_DECISION_FIELDS = {"task_id", "manual_result", "notes", "reviewer"}
ALLOWED_RESULTS = {"pass", "needs_fix", "blocked", "deferred"}
RESULTS_REQUIRING_NOTES = {"needs_fix", "blocked", "deferred"}
FORBIDDEN_MARKERS = [
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


def normalize_version(version: str) -> str:
    return version.lower().replace("-", "_")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def contains_forbidden(value: str) -> list[str]:
    lowered = value.lower()
    return [marker for marker in FORBIDDEN_MARKERS if marker.lower() in lowered]


def display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def validate_decisions(
    decision_fields: list[str],
    decisions: list[dict[str, str]],
    authoritative_rows: list[dict[str, str]],
    allow_overwrite: bool,
) -> tuple[list[str], list[dict[str, str]], int, int, int]:
    blockers: list[str] = []
    usable: list[dict[str, str]] = []

    missing_fields = sorted(REQUIRED_DECISION_FIELDS - set(decision_fields))
    if missing_fields:
        blockers.append(f"missing_decision_fields:{','.join(missing_fields)}")
        return blockers, usable, len(decisions), 0, 0

    authoritative_by_id = {row["task_id"]: row for row in authoritative_rows}
    seen: set[str] = set()
    blank_decisions = 0
    invalid_decisions = 0

    for row in decisions:
        task_id = row.get("task_id", "").strip()
        result = row.get("manual_result", "").strip()
        notes = row.get("notes", "").strip()
        reviewer = row.get("reviewer", "").strip()

        if not task_id:
            blockers.append("blank_task_id")
            invalid_decisions += 1
            continue
        if task_id in seen:
            blockers.append(f"duplicate_task_id:{task_id}")
            invalid_decisions += 1
            continue
        seen.add(task_id)

        if task_id not in authoritative_by_id:
            blockers.append(f"unknown_task_id:{task_id}")
            invalid_decisions += 1
            continue

        if not result:
            blank_decisions += 1
            continue

        if result not in ALLOWED_RESULTS:
            blockers.append(f"invalid_result:{task_id}")
            invalid_decisions += 1
            continue

        if result in RESULTS_REQUIRING_NOTES and not notes:
            blockers.append(f"notes_required:{task_id}")
            invalid_decisions += 1
            continue

        if contains_forbidden(notes) or contains_forbidden(reviewer):
            blockers.append(f"forbidden_marker:{task_id}")
            invalid_decisions += 1
            continue

        existing_result = authoritative_by_id[task_id].get("manual_result", "").strip()
        if existing_result and not allow_overwrite:
            blockers.append(f"overwrite_blocked:{task_id}")
            invalid_decisions += 1
            continue

        usable.append(row)

    return list(dict.fromkeys(blockers)), usable, blank_decisions, len(usable), invalid_decisions


def render_report(
    project: str,
    version: str,
    decisions_csv: Path,
    authoritative_csv: Path,
    total_rows: int,
    blank_decisions: int,
    usable_decisions: int,
    invalid_decisions: int,
    would_update: int,
    applied: bool,
    allow_overwrite: bool,
    blockers: list[str],
) -> str:
    final_decision = "applied" if applied else ("dry_run_no_updates" if would_update == 0 and not blockers else "dry_run_blocked_or_pending")
    lines = [
        f"# Manual Review Decisions Import Dry Run {version}",
        "",
        f"- Project: `{project}`",
        f"- sourceDecisionsCsv: `{decisions_csv.as_posix()}`",
        f"- authoritativeCsv: `{authoritative_csv.as_posix()}`",
        f"- totalDecisionsRows: `{total_rows}`",
        f"- blankDecisions: `{blank_decisions}`",
        f"- usableDecisions: `{usable_decisions}`",
        f"- invalidDecisions: `{invalid_decisions}`",
        f"- wouldUpdate: `{would_update}`",
        f"- applied: `{str(applied).lower()}`",
        f"- overwriteMode: `{str(allow_overwrite).lower()}`",
        f"- finalDecision: `{final_decision}`",
        "",
        "## Blockers",
        "",
    ]
    if blockers:
        for blocker in blockers:
            lines.append(f"- `{blocker}`")
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def apply_decisions(
    authoritative_fields: list[str],
    authoritative_rows: list[dict[str, str]],
    usable_decisions: list[dict[str, str]],
    output_path: Path,
) -> None:
    fields = list(authoritative_fields)
    for field in ["reviewer", "reviewed_at"]:
        if field not in fields:
            fields.append(field)

    by_id = {row["task_id"]: row for row in authoritative_rows}
    now = datetime.now(timezone.utc).isoformat()
    for decision in usable_decisions:
        row = by_id[decision["task_id"]]
        row["manual_result"] = decision["manual_result"].strip()
        row["notes"] = decision.get("notes", "").strip()
        row["reviewer"] = decision.get("reviewer", "").strip()
        row["reviewed_at"] = decision.get("reviewed_at", "").strip() or now

    for row in authoritative_rows:
        for field in fields:
            row.setdefault(field, "")
    write_csv(output_path, fields, authoritative_rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--decisions-csv", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--allow-overwrite", action="store_true")
    parser.add_argument("--confirm-import", default="")
    args = parser.parse_args()

    paths = from_project(args.project)
    decisions_csv = Path(args.decisions_csv)
    authoritative_csv = paths.report_path("manual_review_tasks_v0.7_a4.csv")
    report_path = paths.report_path(f"manual_review_decisions_import_dry_run_{normalize_version(args.version)}.md")
    decisions_display_path = display_path(decisions_csv, paths.repo_root)
    authoritative_display_path = display_path(authoritative_csv, paths.repo_root)

    authoritative_fields, authoritative_rows = read_csv(authoritative_csv)
    decision_fields, decisions = read_csv(decisions_csv)
    blockers, usable, blank_count, usable_count, invalid_count = validate_decisions(
        decision_fields,
        decisions,
        authoritative_rows,
        args.allow_overwrite,
    )
    would_update = usable_count if not blockers else 0
    applied = False

    if args.apply:
        expected = f"IMPORT MANUAL REVIEW DECISIONS INTO {paths.slug}"
        if args.confirm_import != expected:
            blockers.append("missing_exact_import_confirmation")
        elif blockers:
            applied = False
        else:
            apply_decisions(authoritative_fields, authoritative_rows, usable, authoritative_csv)
            applied = True

    report_path.write_text(
        render_report(
            paths.slug,
            args.version,
            Path(decisions_display_path),
            Path(authoritative_display_path),
            len(decisions),
            blank_count,
            usable_count,
            invalid_count,
            would_update,
            applied,
            args.allow_overwrite,
            blockers,
        ),
        encoding="utf-8",
    )

    result_counts = Counter(row.get("manual_result", "").strip() for row in decisions)
    print(f"totalDecisionsRows: {len(decisions)}")
    print(f"blankDecisions: {blank_count}")
    print(f"usableDecisions: {usable_count}")
    print(f"invalidDecisions: {invalid_count}")
    print(f"wouldUpdate: {would_update}")
    print(f"applied: {str(applied).lower()}")
    print(f"resultCounts: {dict(result_counts)}")
    print(f"Report: {report_path}")
    return 1 if args.apply and blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
