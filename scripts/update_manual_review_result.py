#!/usr/bin/env python3
"""Safely update one manual review task result.

Default behavior is dry-run. CSV writes require --apply and an exact
confirmation string for the resolved task id.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.lib.project_paths import from_project
except ModuleNotFoundError:
    from lib.project_paths import from_project


BASE_FIELDS = [
    "task_id",
    "priority",
    "category",
    "target_id",
    "target_title",
    "review_question",
    "source_file",
    "manual_result",
    "notes",
]
EXTRA_FIELDS = ["reviewer", "reviewed_at"]
ALLOWED_RESULTS = {"pass", "needs_fix", "blocked", "deferred"}
RESULTS_REQUIRING_NOTES = {"needs_fix", "blocked", "deferred"}
FORBIDDEN_NOTE_MARKERS = [
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


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def resolve_task_id(task_id: str, rows: list[dict[str, str]]) -> str:
    exact = {row["task_id"]: row["task_id"] for row in rows}
    if task_id in exact:
        return task_id

    lowered = {row["task_id"].lower(): row["task_id"] for row in rows}
    if task_id.lower() in lowered:
        return lowered[task_id.lower()]

    # Convenience alias for documentation examples such as P0-001.
    if "-" in task_id:
        prefix, _, ordinal_text = task_id.partition("-")
        if prefix.upper() in {"P0", "P1", "P2"} and ordinal_text.isdigit():
            ordinal = int(ordinal_text)
            priority_rows = [row for row in rows if row.get("priority") == prefix.upper()]
            if 1 <= ordinal <= len(priority_rows):
                return priority_rows[ordinal - 1]["task_id"]

    raise SystemExit(f"Task id not found: {task_id}")


def validate_input(result: str, notes: str) -> None:
    if result not in ALLOWED_RESULTS:
        raise SystemExit(f"Invalid result {result!r}; allowed: {sorted(ALLOWED_RESULTS)}")
    if result in RESULTS_REQUIRING_NOTES and not notes.strip():
        raise SystemExit(f"{result} requires notes.")
    lowered = notes.lower()
    hits = [marker for marker in FORBIDDEN_NOTE_MARKERS if marker.lower() in lowered]
    if hits:
        raise SystemExit(f"Notes contain forbidden marker(s): {hits}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--notes", default="")
    parser.add_argument("--reviewer", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-update", default="")
    parser.add_argument("--input-csv")
    parser.add_argument("--output-csv")
    args = parser.parse_args()

    validate_input(args.result, args.notes)
    paths = from_project(args.project)
    csv_path = Path(args.input_csv) if args.input_csv else paths.report_path("manual_review_tasks_v0.7_a4.csv")
    output_path = Path(args.output_csv) if args.output_csv else csv_path
    fieldnames, rows = read_rows(csv_path)
    resolved_task_id = resolve_task_id(args.task_id, rows)

    row = next(item for item in rows if item["task_id"] == resolved_task_id)
    dry_run = args.dry_run or not args.apply

    if not dry_run:
        expected = f"UPDATE MANUAL REVIEW TASK {resolved_task_id}"
        if args.confirm_update != expected:
            raise SystemExit(f"Missing exact confirmation: {expected}")
        if "reviewer" not in fieldnames:
            fieldnames = [*fieldnames, "reviewer"]
        if "reviewed_at" not in fieldnames:
            fieldnames = [*fieldnames, "reviewed_at"]
        row["manual_result"] = args.result
        row["notes"] = args.notes
        row["reviewer"] = args.reviewer
        row["reviewed_at"] = datetime.now(timezone.utc).isoformat()
        for item in rows:
            for field in fieldnames:
                item.setdefault(field, "")
        write_rows(output_path, fieldnames, rows)

    print(f"mode: {'dry-run' if dry_run else 'apply'}")
    print(f"requestedTaskId: {args.task_id}")
    print(f"resolvedTaskId: {resolved_task_id}")
    print(f"result: {args.result}")
    print(f"reviewer: {args.reviewer}")
    print(f"csvChanged: {str(not dry_run).lower()}")
    print(f"inputCsv: {csv_path}")
    print(f"outputCsv: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
