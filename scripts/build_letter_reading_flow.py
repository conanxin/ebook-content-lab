#!/usr/bin/env python3
"""Build v0.7-A15 letter-first reading-flow fields.

This pass does not read private source files. It reorganizes the existing
public-preview reading-guide data so the page can render 25 coherent letter
reading units instead of scattering related facts across separate modules.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.lib.project_paths import from_project
except ModuleNotFoundError:
    from lib.project_paths import from_project


VERSION = "v0.7-A15"
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


def first_sentence(text: str | None, limit: int = 120) -> str:
    if not text:
        return "本封信的导读摘要仍待人工复核。"
    normalized = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[。！？!?])", normalized, maxsplit=1)
    sentence = (parts[0] if parts else normalized).strip()
    return sentence[:limit]


def join(values: list[str] | None, fallback: str = "待人工复核") -> str:
    values = [value for value in values or [] if value]
    return "、".join(values) if values else fallback


def reading_length_hint(char_count: int | None, chunk_count: int | None) -> str:
    if chunk_count and chunk_count >= 6:
        return "篇幅较长，适合分两次阅读。"
    if char_count and char_count >= 4500:
        return "信息密度较高，建议按场景分段阅读。"
    if char_count and char_count <= 2200:
        return "篇幅较短，适合先快速顺读。"
    return "中等篇幅，适合按路线和地点线索阅读。"


def source_status_label(status: str | None) -> str:
    if status == "public_source":
        return "已有公开来源"
    return "待补充公开来源"


def coordinate_status_label(status: str | None) -> str:
    if status == "public_coordinate":
        return "已有公开坐标"
    if status == "approximate_coordinate":
        return "近似坐标"
    return "坐标待复核"


def place_name(place: dict[str, Any]) -> str:
    return place.get("place") or place.get("place_name") or place.get("name") or "地点待复核"


def route_roles(places: list[dict[str, Any]]) -> dict[str, str]:
    roles: dict[str, str] = {}
    names = [place_name(place) for place in places]
    for index, name in enumerate(names):
        if len(names) == 1:
            roles[name] = "核心地点"
        elif index == 0:
            roles[name] = "起点或进入地点"
        elif index == len(names) - 1:
            roles[name] = "抵达或收束地点"
        else:
            roles[name] = "途经或观察地点"
    return roles


def build_source_clues(chapter: dict[str, Any]) -> list[dict[str, str]]:
    clues: list[dict[str, str]] = []
    for index, item in enumerate(chapter.get("original_excerpt") or [], start=1):
        excerpt = str(item.get("excerpt") or "").strip()
        if not excerpt:
            continue
        clues.append(
            {
                "clue_id": f"{chapter.get('letter_id', 'letter')}-clue-{index:02d}",
                "mode": item.get("mode") or "short_original_clue",
                "excerpt": excerpt,
                "note": item.get("note") or "用于定位本封信的场景和语气，不作为全文替代。",
                "use": "先读这一小段，再看下方的场景和地点说明。",
            }
        )

    close = chapter.get("close_reading") or {}
    scene_notes = chapter.get("original_scene_notes") or []
    route_label = chapter.get("route_label") or join(chapter.get("places"))
    additions = [
        (
            "structured_reading_clue",
            close.get("excerpt_focus") or f"标题和路线把本封信放在“{route_label}”这一段旅程中。",
            "结构化原文线索：用于提示本封信的阅读焦点。",
            "用来看本封信如何从标题、场景和地点进入旅行叙事。",
        ),
        (
            "scene_clue",
            scene_notes[0] if scene_notes else f"本封信的核心场景围绕 {route_label} 展开。",
            "场景线索：帮助读者在不阅读整章全文的情况下抓住叙事位置。",
            "用来看出发、途中、抵达或观看方式的转换。",
        ),
        (
            "place_clue",
            f"地点线索：{join((chapter.get('places') or [])[:5])}。",
            "地点线索：把短摘和今日景点说明连接起来。",
            "用来对照下方的昔日旅程与今日读法。",
        ),
    ]
    for mode, excerpt, note, use in additions:
        if len(clues) >= 4:
            break
        if excerpt and all(str(clue.get("excerpt")) != str(excerpt) for clue in clues):
            clues.append(
                {
                    "clue_id": f"{chapter.get('letter_id', 'letter')}-clue-{len(clues) + 1:02d}",
                    "mode": mode,
                    "excerpt": str(excerpt)[:180],
                    "note": note,
                    "use": use,
                }
            )
    return clues[:4]


def find_question(chapter: dict[str, Any], questions: list[dict[str, Any]]) -> dict[str, Any] | None:
    letter_id = chapter.get("letter_id")
    for question in questions:
        if question.get("letter_id") == letter_id:
            return question
        if letter_id and letter_id in (question.get("linked_letters") or []) and question.get("scope") == "letter":
            return question
    for question in questions:
        if question.get("question_id", "").endswith(f"{int(chapter.get('order') or 0):03d}"):
            return question
    return None


def build_embedded_places(chapter: dict[str, Any]) -> list[dict[str, Any]]:
    route_now = chapter.get("route_now") or []
    roles = route_roles(route_now)
    embedded = []
    for place in route_now[:5]:
        name = place_name(place)
        embedded.append(
            {
                "place_name": name,
                "role": roles.get(name, "地点线索"),
                "then_perspective": join(place.get("then_context"), chapter.get("route_then", {}).get("note") or "书信中的旅行语境待复核"),
                "today_perspective": place.get("now_context")
                or place.get("today_reading")
                or "今日景点信息待公开来源复核。",
                "source_status": place.get("source_status") or "needs_source_review",
                "source_label": source_status_label(place.get("source_status")),
                "source_name": place.get("source_name"),
                "source_url": place.get("source_url"),
                "coordinate_status": place.get("coordinate_status") or "needs_coordinate_review",
                "coordinate_label": coordinate_status_label(place.get("coordinate_status")),
                "review_note": place.get("source_review_note")
                or place.get("coordinate_review_note")
                or "待后续人工复核。",
            }
        )
    if not embedded:
        for name in (chapter.get("places") or [])[:3]:
            embedded.append(
                {
                    "place_name": name,
                    "role": "地点线索",
                    "then_perspective": chapter.get("route_then", {}).get("note") or "书信中的旅行语境待复核。",
                    "today_perspective": "今日景点信息待公开来源复核。",
                    "source_status": "needs_source_review",
                    "source_label": "待补充公开来源",
                    "coordinate_status": "needs_coordinate_review",
                    "coordinate_label": "坐标待复核",
                    "review_note": "待后续人工复核。",
                }
            )
    return embedded


def build_letter_unit(chapter: dict[str, Any], question: dict[str, Any] | None) -> dict[str, Any]:
    source_clues = build_source_clues(chapter)
    embedded_places = build_embedded_places(chapter)
    close = chapter.get("close_reading") or {}
    route_then = chapter.get("route_then") or {}
    guide = first_sentence(chapter.get("source_informed_summary") or chapter.get("letter_summary") or chapter.get("summary"), 150)
    question_answer = {
        "question_id": question.get("question_id") if question else None,
        "question": question.get("question") if question else "本封信的阅读问题待人工复核。",
        "reference_answer": (
            question.get("close_reading_answer")
            or question.get("answer_hint_expanded")
            or question.get("answer_hint")
            or chapter.get("answer_hint_expanded")
            or "参考回答待人工复核。"
        )
        if question
        else chapter.get("answer_hint_expanded") or "参考回答待人工复核。",
        "answer_steps": (question.get("answer_steps") if question else None)
        or [
            "先确认本封信的路线和核心地点。",
            "再读原文线索，找出场景和情绪变化。",
            "最后把今日景点说明放回问题中回答。",
        ],
        "basis": "基于原书线索、地点说明、结构化导读与公开来源状态整理，待人工复核。",
    }

    return {
        "version": VERSION,
        "letter_number": chapter.get("order"),
        "letter_id": chapter.get("letter_id"),
        "section_id": chapter.get("section_id"),
        "date_or_stamp": chapter.get("letter_stamp") or "日期待复核",
        "route_title": chapter.get("title") or chapter.get("route_label"),
        "one_sentence_guide": guide,
        "themes": chapter.get("themes") or [],
        "basic_info": {
            "route": chapter.get("route_label") or join(chapter.get("places")),
            "core_places": (chapter.get("places") or [])[:5],
            "chunk_count": chapter.get("chunk_count"),
            "char_count": chapter.get("char_count"),
            "reading_length_hint": reading_length_hint(chapter.get("char_count"), chapter.get("chunk_count")),
            "what_to_watch": chapter.get("reading_focus_expanded") or chapter.get("reading_focus") or "看地点、场景和旅行节奏如何变化。",
        },
        "source_clues": source_clues,
        "close_reading_flow": {
            "what_it_says": chapter.get("source_informed_summary") or chapter.get("letter_summary") or chapter.get("summary"),
            "why_it_matters": close.get("why_it_matters") or chapter.get("reading_focus_expanded") or chapter.get("reading_focus"),
            "reading_steps": chapter.get("reading_steps")
            or [
                "先看路线和地点。",
                "再读原文线索。",
                "接着看今昔对照。",
                "最后回答阅读问题。",
            ],
            "changes_to_notice": close.get("then_now_prompt") or chapter.get("then_now_comparison") or "今昔变化待继续复核。",
        },
        "embedded_places": embedded_places,
        "question_answer": question_answer,
        "secondary_details": {
            "scene_notes": chapter.get("original_scene_notes") or [],
            "then_route_note": route_then.get("note"),
            "then_now_comparison": chapter.get("then_now_comparison"),
            "evidence_refs": chapter.get("evidence_refs") or [],
            "review_notice": chapter.get("review_notice")
            or "公开预览 / 个人阅读增强版：本封信仍待人工复核。",
        },
    }


def enrich(project: str) -> dict[str, int]:
    paths = from_project(project)
    overview = read_json(paths.book_overview_json)
    chapter_data = read_json(paths.chapter_reading_cards_json)
    questions_data = read_json(paths.reading_questions_json)
    questions = questions_data.get("questions", [])
    chapters = chapter_data.get("chapters", [])

    enhanced_questions = 0
    for chapter in chapters:
        question = find_question(chapter, questions)
        unit = build_letter_unit(chapter, question)
        chapter["letter_reading_unit"] = unit
        chapter["original_excerpt"] = unit["source_clues"]
        chapter["letter_reading_flow_ready"] = True
        chapter["embedded_place_count"] = len(unit["embedded_places"])
        chapter["updated_in"] = VERSION
        if question:
            question["letter_anchor"] = chapter.get("chapter_id")
            question["answer_summary"] = first_sentence(unit["question_answer"]["reference_answer"], 150)
            question["basis"] = "基于原书线索、地点说明、结构化导读与公开来源状态整理，待人工复核。"
            question["updated_in"] = VERSION
            enhanced_questions += 1

    overview["page_redesign"] = {
        "version": VERSION,
        "mode": "letter-reading-flow",
        "main_axis": "25封书信",
        "layout": "single-column-reading-flow",
        "goal": "把原文线索、精读步骤、地点今昔对照和阅读问题集中回每封信内部。",
    }
    overview["letter_reading_flow_summary"] = {
        "letter_units": len(chapters),
        "source_clue_ready": sum(1 for chapter in chapters if len(chapter.get("letter_reading_unit", {}).get("source_clues", [])) >= 3),
        "embedded_places_ready": sum(1 for chapter in chapters if chapter.get("letter_reading_unit", {}).get("embedded_places")),
        "question_answer_ready": sum(1 for chapter in chapters if chapter.get("letter_reading_unit", {}).get("question_answer", {}).get("reference_answer")),
        "updated_in": VERSION,
    }
    overview["navigation_model"] = {
        "version": VERSION,
        "anchors": ["概览", "25封书信", "路线时间线", "地点索引", "阅读问题"],
        "note": "附属模块后置，主阅读流按 letter-001 到 letter-025 顺读。",
    }

    generated_at = datetime.now(timezone.utc).isoformat()
    for payload in [overview, chapter_data, questions_data]:
        payload["generated_at"] = generated_at
        payload["status"] = "draft"
        payload["release_phase"] = "public-preview"
        payload["review_status"] = "manual-review-pending"

    write_json(paths.book_overview_json, overview)
    write_json(paths.chapter_reading_cards_json, chapter_data)
    write_json(paths.reading_questions_json, questions_data)
    for name in PUBLIC_FILES:
        shutil.copyfile(paths.public_path(name), paths.web_project_path(name))

    stats = {
        "letter_units": len(chapters),
        "source_clue_ready": overview["letter_reading_flow_summary"]["source_clue_ready"],
        "embedded_places_ready": overview["letter_reading_flow_summary"]["embedded_places_ready"],
        "question_answer_ready": overview["letter_reading_flow_summary"]["question_answer_ready"],
        "enhanced_questions": enhanced_questions,
    }

    plan = paths.report_path("v0.7_a15_letter_reading_flow_plan.md")
    plan.write_text(
        "\n".join(
            [
                "# v0.7-A15 Letter Reading Flow Plan",
                "",
                "## Goal",
                "",
                "Rebuild the second-reading-guide page around the 25 letters as the main reading flow.",
                "",
                "## Changes",
                "",
                "- Add `letter_reading_unit` to each chapter card.",
                "- Move excerpts, close reading, embedded places, and question answers into each letter unit.",
                "- Keep global route timeline, place index, and question overview as supplemental modules.",
                "- Preserve `draft`, `public-preview`, and `manual-review-pending` status.",
                "",
                "## Boundaries",
                "",
                "- No private source files are read or published by this builder.",
                "- No manual review result is changed.",
                "- No reviewed/final promotion is performed.",
                "",
                "## Follow-up",
                "",
                "A16 can refine per-letter copy after real reading feedback or manual review.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    report = paths.report_path("letter_reading_flow_report_v0.7_a15.md")
    report.write_text(render_report(stats), encoding="utf-8")
    backlog = paths.report_path("letter_reading_flow_backlog_v0.7_a15.md")
    backlog.write_text(render_backlog(chapters), encoding="utf-8")
    return stats


def render_report(stats: dict[str, int]) -> str:
    return "\n".join(
        [
            "# Letter Reading Flow Report v0.7-A15",
            "",
            "## Summary",
            "",
            f"- Letter units: `{stats['letter_units']}`",
            f"- Source clue coverage: `{stats['source_clue_ready']}`",
            f"- Embedded place coverage: `{stats['embedded_places_ready']}`",
            f"- Question answer coverage: `{stats['question_answer_ready']}`",
            f"- Enhanced reading questions: `{stats['enhanced_questions']}`",
            "",
            "## Public Preview State",
            "",
            "- status remains `draft`",
            "- release_phase remains `public-preview`",
            "- review_status remains `manual-review-pending`",
            "",
            "## Boundary",
            "",
            "- No private source path is exported.",
            "- No manual review result is changed.",
            "- The page remains a personal-reading public preview, not a final reviewed edition.",
            "",
            "## Online URL",
            "",
            "- https://conanxin.github.io/ebook-content-lab/#/projects/second-reading-guide",
            "",
        ]
    )


def render_backlog(chapters: list[dict[str, Any]]) -> str:
    lines = [
        "# Letter Reading Flow Backlog v0.7-A15",
        "",
        "Items for later human refinement:",
        "",
    ]
    for chapter in chapters:
        unit = chapter.get("letter_reading_unit", {})
        source_modes = Counter(clue.get("mode") for clue in unit.get("source_clues", []))
        lines.append(
            f"- letter-{int(chapter.get('order') or 0):03d}: refine original clues and place prose; source clue modes: {dict(source_modes)}"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", default=VERSION)
    args = parser.parse_args()
    stats = enrich(args.project)
    print("Built A15 letter reading flow")
    for key, value in stats.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
