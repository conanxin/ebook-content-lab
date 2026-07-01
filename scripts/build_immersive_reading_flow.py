#!/usr/bin/env python3
"""Build v0.7-A17 immersive reading flow metadata.

This builder keeps all existing source_excerpts intact, but splits display into
quick and deep reading layers so each letter card is lighter by default.
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


VERSION = "v0.7-A17"
PUBLIC_FILES = [
    "book_overview.json",
    "chapter_reading_cards.json",
    "key_concepts.json",
    "quote_index.json",
    "reading_questions.json",
]
SEGMENTS = [
    "起程与山路",
    "南行与城市",
    "山水与名胜",
    "江南与海上",
    "返程与回望",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def text_or(value: str | None, fallback: str) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else fallback


def first_sentence(text: str | None, limit: int = 150) -> str:
    if not text:
        return "参考回答待人工复核。"
    normalized = " ".join(text.split())
    for mark in ["。", "！", "？", "；"]:
        if mark in normalized:
            normalized = normalized.split(mark, 1)[0] + mark
            break
    return normalized[:limit]


def question_answer(question: dict[str, Any]) -> str:
    return text_or(
        question.get("close_reading_answer")
        or question.get("answer_hint_expanded")
        or question.get("answer_hint")
        or question.get("reference_answer")
        or question.get("guide_answer"),
        "参考回答待人工复核。",
    )


def build(project: str) -> dict[str, int]:
    paths = from_project(project)
    overview = read_json(paths.book_overview_json)
    chapter_data = read_json(paths.chapter_reading_cards_json)
    questions_data = read_json(paths.reading_questions_json)
    chapters = chapter_data.get("chapters", [])
    questions = questions_data.get("questions", [])
    questions_by_letter = {question.get("letter_id"): question for question in questions if question.get("letter_id")}

    for index, chapter in enumerate(chapters):
        excerpts = list(chapter.get("source_excerpts") or [])
        core = excerpts[:2]
        extra = excerpts[2:]
        letter_id = chapter.get("letter_id")
        previous_letter_id = chapters[index - 1].get("letter_id") if index > 0 else None
        next_letter_id = chapters[index + 1].get("letter_id") if index + 1 < len(chapters) else None
        segment = SEGMENTS[min(index // 5, len(SEGMENTS) - 1)]
        question = questions_by_letter.get(letter_id)
        answer = question_answer(question or {})

        chapter["core_source_excerpts"] = core
        chapter["extra_source_excerpts"] = extra
        chapter["reading_segment"] = segment
        chapter["reading_flow"] = {
            "version": VERSION,
            "default_mode": "quick",
            "available_modes": ["quick", "deep"],
            "default_visible_excerpt_count": len(core),
            "extra_excerpt_count": len(extra),
            "recommended_reading_order": [
                "core_excerpt",
                "source_summary",
                "scene_notes",
                "route_then_now",
                "close_reading",
                "question_answer",
            ],
            "previous_letter_id": previous_letter_id,
            "next_letter_id": next_letter_id,
        }
        chapter["navigation"] = {
            "previous_letter_id": previous_letter_id,
            "next_letter_id": next_letter_id,
            "position_label": f"第 {index + 1} / {len(chapters)} 封",
            "segment": segment,
        }
        chapter["reading_modes"] = {
            "quick_summary": chapter.get("letter_reading_unit", {}).get("one_sentence_guide")
            or chapter.get("source_informed_summary")
            or chapter.get("summary"),
            "deep_reading_prompt": "展开精读后，按原文锚点、场景说明、路线结构、今昔对照、问题和参考答案顺序阅读。",
            "mobile_hint": "手机阅读时建议先用快速浏览走完整条路线，再逐封展开精读。",
        }
        unit = chapter.setdefault("letter_reading_unit", {})
        unit["core_source_excerpts"] = core
        unit["extra_source_excerpts"] = extra
        unit["reading_mode"] = chapter["reading_modes"]
        unit["navigation"] = chapter["navigation"]
        unit["version"] = VERSION
        chapter["updated_in"] = VERSION

    chapters_by_letter = {chapter.get("letter_id"): chapter for chapter in chapters}
    for question in questions:
        letter_id = question.get("letter_id") or (question.get("linked_letters") or [None])[0]
        chapter = chapters_by_letter.get(letter_id)
        answer = question_answer(question)
        question["quick_answer"] = first_sentence(question.get("answer_summary") or answer, 120)
        question["deep_answer"] = answer
        if chapter:
            question["linked_letter_navigation"] = {
                "letter_id": chapter.get("letter_id"),
                "chapter_id": chapter.get("chapter_id"),
                "previous_letter_id": chapter.get("navigation", {}).get("previous_letter_id"),
                "next_letter_id": chapter.get("navigation", {}).get("next_letter_id"),
                "position_label": chapter.get("navigation", {}).get("position_label"),
            }
        else:
            question["linked_letter_navigation"] = {
                "letter_id": None,
                "chapter_id": None,
                "previous_letter_id": None,
                "next_letter_id": None,
                "position_label": "全书问题",
            }
        question["updated_in"] = VERSION

    overview["immersive_reading"] = {
        "version": VERSION,
        "mode": "letter-flow",
        "default_mode": "quick",
        "supports_deep_mode": True,
        "letter_count": len(chapters),
        "navigation": "previous-next",
        "source_anchor_policy": "2 core excerpts by default, extra excerpts folded",
        "updated_in": VERSION,
    }
    overview["reading_flow_summary"] = (
        "建议先用快速浏览读完 25 封信的路线推进，再对感兴趣的信切换到精读模式。"
        "快速浏览只显示核心摘要、1-2 条原文锚点、路线和答案摘要；精读模式展开全部原文线索、场景、今昔对照和完整回答。"
    )
    overview["generated_at"] = datetime.now(timezone.utc).isoformat()

    for payload in [overview, chapter_data, questions_data]:
        payload["status"] = "draft"
        payload["release_phase"] = "public-preview"
        payload["review_status"] = "manual-review-pending"

    write_json(paths.book_overview_json, overview)
    write_json(paths.chapter_reading_cards_json, chapter_data)
    write_json(paths.reading_questions_json, questions_data)
    for name in PUBLIC_FILES:
        shutil.copyfile(paths.public_path(name), paths.web_project_path(name))

    stats = {
        "letters": len(chapters),
        "source_excerpts_total": sum(len(chapter.get("source_excerpts") or []) for chapter in chapters),
        "core_coverage": sum(1 for chapter in chapters if chapter.get("core_source_excerpts")),
        "extra_coverage": sum(1 for chapter in chapters if chapter.get("extra_source_excerpts")),
        "reading_flow_coverage": sum(1 for chapter in chapters if chapter.get("reading_flow")),
        "navigation_coverage": sum(1 for chapter in chapters if chapter.get("navigation")),
        "reading_modes_coverage": sum(1 for chapter in chapters if chapter.get("reading_modes")),
        "question_quick_deep_coverage": sum(1 for question in questions if question.get("quick_answer") and question.get("deep_answer")),
    }
    paths.report_path("v0.7_a17_immersive_reading_flow_plan.md").write_text(render_plan(), encoding="utf-8")
    paths.report_path("immersive_reading_flow_report_v0.7_a17.md").write_text(render_report(stats), encoding="utf-8")
    paths.report_path("immersive_reading_flow_backlog_v0.7_a17.md").write_text(render_backlog(chapters), encoding="utf-8")
    return stats


def render_plan() -> str:
    return "\n".join(
        [
            "# v0.7-A17 Immersive Reading Flow Plan",
            "",
            "## User Feedback",
            "",
            "A16 added source anchors, but showing every anchor at once can make each letter card too long and dense.",
            "",
            "## Goals",
            "",
            "- Make default reading lighter.",
            "- Keep source anchors but show only core excerpts by default.",
            "- Add quick/deep reading modes.",
            "- Add previous/next letter navigation.",
            "- Improve mobile long-card rhythm.",
            "",
            "## Excerpt Layering",
            "",
            "- `source_excerpts` is retained as the full source anchor set.",
            "- `core_source_excerpts` contains the first two anchors.",
            "- `extra_source_excerpts` contains the folded anchors.",
            "",
            "## Safety Boundary",
            "",
            "- No private source files are read or published.",
            "- Status remains draft / public-preview / manual-review-pending.",
            "- No promotion or manual review result is changed.",
            "",
            "## A18 Suggestion",
            "",
            "Consider a true reader mode, split view, side notes, or real manual review pass.",
            "",
        ]
    )


def render_report(stats: dict[str, int]) -> str:
    lines = [
        "# Immersive Reading Flow Report v0.7-A17",
        "",
        "## Counts",
        "",
    ]
    for key, value in stats.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## UI Optimization",
            "",
            "- Quick/deep mode metadata generated.",
            "- Each letter receives previous/next navigation.",
            "- Extra excerpts are separated for folded display.",
            "",
            "## Public Preview State",
            "",
            "- status remains `draft`",
            "- release_phase remains `public-preview`",
            "- review_status remains `manual-review-pending`",
            "",
            "## Online URL",
            "",
            "- https://conanxin.github.io/ebook-content-lab/#/projects/second-reading-guide",
            "",
        ]
    )
    return "\n".join(lines)


def render_backlog(chapters: list[dict[str, Any]]) -> str:
    lines = [
        "# Immersive Reading Flow Backlog v0.7-A17",
        "",
        "- Later: manually refine which excerpts are core vs extra for each letter.",
        "- Later: rewrite quick/deep answers after real human review.",
        "- Later: test mobile card rhythm with reader-mode screenshots.",
        "- Later: consider true reader mode, split view, and side notes.",
        "",
        "## Letter Review Queue",
        "",
    ]
    for chapter in chapters:
        lines.append(
            f"- {chapter.get('letter_id')}: review core excerpts and quick summary for `{chapter.get('title')}`."
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", default=VERSION)
    args = parser.parse_args()
    stats = build(args.project)
    print("Built immersive reading flow")
    for key, value in stats.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
