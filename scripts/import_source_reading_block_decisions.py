#!/usr/bin/env python3
"""Dry-run import for A21 source reading block review decisions.

The default behavior is a dry run. Without --apply this script writes only the
A22 plan, usage guide, and dry-run report; it does not modify public data,
web mirrors, A21 task files, or A21 decision templates.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.lib.project_paths import from_project
except ModuleNotFoundError:
    from lib.project_paths import from_project


ALLOWED_RESULTS = {
    "keep",
    "replace",
    "shorten",
    "expand",
    "move_to_extra",
    "move_to_core",
    "needs_context",
    "rewrite_note",
    "remove",
    "defer",
}

ALLOWED_REPLACEMENT_STRATEGIES = {
    "",
    "use_adjacent_paragraph",
    "use_more_specific_scene",
    "use_route_movement",
    "use_place_description",
    "use_reflection",
    "manual_pick",
    "not_needed",
}

RESULTS_REQUIRING_NOTES = {
    "replace",
    "shorten",
    "expand",
    "needs_context",
    "rewrite_note",
    "remove",
    "defer",
}

REQUIRED_DECISION_FIELDS = {
    "block_task_id",
    "review_result",
    "replacement_strategy",
    "review_notes",
}

FORBIDDEN_MARKERS = [
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


def normalize_version(version: str) -> str:
    return version.lower().replace("-", "_")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.name


def contains_forbidden(value: str) -> list[str]:
    lowered = value.lower()
    return [marker for marker in FORBIDDEN_MARKERS if marker.lower() in lowered]


def validate_decisions(
    decision_fields: list[str],
    decisions: list[dict[str, str]],
    task_rows: list[dict[str, str]],
    allow_overwrite: bool,
) -> tuple[list[str], list[dict[str, str]], int, int, int]:
    blockers: list[str] = []
    usable: list[dict[str, str]] = []

    missing_fields = sorted(REQUIRED_DECISION_FIELDS - set(decision_fields))
    if missing_fields:
        blockers.append(f"missing_decision_fields:{','.join(missing_fields)}")
        return blockers, usable, len(decisions), 0, 0

    task_by_id = {row.get("block_task_id", ""): row for row in task_rows}
    seen: set[str] = set()
    blank_decisions = 0
    invalid_decisions = 0

    for row in decisions:
        task_id = (row.get("block_task_id") or "").strip()
        result = (row.get("review_result") or "").strip()
        strategy = (row.get("replacement_strategy") or "").strip()
        notes = (row.get("review_notes") or "").strip()
        reviewer = (row.get("reviewer") or "").strip()

        if not task_id:
            blockers.append("blank_block_task_id")
            invalid_decisions += 1
            continue
        if task_id in seen:
            blockers.append(f"duplicate_block_task_id:{task_id}")
            invalid_decisions += 1
            continue
        seen.add(task_id)

        if task_id not in task_by_id:
            blockers.append(f"unknown_block_task_id:{task_id}")
            invalid_decisions += 1
            continue

        if not result and not strategy and not notes:
            blank_decisions += 1
            continue
        if not result:
            blockers.append(f"missing_review_result:{task_id}")
            invalid_decisions += 1
            continue

        if result not in ALLOWED_RESULTS:
            blockers.append(f"invalid_review_result:{task_id}")
            invalid_decisions += 1
            continue
        if strategy not in ALLOWED_REPLACEMENT_STRATEGIES:
            blockers.append(f"invalid_replacement_strategy:{task_id}")
            invalid_decisions += 1
            continue
        if result in RESULTS_REQUIRING_NOTES and not notes:
            blockers.append(f"review_notes_required:{task_id}")
            invalid_decisions += 1
            continue
        if result == "replace" and (not strategy or strategy == "not_needed"):
            blockers.append(f"replacement_strategy_required:{task_id}")
            invalid_decisions += 1
            continue
        if result == "keep" and strategy not in {"", "not_needed"}:
            blockers.append(f"keep_strategy_must_be_blank_or_not_needed:{task_id}")
            invalid_decisions += 1
            continue

        existing_result = (task_by_id[task_id].get("review_result") or "").strip()
        if existing_result and not allow_overwrite:
            blockers.append(f"overwrite_blocked:{task_id}")
            invalid_decisions += 1
            continue

        text_to_scan = "\n".join([notes, reviewer, strategy])
        hits = contains_forbidden(text_to_scan)
        if hits:
            blockers.append(f"forbidden_marker:{task_id}")
            invalid_decisions += 1
            continue

        usable.append(row)

    return list(dict.fromkeys(blockers)), usable, blank_decisions, len(usable), invalid_decisions


def render_plan(version: str) -> str:
    return "\n".join(
        [
            f"# {version} Source Reading Block Decisions Import Plan",
            "",
            "## A22 Goal",
            "",
            "Add a safe importer for future human-filled source reading block decisions. Current A21 decisions are blank, so this phase performs a dry-run only.",
            "",
            "## Why Current Run Is Dry-Run Only",
            "",
            "The A21 decisions template has no human results yet. Empty decisions are not treated as `keep`, and no batch approval is inferred.",
            "",
            "## Inputs",
            "",
            "- A21 source reading block decisions template",
            "- A21 source reading block review task CSV",
            "- A21 source reading block review summary JSON",
            "- Public chapter reading cards",
            "",
            "## Outputs",
            "",
            "- `source_reading_block_decisions_import_dry_run_v0.7_a22.md`",
            "- `source_reading_block_decisions_import_validation_v0.7_a22.md`",
            "- `source_reading_block_decisions_import_usage_v0.7_a22.md`",
            "",
            "## Import Safety Mechanisms",
            "",
            "- Default mode is dry-run.",
            "- Empty decisions remain blank and do not count as `keep`.",
            "- Unknown or duplicate task IDs block import.",
            "- Missing required fields block import.",
            "- Apply mode requires an exact confirmation phrase.",
            "",
            "## Allow-Overwrite Protection",
            "",
            "Existing non-empty task results cannot be overwritten unless `--allow-overwrite` is provided.",
            "",
            "## Legal Review Results",
            "",
            "`keep`, `replace`, `shorten`, `expand`, `move_to_extra`, `move_to_core`, `needs_context`, `rewrite_note`, `remove`, `defer`.",
            "",
            "## Legal Replacement Strategies",
            "",
            "Blank, `use_adjacent_paragraph`, `use_more_specific_scene`, `use_route_movement`, `use_place_description`, `use_reflection`, `manual_pick`, `not_needed`.",
            "",
            "## Notes Required",
            "",
            "`replace`, `shorten`, `expand`, `needs_context`, `rewrite_note`, `remove`, and `defer` require `review_notes`.",
            "",
            "## Apply Confirmation Phrase",
            "",
            "`IMPORT SOURCE READING BLOCK DECISIONS INTO second-reading-guide`",
            "",
            "## Relationship To A21 And A20",
            "",
            "A21 creates the human workbench. A20 provides the current reading blocks. A22 only validates and previews future imports.",
            "",
            "## A23 Recommendation",
            "",
            "After humans fill decisions, run this importer in dry-run mode again, then build an apply/rewrite pass for accepted changes.",
            "",
        ]
    )


def render_usage(version: str) -> str:
    return "\n".join(
        [
            f"# Source Reading Block Decisions Import Usage {version}",
            "",
            "## Copy The Template",
            "",
            "Copy the A21 decisions template to a new working file before manual editing. Keep the generated template unchanged as the blank baseline.",
            "",
            "## Fill Review Results",
            "",
            "Use one of: `keep`, `replace`, `shorten`, `expand`, `move_to_extra`, `move_to_core`, `needs_context`, `rewrite_note`, `remove`, `defer`.",
            "",
            "## Fill Replacement Strategy",
            "",
            "Use blank or one of: `use_adjacent_paragraph`, `use_more_specific_scene`, `use_route_movement`, `use_place_description`, `use_reflection`, `manual_pick`, `not_needed`.",
            "",
            "## Notes Required",
            "",
            "`replace`, `shorten`, `expand`, `needs_context`, `rewrite_note`, `remove`, and `defer` must include `review_notes`. For `replace`, choose a replacement strategy other than `not_needed`.",
            "",
            "## Why Empty Is Not Keep",
            "",
            "A blank decision means not reviewed. The importer never treats blank cells as approval.",
            "",
            "## Dry-Run Import",
            "",
            "`python scripts/import_source_reading_block_decisions.py --project projects/second-reading-guide --version v0.7-A22 --decisions-csv <filled-decisions.csv> --dry-run`",
            "",
            "## Apply Import",
            "",
            "Apply mode is for a later phase. It requires `--apply` plus `--confirm-import \"IMPORT SOURCE READING BLOCK DECISIONS INTO second-reading-guide\"`.",
            "",
            "## Checks After Import",
            "",
            "Run the A22 checker, the A21 workbench checker, source reading block checks, public reading-guide checks, promotion dry-run, and web build.",
            "",
            "## Next Phase",
            "",
            "A23 can turn validated decisions into a controlled apply or rewrite workflow.",
            "",
        ]
    )


def render_dry_run_report(
    project: str,
    version: str,
    decisions_csv: str,
    task_csv: str,
    total_rows: int,
    blank_decisions: int,
    usable_decisions: int,
    invalid_decisions: int,
    would_update: int,
    applied: bool,
    allow_overwrite: bool,
    blockers: list[str],
) -> str:
    final_decision = "applied" if applied else ("dry_run_no_updates" if would_update == 0 and invalid_decisions == 0 else "dry_run_blocked_or_pending")
    lines = [
        f"# Source Reading Block Decisions Import Dry Run {version}",
        "",
        f"- Project: `{project}`",
        f"- sourceDecisionsCsv: `{decisions_csv}`",
        f"- sourceTaskCsv: `{task_csv}`",
        f"- totalDecisionRows: `{total_rows}`",
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


def apply_import_result(paths: Any, usable: list[dict[str, str]], version: str) -> Path:
    fields = [
        "block_task_id",
        "review_result",
        "replacement_strategy",
        "review_notes",
        "reviewer",
        "reviewed_at",
        "imported_at",
    ]
    now = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, str]] = []
    for row in usable:
        rows.append(
            {
                "block_task_id": row.get("block_task_id", "").strip(),
                "review_result": row.get("review_result", "").strip(),
                "replacement_strategy": row.get("replacement_strategy", "").strip(),
                "review_notes": row.get("review_notes", "").strip(),
                "reviewer": row.get("reviewer", "").strip(),
                "reviewed_at": row.get("reviewed_at", "").strip(),
                "imported_at": now,
            }
        )
    out_path = paths.report_path(f"source_reading_block_decisions_import_result_{normalize_version(version)}.csv")
    write_csv(out_path, fields, rows)
    return out_path


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
    task_csv = paths.report_path("source_reading_block_review_tasks_v0.7_a21.csv")
    report_path = paths.report_path("source_reading_block_decisions_import_dry_run_v0.7_a22.md")

    task_fields, task_rows = read_csv(task_csv)
    decision_fields, decisions = read_csv(decisions_csv)
    blockers, usable, blank_count, usable_count, invalid_count = validate_decisions(
        decision_fields,
        decisions,
        task_rows,
        args.allow_overwrite,
    )
    would_update = usable_count if not blockers else 0
    applied = False

    if args.apply:
        expected = f"IMPORT SOURCE READING BLOCK DECISIONS INTO {paths.slug}"
        if args.confirm_import != expected:
            blockers.append("missing_exact_import_confirmation")
            would_update = 0
        elif blockers:
            would_update = 0
        else:
            apply_import_result(paths, usable, args.version)
            applied = True
    elif not args.dry_run:
        # Safe default: no explicit mode still behaves as dry-run.
        pass

    paths.report_path("v0.7_a22_source_reading_block_decisions_import_plan.md").write_text(
        render_plan(args.version),
        encoding="utf-8",
    )
    paths.report_path("source_reading_block_decisions_import_usage_v0.7_a22.md").write_text(
        render_usage(args.version),
        encoding="utf-8",
    )
    report_path.write_text(
        render_dry_run_report(
            paths.slug,
            args.version,
            display_path(decisions_csv, paths.repo_root),
            display_path(task_csv, paths.repo_root),
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

    result_counts = Counter((row.get("review_result") or "").strip() for row in decisions)
    print(f"totalDecisionRows: {len(decisions)}")
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
