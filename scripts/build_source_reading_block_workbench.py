#!/usr/bin/env python3
"""Build an A21 human review workbench for source reading blocks.

A21 is review-workbench-only. It reads public JSON and writes review
artifacts, but it does not modify public reading-guide data or web mirrors.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.lib.project_paths import from_project
except ModuleNotFoundError:
    from lib.project_paths import from_project


VERSION = "v0.7-A21"

TASK_FIELDS = [
    "block_task_id",
    "letter_id",
    "section_id",
    "chapter_title",
    "block_index",
    "current_placement",
    "block_text",
    "block_length",
    "guide_note",
    "reading_role",
    "source_scope",
    "linked_question_id",
    "review_priority",
    "review_question",
    "suggested_checks",
    "review_result",
    "replacement_strategy",
    "review_notes",
    "reviewer",
    "reviewed_at",
]

DECISION_FIELDS = [
    "block_task_id",
    "letter_id",
    "section_id",
    "chapter_title",
    "block_text",
    "block_length",
    "current_placement",
    "review_result",
    "replacement_strategy",
    "review_notes",
    "reviewer",
    "reviewed_at",
]

LEGAL_REVIEW_RESULTS = [
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
]

LEGAL_REPLACEMENT_STRATEGIES = [
    "use_adjacent_paragraph",
    "use_more_specific_scene",
    "use_route_movement",
    "use_place_description",
    "use_reflection",
    "manual_pick",
    "not_needed",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def block_id(block: dict[str, Any], letter_id: str, index: int) -> str:
    return str(block.get("block_id") or f"{letter_id}-reading-block-{index:02d}")


def question_block_index(questions: dict[str, Any]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = defaultdict(list)
    for question in questions.get("questions", []):
        question_id = str(question.get("question_id", ""))
        anchor = question.get("source_anchor")
        if not question_id or not isinstance(anchor, dict):
            continue
        anchor_block_id = anchor.get("block_id")
        if anchor_block_id:
            index[str(anchor_block_id)].append(question_id)
    return index


def placement_for(block_identifier: str, core_ids: set[str], extra_ids: set[str]) -> str:
    if block_identifier in core_ids:
        return "core"
    if block_identifier in extra_ids:
        return "extra"
    return "source"


def priority_for(placement: str, block_index: int, linked_question_ids: list[str]) -> str:
    if placement == "core" and block_index == 1:
        return "P0"
    if placement == "core" or linked_question_ids:
        return "P1"
    return "P2"


def review_question_for(placement: str, reading_role: str) -> str:
    questions = [
        "Does this block represent the letter strongly enough?",
        "Does it have complete meaning without feeling cut off?",
        "Does it give useful scene, place, route, or travel detail?",
        "Is the guide note specific and helpful?",
    ]
    if placement == "core":
        questions.append("Should it remain a core reading block or move to the extra area?")
    else:
        questions.append("Should it stay in the extra area or move into the core reading flow?")
    if reading_role in {"other", ""}:
        questions.append("Should the reading role be recategorized during human review?")
    return " ".join(questions)


def suggested_checks_for(text: str, placement: str) -> str:
    checks = [
        "representative",
        "complete meaning",
        "no abrupt cut",
        "length fit",
        "guide note usefulness",
    ]
    if len(text) < 90:
        checks.append("possibly short")
    if len(text) > 280:
        checks.append("possibly long")
    if placement == "core":
        checks.append("core placement fit")
    else:
        checks.append("possible core upgrade")
    return "; ".join(checks)


def build_tasks(chapters: dict[str, Any], questions: dict[str, Any]) -> list[dict[str, str]]:
    linked_questions_by_block = question_block_index(questions)
    tasks: list[dict[str, str]] = []

    for chapter in chapters.get("chapters", []):
        letter_id = str(chapter.get("letter_id", ""))
        section_id = str(chapter.get("section_id", ""))
        title = str(chapter.get("title", ""))
        source_blocks = chapter.get("source_reading_blocks") or []
        core_ids = {
            block_id(block, letter_id, index)
            for index, block in enumerate(chapter.get("core_source_reading_blocks") or [], start=1)
        }
        extra_ids = {
            block_id(block, letter_id, index)
            for index, block in enumerate(chapter.get("extra_source_reading_blocks") or [], start=1)
        }
        seen: set[str] = set()

        for index, block in enumerate(source_blocks, start=1):
            identifier = block_id(block, letter_id, index)
            if identifier in seen:
                continue
            seen.add(identifier)
            text = str(block.get("text", ""))
            placement = placement_for(identifier, core_ids, extra_ids)
            linked_question_ids = linked_questions_by_block.get(identifier, [])
            priority = priority_for(placement, index, linked_question_ids)
            task_id = f"block-{letter_id}-{index:03d}"
            reading_role = str(block.get("reading_role", ""))
            tasks.append(
                {
                    "block_task_id": task_id,
                    "letter_id": letter_id,
                    "section_id": section_id,
                    "chapter_title": title,
                    "block_index": str(index),
                    "current_placement": placement,
                    "block_text": text,
                    "block_length": str(len(text)),
                    "guide_note": str(block.get("guide_note", "")),
                    "reading_role": reading_role,
                    "source_scope": str(block.get("source_scope", "")),
                    "linked_question_id": ";".join(linked_question_ids),
                    "review_priority": priority,
                    "review_question": review_question_for(placement, reading_role),
                    "suggested_checks": suggested_checks_for(text, placement),
                    "review_result": "",
                    "replacement_strategy": "",
                    "review_notes": "",
                    "reviewer": "",
                    "reviewed_at": "",
                }
            )
    return tasks


def decision_rows(tasks: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for task in tasks:
        rows.append(
            {
                "block_task_id": task["block_task_id"],
                "letter_id": task["letter_id"],
                "section_id": task["section_id"],
                "chapter_title": task["chapter_title"],
                "block_text": task["block_text"],
                "block_length": task["block_length"],
                "current_placement": task["current_placement"],
                "review_result": "",
                "replacement_strategy": "",
                "review_notes": "",
                "reviewer": "",
                "reviewed_at": "",
            }
        )
    return rows


def render_plan(version: str) -> str:
    return "\n".join(
        [
            f"# {version} Source Reading Block Workbench Plan",
            "",
            "## User Feedback",
            "",
            "A20 added longer source reading blocks. The next step is not automatic rewriting, but a human workbench for judging whether those blocks are representative, complete, and well placed.",
            "",
            "## A21 Goal",
            "",
            "Generate review tasks, a workbench, a decisions template, a summary, validation, and usage guidance for all public source reading blocks.",
            "",
            "## Inputs",
            "",
            "- `projects/second-reading-guide/public/book_overview.json`",
            "- `projects/second-reading-guide/public/chapter_reading_cards.json`",
            "- `projects/second-reading-guide/public/reading_questions.json`",
            "",
            "## Outputs",
            "",
            "- `source_reading_block_workbench_v0.7_a21.md`",
            "- `source_reading_block_review_tasks_v0.7_a21.csv`",
            "- `source_reading_block_decisions_template_v0.7_a21.csv`",
            "- `source_reading_block_review_summary_v0.7_a21.json`",
            "- `source_reading_block_workbench_validation_v0.7_a21.md`",
            "- `source_reading_block_review_usage_v0.7_a21.md`",
            "",
            "## Review Task Fields",
            "",
            "Each task records letter, section, chapter title, block placement, block text, block length, guide note, reading role, linked question, priority, review prompt, suggested checks, and blank decision fields.",
            "",
            "## Legal Review Results",
            "",
            "`keep`, `replace`, `shorten`, `expand`, `move_to_extra`, `move_to_core`, `needs_context`, `rewrite_note`, `remove`, `defer`.",
            "",
            "## Legal Replacement Strategies",
            "",
            "`use_adjacent_paragraph`, `use_more_specific_scene`, `use_route_movement`, `use_place_description`, `use_reflection`, `manual_pick`, `not_needed`.",
            "",
            "## Priority Rules",
            "",
            "- P0: first core source reading block in each letter.",
            "- P1: remaining core blocks and blocks directly linked from reading questions.",
            "- P2: extra source reading blocks.",
            "",
            "## Why This Phase Does Not Change Blocks",
            "",
            "A21 prepares human review decisions. It does not infer that every block is acceptable, and it does not rewrite, delete, or reorder public reading blocks.",
            "",
            "## How To Use The Decisions Template",
            "",
            "Fill the template manually after reading the workbench. Leave uncertain rows blank or mark them as `defer`; use notes for any replacement, shortening, expansion, movement, or context request.",
            "",
            "## A22 Recommendation",
            "",
            "Build a dry-run importer that validates completed block decisions before applying any public JSON changes.",
            "",
        ]
    )


def render_task_block(task: dict[str, str]) -> list[str]:
    return [
        f"#### {task['block_task_id']} / {task['review_priority']} / {task['current_placement']} / {task['block_length']} chars",
        "",
        f"> {task['block_text']}",
        "",
        f"- reading_role: `{task['reading_role']}`",
        f"- source_scope: `{task['source_scope']}`",
        f"- linked_question_id: `{task['linked_question_id'] or 'none'}`",
        f"- guide_note: {task['guide_note']}",
        f"- review_question: {task['review_question']}",
        f"- suggested_checks: {task['suggested_checks']}",
        "",
    ]


def render_workbench(project: str, version: str, tasks: list[dict[str, str]], questions: dict[str, Any]) -> str:
    questions_by_letter: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for question in questions.get("questions", []):
        for letter_id in question.get("linked_letters") or []:
            questions_by_letter[str(letter_id)].append(question)
        if question.get("letter_id"):
            questions_by_letter[str(question["letter_id"])].append(question)

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for task in tasks:
        grouped[task["letter_id"]].append(task)

    lines = [
        f"# Source Reading Block Workbench {version}",
        "",
        f"- Project: `{project}`",
        f"- Total block tasks: `{len(tasks)}`",
        "- Purpose: human refinement only; this workbench does not change public reading blocks.",
        "",
    ]

    def sort_letter(value: str) -> int:
        try:
            return int(value.split("-")[-1])
        except ValueError:
            return 0

    for letter_id in sorted(grouped, key=sort_letter):
        rows = grouped[letter_id]
        first = rows[0]
        core_rows = [row for row in rows if row["current_placement"] == "core"]
        extra_rows = [row for row in rows if row["current_placement"] != "core"]
        lines.extend(
            [
                f"## {first['chapter_title']}",
                "",
                f"- letter_id: `{letter_id}`",
                f"- section_id: `{first['section_id']}`",
                f"- current core blocks: `{len(core_rows)}`",
                f"- current extra blocks: `{len(extra_rows)}`",
                "",
                "### Current core reading blocks",
                "",
            ]
        )
        for task in core_rows:
            lines.extend(render_task_block(task))

        lines.extend(["### Current extra reading blocks", ""])
        for task in extra_rows:
            lines.extend(render_task_block(task))

        linked_questions = questions_by_letter.get(letter_id, [])
        unique_questions = []
        seen_question_ids: set[str] = set()
        for question in linked_questions:
            question_id = str(question.get("question_id", ""))
            if question_id and question_id not in seen_question_ids:
                seen_question_ids.add(question_id)
                unique_questions.append(question)

        lines.extend(["### Reading question relation", ""])
        if unique_questions:
            for question in unique_questions[:3]:
                lines.append(f"- `{question.get('question_id')}`: {question.get('question')}")
        else:
            lines.append("- No question is directly attached to this letter.")

        lines.extend(
            [
                "",
                "### Human refinement focus",
                "",
                "- Confirm the first core block is the best entry point for this letter.",
                "- Check whether any block feels cut off, too long, too short, or weakly representative.",
                "- Mark guide notes that need rewriting instead of changing the original block text.",
                "- Leave decision fields blank until a real human review is performed.",
                "",
            ]
        )
    return "\n".join(lines)


def render_usage(version: str) -> str:
    return "\n".join(
        [
            f"# Source Reading Block Review Usage {version}",
            "",
            "## Open The Workbench",
            "",
            "Start with `source_reading_block_workbench_v0.7_a21.md`. It groups the current public reading blocks by the 25 letters.",
            "",
            "## Fill The Decisions Template",
            "",
            "Use `source_reading_block_decisions_template_v0.7_a21.csv` as the manual working file. Do not edit the generated task CSV unless regenerating A21.",
            "",
            "## Review Result Values",
            "",
            "- `keep`: the block can remain as is.",
            "- `replace`: choose a better block later.",
            "- `shorten`: keep the idea but reduce length.",
            "- `expand`: add context around the block later.",
            "- `move_to_extra`: move a core block into the folded area.",
            "- `move_to_core`: promote an extra block into the default view.",
            "- `needs_context`: keep or replace only after more context is reviewed.",
            "- `rewrite_note`: keep the block but improve the guide note.",
            "- `remove`: remove the block from public display in a later apply phase.",
            "- `defer`: postpone the decision.",
            "",
            "## Replacement Strategy Values",
            "",
            "`use_adjacent_paragraph`, `use_more_specific_scene`, `use_route_movement`, `use_place_description`, `use_reflection`, `manual_pick`, `not_needed`.",
            "",
            "## Notes Required",
            "",
            "Write `review_notes` for `replace`, `shorten`, `expand`, `move_to_extra`, `move_to_core`, `needs_context`, `rewrite_note`, `remove`, or `defer`.",
            "",
            "## Why Not Auto-Keep Everything",
            "",
            "A20 generated useful longer blocks, but only human reading can decide whether each block is representative, complete, and placed correctly.",
            "",
            "## After Filling Decisions",
            "",
            "A22 should add a dry-run importer that checks the completed decisions file, reports would-change counts, and only applies updates with an explicit confirmation phrase.",
            "",
        ]
    )


def build_summary(tasks: list[dict[str, str]], version: str) -> dict[str, Any]:
    placement_counts = Counter(task["current_placement"] for task in tasks)
    priority_counts = Counter(task["review_priority"] for task in tasks)
    letters = {task["letter_id"] for task in tasks}
    return {
        "version": version,
        "status": "review-workbench-only",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "totalBlockTasks": len(tasks),
        "lettersCovered": len(letters),
        "coreBlockTasks": placement_counts.get("core", 0),
        "extraBlockTasks": placement_counts.get("extra", 0),
        "sourceOnlyBlockTasks": placement_counts.get("source", 0),
        "p0Tasks": priority_counts.get("P0", 0),
        "p1Tasks": priority_counts.get("P1", 0),
        "p2Tasks": priority_counts.get("P2", 0),
        "blankReviewResults": sum(1 for task in tasks if not task.get("review_result")),
        "readyForBlockApply": False,
        "allowedReviewResults": LEGAL_REVIEW_RESULTS,
        "allowedReplacementStrategies": LEGAL_REPLACEMENT_STRATEGIES,
    }


def build(project: str, version: str) -> dict[str, Any]:
    paths = from_project(project)
    chapters = read_json(paths.chapter_reading_cards_json)
    questions = read_json(paths.reading_questions_json)
    _overview = read_json(paths.book_overview_json)

    tasks = build_tasks(chapters, questions)
    summary = build_summary(tasks, version)

    paths.report_path("v0.7_a21_source_reading_block_workbench_plan.md").write_text(
        render_plan(version),
        encoding="utf-8",
    )
    paths.report_path("source_reading_block_workbench_v0.7_a21.md").write_text(
        render_workbench(paths.slug, version, tasks, questions),
        encoding="utf-8",
    )
    write_csv(paths.report_path("source_reading_block_review_tasks_v0.7_a21.csv"), tasks, TASK_FIELDS)
    write_csv(paths.report_path("source_reading_block_decisions_template_v0.7_a21.csv"), decision_rows(tasks), DECISION_FIELDS)
    write_json(paths.report_path("source_reading_block_review_summary_v0.7_a21.json"), summary)
    paths.report_path("source_reading_block_review_usage_v0.7_a21.md").write_text(
        render_usage(version),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", default=VERSION)
    args = parser.parse_args()

    summary = build(args.project, args.version)
    print("Source reading block workbench built")
    for key in [
        "totalBlockTasks",
        "lettersCovered",
        "coreBlockTasks",
        "extraBlockTasks",
        "p0Tasks",
        "p1Tasks",
        "p2Tasks",
        "blankReviewResults",
    ]:
        print(f"{key}: {summary[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
