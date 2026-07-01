#!/usr/bin/env python3
"""Build v0.7-A16 source anchor layer for the reading guide.

The builder converts existing public short clues into explicit source_excerpts.
It does not read private EPUB/book/section/chunk files and does not change
manual review results or project status.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.lib.project_paths import from_project
except ModuleNotFoundError:
    from lib.project_paths import from_project


VERSION = "v0.7-A16"
PUBLIC_FILES = [
    "book_overview.json",
    "chapter_reading_cards.json",
    "key_concepts.json",
    "quote_index.json",
    "reading_questions.json",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def text_or(value: str | None, fallback: str) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else fallback


def source_text_from_clue(clue: dict[str, Any], chapter: dict[str, Any], index: int) -> str:
    text = text_or(clue.get("excerpt"), "")
    if text:
        return text[:220]
    places = "、".join((chapter.get("places") or [])[:3]) or "地点待复核"
    return f"结构化原文线索：本封信围绕 {places} 展开。"


def build_excerpts(chapter: dict[str, Any]) -> list[dict[str, Any]]:
    unit = chapter.get("letter_reading_unit") or {}
    clues = list(unit.get("source_clues") or chapter.get("original_excerpt") or [])
    scene_notes = list(chapter.get("original_scene_notes") or unit.get("secondary_details", {}).get("scene_notes") or [])
    places = chapter.get("places") or []

    while len(clues) < 2:
        if scene_notes:
            clues.append(
                {
                    "mode": "scene_anchor",
                    "excerpt": scene_notes.pop(0),
                    "note": "场景线索转为原文锚点，帮助读者先抓住文本场面。",
                    "use": "用于进入本封信的场景阅读。",
                }
            )
        else:
            clues.append(
                {
                    "mode": "route_anchor",
                    "excerpt": f"本封信的地点线索集中在 {'、'.join(places[:3]) or '待复核地点'}。",
                    "note": "结构化路线线索，用于补足原文锚点层。",
                    "use": "用于把文本锚点接到路线和地点说明。",
                }
            )

    excerpts: list[dict[str, Any]] = []
    for index, clue in enumerate(clues[:4], start=1):
        anchor_id = f"{chapter.get('letter_id', 'letter')}-source-anchor-{index:02d}"
        excerpts.append(
            {
                "anchor_id": anchor_id,
                "text": source_text_from_clue(clue, chapter, index),
                "note": text_or(
                    clue.get("note"),
                    "这条短摘或线索用于把解释落回文本，不替代原书全文。",
                ),
                "reading_use": text_or(
                    clue.get("use"),
                    "先读这个锚点，再看场景、路线和今昔对照。",
                ),
                "mode": clue.get("mode") or "short_source_anchor",
                "review_status": "manual-review-pending",
            }
        )
    return excerpts


def question_anchor_for(question: dict[str, Any], chapters_by_letter: dict[str, dict[str, Any]], chapters: list[dict[str, Any]]) -> dict[str, Any]:
    linked_letters = question.get("linked_letters") or []
    letter_id = question.get("letter_id") or (linked_letters[0] if linked_letters else None)
    if question.get("scope") == "book":
        anchors = []
        for chapter in chapters[:3]:
            first = (chapter.get("source_excerpts") or [{}])[0]
            anchors.append(
                {
                    "letter_id": chapter.get("letter_id"),
                    "chapter_id": chapter.get("chapter_id"),
                    "anchor_id": first.get("anchor_id"),
                }
            )
        return {
            "anchor_type": "book_route_sample",
            "anchors": anchors,
            "note": "全书问题先连接前三封信的原文锚点，再回到 25 封书信整体路线。",
        }

    chapter = chapters_by_letter.get(str(letter_id))
    if not chapter:
        chapter = chapters[0]
    first = (chapter.get("source_excerpts") or [{}])[0]
    return {
        "anchor_type": "letter_source_excerpt",
        "letter_id": chapter.get("letter_id"),
        "chapter_id": chapter.get("chapter_id"),
        "anchor_id": first.get("anchor_id"),
        "place_or_scene": "、".join((chapter.get("places") or [])[:3]) or chapter.get("title"),
        "note": "问题回答应先回到这封信的原文锚点，再展开场景、路线和今昔对照。",
    }


def render_plan() -> str:
    return "\n".join(
        [
            "# v0.7-A16 Source Anchor Plan",
            "",
            "## Goal",
            "",
            "Fix the missing text-anchor layer by adding source excerpts to every letter card.",
            "",
            "## Design",
            "",
            "- Each of the 25 letters gets `source_excerpts` with 2-4 anchored short clues.",
            "- The visible letter flow becomes: source anchor, scene, route, then/now, question, answer.",
            "- Each reading question receives `source_anchor` so answers can return to a letter or scene.",
            "",
            "## Boundaries",
            "",
            "- This builder uses existing public short clues and structured summaries.",
            "- It does not publish EPUB, book.md, section JSONL, chunk JSONL, or private paths.",
            "- Status remains draft / public-preview / manual-review-pending.",
            "",
        ]
    )


def render_report(stats: dict[str, int]) -> str:
    return "\n".join(
        [
            "# Source Anchor Report v0.7-A16",
            "",
            f"- Letter cards: `{stats['letters']}`",
            f"- Letters with source_excerpts: `{stats['letters_with_excerpts']}`",
            f"- Minimum excerpts per letter: `{stats['min_excerpts']}`",
            f"- Reading questions with source_anchor: `{stats['questions_with_source_anchor']}`",
            f"- Total source excerpts: `{stats['total_excerpts']}`",
            "",
            "## Boundary",
            "",
            "- Status remains `draft`.",
            "- release_phase remains `public-preview`.",
            "- review_status remains `manual-review-pending`.",
            "- Manual review results are unchanged.",
            "",
        ]
    )


def build(project: str) -> dict[str, int]:
    paths = from_project(project)
    overview = read_json(paths.book_overview_json)
    chapters_data = read_json(paths.chapter_reading_cards_json)
    questions_data = read_json(paths.reading_questions_json)
    chapters = chapters_data.get("chapters", [])
    questions = questions_data.get("questions", [])

    for chapter in chapters:
        excerpts = build_excerpts(chapter)
        chapter["source_excerpts"] = excerpts
        chapter["source_anchor_layer_ready"] = True
        chapter["updated_in"] = VERSION
        unit = chapter.setdefault("letter_reading_unit", {})
        unit["source_excerpts"] = excerpts
        unit["reading_order"] = [
            "source_anchor",
            "scene",
            "route",
            "then_now",
            "question",
            "answer",
        ]
        unit["version"] = VERSION

    chapters_by_letter = {str(chapter.get("letter_id")): chapter for chapter in chapters}
    for question in questions:
        question["source_anchor"] = question_anchor_for(question, chapters_by_letter, chapters)
        question["updated_in"] = VERSION

    overview["source_anchor_layer"] = {
        "version": VERSION,
        "letters_with_source_excerpts": sum(1 for chapter in chapters if chapter.get("source_excerpts")),
        "min_excerpts_per_letter": min(len(chapter.get("source_excerpts") or []) for chapter in chapters) if chapters else 0,
        "question_source_anchor_count": sum(1 for question in questions if question.get("source_anchor")),
        "reading_order": ["原文锚点", "场景说明", "路线结构", "今昔对照", "阅读问题", "参考答案"],
        "updated_in": VERSION,
    }
    overview["generated_at"] = datetime.now(timezone.utc).isoformat()
    for payload in [overview, chapters_data, questions_data]:
        payload["status"] = "draft"
        payload["release_phase"] = "public-preview"
        payload["review_status"] = "manual-review-pending"

    write_json(paths.book_overview_json, overview)
    write_json(paths.chapter_reading_cards_json, chapters_data)
    write_json(paths.reading_questions_json, questions_data)
    for name in PUBLIC_FILES:
        shutil.copyfile(paths.public_path(name), paths.web_project_path(name))

    stats = {
        "letters": len(chapters),
        "letters_with_excerpts": sum(1 for chapter in chapters if chapter.get("source_excerpts")),
        "min_excerpts": min(len(chapter.get("source_excerpts") or []) for chapter in chapters) if chapters else 0,
        "questions_with_source_anchor": sum(1 for question in questions if question.get("source_anchor")),
        "total_excerpts": sum(len(chapter.get("source_excerpts") or []) for chapter in chapters),
    }
    paths.report_path("v0.7_a16_source_anchor_plan.md").write_text(render_plan(), encoding="utf-8")
    paths.report_path("source_anchor_report_v0.7_a16.md").write_text(render_report(stats), encoding="utf-8")
    return stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", default=VERSION)
    args = parser.parse_args()
    stats = build(args.project)
    print("Built source anchor layer")
    for key, value in stats.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
