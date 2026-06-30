#!/usr/bin/env python3
"""Build safe manual review packets for reading-guide tasks."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from scripts.lib.project_paths import from_project
except ModuleNotFoundError:
    from lib.project_paths import from_project


DECISION_FIELDS = [
    "task_id",
    "priority",
    "category",
    "target_id",
    "target_title",
    "manual_result",
    "notes",
    "reviewer",
    "reviewed_at",
]


def normalize_version(version: str) -> str:
    return version.lower().replace("-", "_")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_tasks(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_decision_template(path: Path, tasks: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DECISION_FIELDS)
        writer.writeheader()
        for row in tasks:
            writer.writerow(
                {
                    "task_id": row["task_id"],
                    "priority": row["priority"],
                    "category": row["category"],
                    "target_id": row["target_id"],
                    "target_title": row["target_title"],
                    "manual_result": "",
                    "notes": "",
                    "reviewer": "",
                    "reviewed_at": "",
                }
            )


def public_context(public_data: dict[str, dict[str, Any]], task: dict[str, str]) -> list[str]:
    category = task["category"]
    target_id = task["target_id"]
    lines: list[str] = []

    if category in {"chapter_card", "chapter_card_sample"}:
        chapters = public_data["chapter_reading_cards.json"].get("chapters", [])
        chapter = next((item for item in chapters if item.get("chapter_id") == target_id), None)
        if chapter:
            lines.extend(
                [
                    f"- section_id: `{chapter.get('section_id')}`",
                    f"- order: `{chapter.get('order')}`",
                    f"- places: `{', '.join(chapter.get('places', [])) or 'none'}`",
                    f"- themes: `{', '.join(chapter.get('themes', [])) or 'none'}`",
                    f"- chunk_count: `{chapter.get('chunk_count')}`",
                    f"- review_status: `{chapter.get('review_status')}`",
                ]
            )
    elif category == "key_concept":
        concepts = public_data["key_concepts.json"].get("concepts", [])
        concept = next((item for item in concepts if item.get("concept_id") == target_id), None)
        if concept:
            lines.extend(
                [
                    f"- label: `{concept.get('label')}`",
                    f"- related_letters: `{len(concept.get('related_letters', []))}`",
                    f"- review_status: `{concept.get('review_status')}`",
                ]
            )
    elif category == "quote_structural_entry":
        quotes = public_data["quote_index.json"].get("quotes", [])
        quote = next((item for item in quotes if item.get("quote_id") == target_id), None)
        if quote:
            lines.extend(
                [
                    f"- quote_mode: `{quote.get('quote_mode')}`",
                    f"- section_id: `{quote.get('section_id')}`",
                    f"- quote_is_empty: `{str(not bool(quote.get('quote'))).lower()}`",
                    f"- review_status: `{quote.get('review_status')}`",
                ]
            )
    elif category == "reading_question":
        questions = public_data["reading_questions.json"].get("questions", [])
        question = next((item for item in questions if item.get("question_id") == target_id), None)
        if question:
            lines.extend(
                [
                    f"- scope: `{question.get('scope')}`",
                    f"- letter_id: `{question.get('letter_id', '')}`",
                    f"- section_id: `{question.get('section_id', '')}`",
                    f"- review_status: `{question.get('review_status')}`",
                ]
            )
    elif category == "book_overview":
        overview = public_data["book_overview.json"]
        structure = overview.get("structure_overview", {})
        lines.extend(
            [
                f"- schema_version: `{overview.get('schema_version')}`",
                f"- status: `{overview.get('status')}`",
                f"- body_letter_count: `{structure.get('body_letter_count')}`",
                f"- source_mode: `{structure.get('source_mode')}`",
            ]
        )
    elif category == "quote_policy":
        quote_index = public_data["quote_index.json"]
        lines.extend(
            [
                f"- quote_mode: `{quote_index.get('quote_mode')}`",
                f"- entries: `{len(quote_index.get('quotes', []))}`",
            ]
        )
    elif category == "schema_status":
        statuses = sorted({str(payload.get("status")) for payload in public_data.values()})
        schemas = sorted({str(payload.get("schema_version")) for payload in public_data.values()})
        lines.extend([f"- schemas: `{', '.join(schemas)}`", f"- statuses: `{', '.join(statuses)}`"])

    return lines or ["- structural context: `see source_file`"]


def update_command(task: dict[str, str]) -> str:
    task_id = task["task_id"]
    return (
        "python scripts/update_manual_review_result.py "
        "--project projects/second-reading-guide "
        f"--task-id {task_id} "
        "--result pass "
        '--notes "Reviewed manually." '
        '--reviewer "your-name" '
        "--apply "
        f'--confirm-update "UPDATE MANUAL REVIEW TASK {task_id}"'
    )


def render_task(task: dict[str, str], public_data: dict[str, dict[str, Any]], include_command: bool) -> list[str]:
    lines = [
        f"### {task['task_id']}",
        "",
        f"- priority: `{task['priority']}`",
        f"- category: `{task['category']}`",
        f"- target_id: `{task['target_id']}`",
        f"- target_title: `{task['target_title']}`",
        f"- source_file: `{task['source_file']}`",
        f"- current manual_result: `{task.get('manual_result') or 'blank'}`",
        f"- review question: {task['review_question']}",
        "",
        "Structured context:",
        "",
        *public_context(public_data, task),
        "",
        "Human decision needed:",
        "",
        "- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.",
        "- Add notes for every non-pass result.",
    ]
    if include_command:
        lines.extend(["", "Apply command template:", "", "```bash", update_command(task), "```"])
    lines.append("")
    return lines


def render_p0_packet(project: str, version: str, tasks: list[dict[str, str]], public_data: dict[str, dict[str, Any]]) -> str:
    p0_tasks = [row for row in tasks if row["priority"] == "P0"]
    lines = [
        f"# Manual Review P0 Packet {version}",
        "",
        f"- Project: `{project}`",
        f"- P0 tasks: `{len(p0_tasks)}`",
        "- This packet contains priority tasks only.",
        "- It does not contain source text or private paths.",
        "",
    ]
    for task in p0_tasks:
        lines.extend(render_task(task, public_data, include_command=True))
    return "\n".join(lines)


def render_all_packet(project: str, version: str, tasks: list[dict[str, str]], public_data: dict[str, dict[str, Any]]) -> str:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in tasks:
        grouped[(row["priority"], row["category"])].append(row)

    lines = [
        f"# Manual Review Full Packet {version}",
        "",
        f"- Project: `{project}`",
        f"- Total tasks: `{len(tasks)}`",
        "- Grouped by priority and category.",
        "- This packet includes structural public metadata only.",
        "",
    ]
    for (priority, category), rows in sorted(grouped.items()):
        lines.extend([f"## {priority} / {category}", "", f"- task count: `{len(rows)}`", ""])
        for task in rows:
            lines.extend(render_task(task, public_data, include_command=False))
    return "\n".join(lines)


def build(project: str, version: str) -> dict[str, Any]:
    paths = from_project(project)
    normalized = normalize_version(version)
    tasks = read_tasks(paths.report_path("manual_review_tasks_v0.7_a4.csv"))
    public_data = {
        "book_overview.json": read_json(paths.book_overview_json),
        "chapter_reading_cards.json": read_json(paths.chapter_reading_cards_json),
        "key_concepts.json": read_json(paths.key_concepts_json),
        "quote_index.json": read_json(paths.quote_index_json),
        "reading_questions.json": read_json(paths.reading_questions_json),
    }

    p0_path = paths.report_path(f"manual_review_packet_p0_{normalized}.md")
    all_path = paths.report_path(f"manual_review_packet_all_{normalized}.md")
    template_path = paths.report_path(f"manual_review_decisions_template_{normalized}.csv")

    p0_path.write_text(render_p0_packet(paths.slug, version, tasks, public_data), encoding="utf-8")
    all_path.write_text(render_all_packet(paths.slug, version, tasks, public_data), encoding="utf-8")
    write_decision_template(template_path, tasks)

    return {
        "p0Packet": str(p0_path),
        "allPacket": str(all_path),
        "decisionsTemplate": str(template_path),
        "p0Tasks": sum(1 for row in tasks if row["priority"] == "P0"),
        "allTasks": len(tasks),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    result = build(args.project, args.version)
    print(f"P0 tasks: {result['p0Tasks']}")
    print(f"All tasks: {result['allTasks']}")
    print(f"P0 packet: {result['p0Packet']}")
    print(f"All packet: {result['allPacket']}")
    print(f"Decisions template: {result['decisionsTemplate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
