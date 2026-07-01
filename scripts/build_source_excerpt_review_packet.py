#!/usr/bin/env python3
"""Build a review packet for public source excerpts.

A19 is review-packet-only: it reads public JSON, writes reports/templates, and
does not alter public excerpt content.
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


VERSION = "v0.7-A19"

TASK_FIELDS = [
    "excerpt_task_id",
    "letter_id",
    "section_id",
    "chapter_title",
    "excerpt_index",
    "placement",
    "excerpt_text",
    "excerpt_note",
    "excerpt_type",
    "linked_question_id",
    "review_priority",
    "review_question",
    "suggested_checks",
    "review_result",
    "review_notes",
    "reviewer",
    "reviewed_at",
]

DECISION_FIELDS = [
    "excerpt_task_id",
    "letter_id",
    "section_id",
    "chapter_title",
    "excerpt_text",
    "current_placement",
    "review_result",
    "review_notes",
    "reviewer",
    "reviewed_at",
]

LEGAL_REVIEW_RESULTS = ["keep", "replace", "move_to_extra", "move_to_core", "needs_context", "remove", "defer"]


def normalize_version(version: str) -> str:
    return version.lower().replace("-", "_")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def anchor_ids_from_question(question: dict[str, Any]) -> list[str]:
    anchor = question.get("source_anchor")
    if not isinstance(anchor, dict):
        return []
    ids: list[str] = []
    if anchor.get("anchor_id"):
        ids.append(str(anchor["anchor_id"]))
    for item in anchor.get("anchors") or []:
        if isinstance(item, dict) and item.get("anchor_id"):
            ids.append(str(item["anchor_id"]))
    return ids


def build_question_index(questions: dict[str, Any]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = defaultdict(list)
    for question in questions.get("questions", []):
        question_id = str(question.get("question_id", ""))
        for anchor_id in anchor_ids_from_question(question):
            if question_id:
                index[anchor_id].append(question_id)
    return index


def excerpt_placement(anchor_id: str, text: str, core: list[dict[str, Any]], extra: list[dict[str, Any]]) -> str:
    if any(item.get("anchor_id") == anchor_id or item.get("text") == text for item in core):
        return "core"
    if any(item.get("anchor_id") == anchor_id or item.get("text") == text for item in extra):
        return "extra"
    return "source"


def priority_for(placement: str, excerpt_index: int, linked_question_ids: list[str]) -> str:
    if placement == "core" and excerpt_index == 1:
        return "P0"
    if placement == "core" or linked_question_ids:
        return "P1"
    return "P2"


def review_question_for(placement: str, excerpt_type: str) -> str:
    base = [
        "这条摘录是否足以锚定本封信？",
        "它是否有场景感、地点感或行旅感？",
        "是否需要补充上下文或替换为更有代表性的片段？",
    ]
    if placement == "core":
        base.append("它是否适合继续放在核心摘录区，还是应移到更多片段？")
    else:
        base.append("它是否值得提升为核心摘录，还是保留在更多片段中？")
    if excerpt_type in {"other", ""}:
        base.append("当前类型较泛，请人工判断是否需要重新归类。")
    return " ".join(base)


def suggested_checks_for(text: str, placement: str) -> str:
    checks = [
        "代表性",
        "场景/地点/行旅感",
        "语义完整",
        "长度节奏",
        "说明是否准确",
    ]
    if len(text) < 28:
        checks.append("偏短")
    if len(text) > 140:
        checks.append("偏长")
    if placement == "core":
        checks.append("核心位置是否合适")
    else:
        checks.append("是否需要移入核心")
    return "；".join(checks)


def build_tasks(chapters: dict[str, Any], questions: dict[str, Any]) -> list[dict[str, str]]:
    question_index = build_question_index(questions)
    tasks: list[dict[str, str]] = []
    seen: set[str] = set()

    for chapter in chapters.get("chapters", []):
        source = chapter.get("source_excerpts") or []
        core = chapter.get("core_source_excerpts") or []
        extra = chapter.get("extra_source_excerpts") or []
        letter_id = str(chapter.get("letter_id", ""))
        section_id = str(chapter.get("section_id", ""))
        title = str(chapter.get("title", ""))

        for index, excerpt in enumerate(source, start=1):
            anchor_id = str(excerpt.get("anchor_id") or f"{letter_id}-source-{index:02d}")
            dedupe_key = f"{letter_id}:{anchor_id}:{excerpt.get('text', '')}"
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            placement = excerpt_placement(anchor_id, str(excerpt.get("text", "")), core, extra)
            linked_question_ids = question_index.get(anchor_id, [])
            priority = priority_for(placement, index, linked_question_ids)
            task_id = f"excerpt-{letter_id}-{index:03d}"
            text = str(excerpt.get("text", ""))
            tasks.append(
                {
                    "excerpt_task_id": task_id,
                    "letter_id": letter_id,
                    "section_id": section_id,
                    "chapter_title": title,
                    "excerpt_index": str(index),
                    "placement": placement,
                    "excerpt_text": text,
                    "excerpt_note": str(excerpt.get("note", "")),
                    "excerpt_type": str(excerpt.get("excerpt_type", "")),
                    "linked_question_id": ";".join(linked_question_ids),
                    "review_priority": priority,
                    "review_question": review_question_for(placement, str(excerpt.get("excerpt_type", ""))),
                    "suggested_checks": suggested_checks_for(text, placement),
                    "review_result": "",
                    "review_notes": "",
                    "reviewer": "",
                    "reviewed_at": "",
                }
            )
    return tasks


def decision_rows(tasks: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "excerpt_task_id": task["excerpt_task_id"],
            "letter_id": task["letter_id"],
            "section_id": task["section_id"],
            "chapter_title": task["chapter_title"],
            "excerpt_text": task["excerpt_text"],
            "current_placement": task["placement"],
            "review_result": "",
            "review_notes": "",
            "reviewer": "",
            "reviewed_at": "",
        }
        for task in tasks
    ]


def render_plan(version: str) -> str:
    return "\n".join(
        [
            f"# {version} Source Excerpt Review Plan",
            "",
            "## User Feedback",
            "",
            "A18 added real source excerpts. The next risk is not missing text, but excerpt quality: some excerpts may be too short, too long, weakly representative, or better placed in the folded area.",
            "",
            "## A19 Goal",
            "",
            "Generate a review packet for all public source excerpts without changing the public JSON, web mirror, manual review CSV, or project status.",
            "",
            "## Inputs",
            "",
            "- `projects/second-reading-guide/public/book_overview.json`",
            "- `projects/second-reading-guide/public/chapter_reading_cards.json`",
            "- `projects/second-reading-guide/public/reading_questions.json`",
            "",
            "## Outputs",
            "",
            "- `source_excerpt_review_packet_v0.7_a19.md`",
            "- `source_excerpt_review_tasks_v0.7_a19.csv`",
            "- `source_excerpt_review_decisions_template_v0.7_a19.csv`",
            "- `source_excerpt_review_summary_v0.7_a19.json`",
            "- `source_excerpt_review_validation_v0.7_a19.md`",
            "",
            "## Task Fields",
            "",
            "Each task records letter, section, placement, excerpt text, note, type, linked question, priority, review question, and blank review decision fields.",
            "",
            "## Legal Review Results",
            "",
            "`keep`, `replace`, `move_to_extra`, `move_to_core`, `needs_context`, `remove`, `defer`.",
            "",
            "## Priority Rules",
            "",
            "- P0: first core excerpt in each letter.",
            "- P1: remaining core excerpts and any excerpt directly linked from a reading question.",
            "- P2: extra excerpts.",
            "",
            "## Why No Excerpt Changes",
            "",
            "A19 is a review-packet-only phase. It prepares human decisions, but does not make those decisions or rewrite source excerpts.",
            "",
            "## How To Use The Template",
            "",
            "Copy or edit the decisions template, fill `review_result` and notes manually, then use a later importer/apply phase to update excerpt placement or replacement.",
            "",
            "## A20 Recommendation",
            "",
            "After excerpt review, build either an excerpt-decision importer or a whole-letter reading mode for longer personal reading.",
            "",
        ]
    )


def render_packet(project: str, version: str, tasks: list[dict[str, str]], questions: dict[str, Any]) -> str:
    questions_by_letter: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for question in questions.get("questions", []):
        letter_id = question.get("letter_id")
        if letter_id:
            questions_by_letter[str(letter_id)].append(question)

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for task in tasks:
        grouped[task["letter_id"]].append(task)

    lines = [
        f"# Source Excerpt Review Packet {version}",
        "",
        f"- Project: `{project}`",
        f"- Total excerpt tasks: `{len(tasks)}`",
        "- Purpose: review excerpt quality only; this packet does not change public JSON.",
        "",
    ]
    for letter_id in sorted(grouped, key=lambda value: int(value.split("-")[-1])):
        rows = grouped[letter_id]
        first = rows[0]
        lines.extend(
            [
                f"## {first['chapter_title']}",
                "",
                f"- letter_id: `{letter_id}`",
                f"- section_id: `{first['section_id']}`",
                f"- current excerpts: `{len(rows)}`",
                "",
                "### Current core excerpts",
                "",
            ]
        )
        for row in [item for item in rows if item["placement"] == "core"]:
            lines.extend(render_task_block(row))
        lines.extend(["### Current extra excerpts", ""])
        for row in [item for item in rows if item["placement"] != "core"]:
            lines.extend(render_task_block(row))

        linked_questions = questions_by_letter.get(letter_id, [])
        lines.extend(["### Linked reading question", ""])
        if linked_questions:
            for question in linked_questions[:2]:
                lines.append(f"- `{question.get('question_id')}`: {question.get('question')}")
        else:
            lines.append("- No letter-specific question linked.")
        lines.extend(
            [
                "",
                "### Human review focus",
                "",
                "- Confirm whether core excerpts are the strongest visible entry points.",
                "- Mark weak excerpts as `replace`, `move_to_extra`, or `needs_context` in the decisions template.",
                "- Keep all decision fields blank until an actual human review is performed.",
                "",
            ]
        )
    return "\n".join(lines)


def render_task_block(row: dict[str, str]) -> list[str]:
    return [
        f"#### {row['excerpt_task_id']} / {row['review_priority']} / {row['placement']}",
        "",
        f"> {row['excerpt_text']}",
        "",
        f"- type: `{row['excerpt_type']}`",
        f"- linked_question_id: `{row['linked_question_id'] or 'none'}`",
        f"- note: {row['excerpt_note']}",
        f"- review question: {row['review_question']}",
        f"- suggested checks: {row['suggested_checks']}",
        "",
    ]


def build_summary(tasks: list[dict[str, str]], version: str) -> dict[str, Any]:
    priority_counts = Counter(task["review_priority"] for task in tasks)
    placement_counts = Counter(task["placement"] for task in tasks)
    letters = {task["letter_id"] for task in tasks}
    return {
        "version": version,
        "status": "review-packet-only",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "totalExcerptTasks": len(tasks),
        "lettersCovered": len(letters),
        "coreExcerptTasks": placement_counts.get("core", 0),
        "extraExcerptTasks": placement_counts.get("extra", 0),
        "sourceOnlyExcerptTasks": placement_counts.get("source", 0),
        "p0Tasks": priority_counts.get("P0", 0),
        "p1Tasks": priority_counts.get("P1", 0),
        "p2Tasks": priority_counts.get("P2", 0),
        "blankReviewResults": sum(1 for task in tasks if not task.get("review_result")),
        "readyForExcerptApply": False,
        "allowedReviewResults": LEGAL_REVIEW_RESULTS,
    }


def build(project: str, version: str) -> dict[str, Any]:
    paths = from_project(project)
    chapters = read_json(paths.chapter_reading_cards_json)
    questions = read_json(paths.reading_questions_json)
    _overview = read_json(paths.book_overview_json)
    tasks = build_tasks(chapters, questions)
    summary = build_summary(tasks, version)

    paths.report_path("v0.7_a19_source_excerpt_review_plan.md").write_text(render_plan(version), encoding="utf-8")
    paths.report_path("source_excerpt_review_packet_v0.7_a19.md").write_text(
        render_packet(paths.slug, version, tasks, questions),
        encoding="utf-8",
    )
    write_csv(paths.report_path("source_excerpt_review_tasks_v0.7_a19.csv"), tasks, TASK_FIELDS)
    write_csv(paths.report_path("source_excerpt_review_decisions_template_v0.7_a19.csv"), decision_rows(tasks), DECISION_FIELDS)
    write_json(paths.report_path("source_excerpt_review_summary_v0.7_a19.json"), summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", default=VERSION)
    args = parser.parse_args()
    summary = build(args.project, args.version)
    print("Source excerpt review packet built")
    for key in ["totalExcerptTasks", "lettersCovered", "p0Tasks", "p1Tasks", "p2Tasks", "blankReviewResults"]:
        print(f"{key}: {summary[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
