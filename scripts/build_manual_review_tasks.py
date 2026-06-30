#!/usr/bin/env python3
"""Build manual review tasks for a reading-guide project.

The generated CSV is the single source of truth for manual review. This script
uses only structural working/public artifacts and does not read private source
text.
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


FIELDS = [
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


def normalize_version(version: str) -> str:
    return version.lower().replace("-", "_")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def task(
    task_id: str,
    priority: str,
    category: str,
    target_id: str,
    target_title: str,
    review_question: str,
    source_file: str,
    notes: str = "",
) -> dict[str, str]:
    return {
        "task_id": task_id,
        "priority": priority,
        "category": category,
        "target_id": target_id,
        "target_title": target_title,
        "review_question": review_question,
        "source_file": source_file,
        "manual_result": "",
        "notes": notes,
    }


def build_tasks(public_data: dict[str, dict[str, Any]], letters_brief: dict[str, Any]) -> list[dict[str, str]]:
    chapters = public_data["chapter_reading_cards.json"].get("chapters", [])
    concepts = public_data["key_concepts.json"].get("concepts", [])
    quotes = public_data["quote_index.json"].get("quotes", [])
    questions = public_data["reading_questions.json"].get("questions", [])
    letters = letters_brief.get("letters", [])

    tasks: list[dict[str, str]] = [
        task(
            "p0-public-boundary-001",
            "P0",
            "public_boundary",
            "public-layer",
            "Public reading-guide files",
            "Confirm public files contain no private paths, no source text, and no long excerpts.",
            "projects/second-reading-guide/public/*.json",
            "Boundary review before any status promotion.",
        ),
        task(
            "p0-book-overview-001",
            "P0",
            "book_overview",
            "book_overview",
            "Book overview",
            "Confirm the overview accurately describes the draft as structural and conservative.",
            "projects/second-reading-guide/public/book_overview.json",
        ),
        task(
            "p0-quote-policy-001",
            "P0",
            "quote_policy",
            "quote_index",
            "Quote index policy",
            "Confirm quote entries use structural_no_quote and do not publish source quotations.",
            "projects/second-reading-guide/public/quote_index.json",
        ),
        task(
            "p0-schema-status-001",
            "P0",
            "schema_status",
            "reading-guide.v0.2",
            "Schema and status",
            "Confirm schema_version is reading-guide.v0.2 and status remains draft.",
            "projects/second-reading-guide/public/*.json",
        ),
        task(
            "p0-web-mirror-001",
            "P0",
            "web_mirror",
            "web-public-mirror",
            "Web public mirror",
            "Confirm web mirror JSON files match project public JSON files.",
            "web/public/projects/second-reading-guide/*.json",
        ),
    ]

    sample_indexes = {0, 6, 12, 18, 24}
    for idx in sorted(i for i in sample_indexes if i < len(chapters)):
        chapter = chapters[idx]
        order = int(chapter.get("order") or idx + 1)
        tasks.append(
            task(
                f"p0-chapter-sample-{order:03d}",
                "P0",
                "chapter_card_sample",
                str(chapter.get("chapter_id") or f"chapter-{order:03d}"),
                str(chapter.get("title") or f"Chapter {order}"),
                "Spot-check that this chapter card is derived only from structural metadata.",
                "projects/second-reading-guide/public/chapter_reading_cards.json",
                "Required P0 sample coverage across the 25 chapter cards.",
            )
        )

    for idx, chapter in enumerate(chapters, start=1):
        order = int(chapter.get("order") or idx)
        tasks.append(
            task(
                f"p1-chapter-card-{order:03d}",
                "P1",
                "chapter_card",
                str(chapter.get("chapter_id") or f"chapter-{order:03d}"),
                str(chapter.get("title") or f"Chapter {order}"),
                "Review title, places, themes, counts, and structural evidence reference.",
                "projects/second-reading-guide/public/chapter_reading_cards.json",
            )
        )

    for idx, concept in enumerate(concepts, start=1):
        tasks.append(
            task(
                f"p1-key-concept-{idx:03d}",
                "P1",
                "key_concept",
                str(concept.get("concept_id") or f"concept-{idx:03d}"),
                str(concept.get("label") or f"Concept {idx}"),
                "Review whether this concept grouping is reasonable as a structural draft.",
                "projects/second-reading-guide/public/key_concepts.json",
            )
        )

    for idx, question in enumerate(questions, start=1):
        tasks.append(
            task(
                f"p1-reading-question-{idx:03d}",
                "P1",
                "reading_question",
                str(question.get("question_id") or f"question-{idx:03d}"),
                str(question.get("question") or f"Question {idx}"),
                "Review whether this reading question is useful and appropriately conservative.",
                "projects/second-reading-guide/public/reading_questions.json",
            )
        )

    for idx, quote in enumerate(quotes, start=1):
        tasks.append(
            task(
                f"p1-quote-structural-{idx:03d}",
                "P1",
                "quote_structural_entry",
                str(quote.get("quote_id") or f"quote-placeholder-{idx:03d}"),
                str(quote.get("section_id") or quote.get("letter_id") or f"Quote slot {idx}"),
                "Confirm this quote slot remains structural-only until a human selects an allowed short quote.",
                "projects/second-reading-guide/public/quote_index.json",
            )
        )

    letter_count = len(letters)
    tasks.extend(
        [
            task(
                "p2-wording-polish-001",
                "P2",
                "wording_polish",
                "public-reading-guide",
                "Public wording",
                "Improve wording only after P0/P1 evidence checks are complete.",
                "projects/second-reading-guide/public/*.json",
                f"Current structural basis covers {letter_count} body letters.",
            ),
            task(
                "p2-concept-grouping-001",
                "P2",
                "concept_grouping_refinement",
                "key_concepts",
                "Concept grouping refinement",
                "Consider whether concept labels should be merged, split, or renamed after manual reading.",
                "projects/second-reading-guide/public/key_concepts.json",
            ),
            task(
                "p2-future-quote-review-001",
                "P2",
                "future_quote_replacement",
                "quote_index",
                "Future quote review",
                "Prepare a later process for manually selected short quotations without publishing long excerpts.",
                "projects/second-reading-guide/public/quote_index.json",
            ),
            task(
                "p2-question-quality-001",
                "P2",
                "question_quality_enhancement",
                "reading_questions",
                "Question quality enhancement",
                "Refine generic structural questions after close reading and manual review.",
                "projects/second-reading-guide/public/reading_questions.json",
            ),
        ]
    )

    return tasks


def summarize(tasks: list[dict[str, str]], project: str, version: str) -> dict[str, Any]:
    priority_counts = Counter(row["priority"] for row in tasks)
    category_counts = Counter(row["category"] for row in tasks)
    source_counts = Counter(row["source_file"] for row in tasks)
    return {
        "project": project,
        "version": version,
        "status": "draft",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "totalTasks": len(tasks),
        "priorityCounts": dict(sorted(priority_counts.items())),
        "categoryCounts": dict(sorted(category_counts.items())),
        "sourceFileCounts": dict(sorted(source_counts.items())),
        "coverage": {
            "chapterCards": sum(1 for row in tasks if row["category"] == "chapter_card"),
            "keyConcepts": sum(1 for row in tasks if row["category"] == "key_concept"),
            "quoteStructuralEntries": sum(1 for row in tasks if row["category"] == "quote_structural_entry"),
            "readingQuestions": sum(1 for row in tasks if row["category"] == "reading_question"),
        },
    }


def write_tasks_csv(path: Path, tasks: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(tasks)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_dashboard(summary: dict[str, Any], tasks: list[dict[str, str]]) -> str:
    lines = [
        "# Manual Review Dashboard v0.7-A4",
        "",
        f"- Project: `{summary['project']}`",
        "- Status: `draft`",
        f"- Total tasks: `{summary['totalTasks']}`",
        "",
        "## Priority Counts",
        "",
        "| priority | count |",
        "|---|---:|",
    ]
    for priority, count in summary["priorityCounts"].items():
        lines.append(f"| `{priority}` | {count} |")

    lines.extend(["", "## Category Counts", "", "| category | count |", "|---|---:|"])
    for category, count in summary["categoryCounts"].items():
        lines.append(f"| `{category}` | {count} |")

    lines.extend(
        [
            "",
            "## P0 Tasks",
            "",
            "| task_id | category | target | question |",
            "|---|---|---|---|",
        ]
    )
    for row in tasks:
        if row["priority"] == "P0":
            question = row["review_question"].replace("|", " ")
            lines.append(f"| `{row['task_id']}` | `{row['category']}` | {row['target_title']} | {question} |")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- The CSV file is the single source of truth for manual review.",
            "- `manual_result` is intentionally blank for all generated tasks.",
            "- A4 creates review tasks only and does not promote project status.",
            "",
        ]
    )
    return "\n".join(lines)


def build(project: str, version: str) -> dict[str, Any]:
    paths = from_project(project)
    public_data = {
        "book_overview.json": read_json(paths.book_overview_json),
        "chapter_reading_cards.json": read_json(paths.chapter_reading_cards_json),
        "key_concepts.json": read_json(paths.key_concepts_json),
        "quote_index.json": read_json(paths.quote_index_json),
        "reading_questions.json": read_json(paths.reading_questions_json),
    }
    letters_brief = read_json(paths.working_path("letters_brief.json"))

    tasks = build_tasks(public_data, letters_brief)
    normalized = normalize_version(version)
    tasks_path = paths.report_path(f"manual_review_tasks_{normalized}.csv")
    summary_path = paths.report_path(f"manual_review_summary_{normalized}.json")
    dashboard_path = paths.report_path(f"manual_review_dashboard_{normalized}.md")

    summary = summarize(tasks, paths.slug, version)
    write_tasks_csv(tasks_path, tasks)
    write_json(summary_path, summary)
    dashboard_path.write_text(render_dashboard(summary, tasks), encoding="utf-8")

    return {
        "tasks_path": str(tasks_path),
        "summary_path": str(summary_path),
        "dashboard_path": str(dashboard_path),
        "summary": summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    result = build(args.project, args.version)
    summary = result["summary"]
    print(f"Manual review tasks: {summary['totalTasks']}")
    print(f"Priority counts: {summary['priorityCounts']}")
    print(f"Category counts: {summary['categoryCounts']}")
    print(f"Source file counts: {summary['sourceFileCounts']}")
    print(f"CSV: {result['tasks_path']}")
    print(f"Summary: {result['summary_path']}")
    print(f"Dashboard: {result['dashboard_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
