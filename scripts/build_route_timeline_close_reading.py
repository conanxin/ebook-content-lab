#!/usr/bin/env python3
"""Build route timeline and close-reading structures for reading-guide public data."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.lib.project_paths import from_project
except ModuleNotFoundError:
    from lib.project_paths import from_project


VERSION = "v0.7-A13"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def place_name(item: dict[str, Any]) -> str:
    return str(item.get("place") or item.get("place_name") or item.get("name") or "").strip()


def short_text(value: str | None, fallback: str, limit: int = 180) -> str:
    text = (value or "").strip() or fallback
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def question_answer(question: dict[str, Any]) -> str:
    return short_text(
        question.get("answer_hint_expanded")
        or question.get("answer_hint")
        or question.get("reference_answer")
        or question.get("guide_answer"),
        "这道题的参考回答仍需人工复核；可先从路线、地点和原文线索入手。",
        260,
    )


def build_place_route_index(overview: dict[str, Any], chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    title_by_letter = {str(ch.get("letter_id")): str(ch.get("title") or "") for ch in chapters}
    order_by_letter = {str(ch.get("letter_id")): ch.get("order") for ch in chapters}
    result: list[dict[str, Any]] = []
    for item in overview.get("place_then_now", []) or []:
        name = place_name(item)
        letters = [str(value) for value in item.get("appears_in_letters") or item.get("letters") or []]
        result.append(
            {
                "place_name": name,
                "letters": letters,
                "letter_titles": [title_by_letter.get(letter, "") for letter in letters if title_by_letter.get(letter)],
                "reading_order": [order_by_letter.get(letter) for letter in letters if order_by_letter.get(letter) is not None],
                "source_status": item.get("source_status") or "needs_source_review",
                "source_type": item.get("source_type") or "unknown",
                "source_name": item.get("source_name") or "待补充公开来源",
                "source_url": item.get("source_url"),
                "today_reading": item.get("now_context") or item.get("today_reading") or "今日读法待复核。",
                "then_context": item.get("then_context") or [],
                "source_review_note": item.get("source_review_note") or "待补充公开来源",
                "updated_in": VERSION,
            }
        )
    return sorted(result, key=lambda item: (item.get("reading_order") or [999])[0])


def build_timeline_node(
    chapter: dict[str, Any],
    matched_questions: list[dict[str, Any]],
) -> dict[str, Any]:
    route_now = chapter.get("route_now", []) or []
    public_count = sum(1 for item in route_now if item.get("source_status") == "public_source")
    pending_count = sum(1 for item in route_now if item.get("source_status") != "public_source")
    places = [str(place) for place in chapter.get("places", []) or []]
    linked_question_ids = [str(q.get("question_id")) for q in matched_questions if q.get("question_id")]
    return {
        "letter_id": chapter.get("letter_id"),
        "letter_number": chapter.get("order"),
        "chapter_id": chapter.get("chapter_id"),
        "title": chapter.get("title"),
        "route_label": chapter.get("route_label") or "、".join(places),
        "primary_places": places,
        "then_context": chapter.get("route_then", {}).get("note")
        or short_text(chapter.get("source_informed_summary"), "本封信的当年旅行语境待人工复核。", 180),
        "now_context": f"本节点包含 {public_count} 个已补公开来源地点、{pending_count} 个待补来源地点。",
        "reading_mood": short_text(
            chapter.get("reading_focus_expanded") or chapter.get("theme_note") or chapter.get("reading_focus"),
            "可按路线、场景、地点和问题四层进入本封信。",
            160,
        ),
        "source_status_summary": {
            "public_source_count": public_count,
            "needs_source_review_count": pending_count,
        },
        "linked_question_ids": linked_question_ids,
        "updated_in": VERSION,
    }


def build_close_reading(chapter: dict[str, Any], matched_questions: list[dict[str, Any]]) -> dict[str, Any]:
    excerpts = chapter.get("original_excerpt", []) or []
    first_excerpt = excerpts[0] if excerpts else {}
    scenes = [str(value) for value in chapter.get("original_scene_notes", []) or []]
    places = [str(value) for value in chapter.get("places", []) or []]
    question = matched_questions[0] if matched_questions else {}
    answer = question_answer(question)
    excerpt_text = str(first_excerpt.get("excerpt") or chapter.get("source_informed_summary") or "原文线索待人工复核。")
    excerpt_note = str(first_excerpt.get("note") or "这条线索用于进入本封信的场景和路线。")
    return {
        "excerpt_focus": short_text(excerpt_text, "原文线索待人工复核。", 220),
        "why_it_matters": short_text(
            f"{excerpt_note} 它把本封信从单纯地点列表推进到具体旅行经验，适合和路线、场景、今日地点一起读。",
            "这封信的精读价值仍待人工复核。",
            260,
        ),
        "scene_to_notice": scenes[:5] or ["场景线索待人工复核。"],
        "place_to_notice": places,
        "then_now_prompt": short_text(
            chapter.get("then_now_comparison"),
            "把书中当年的到达、移动和观看方式，与今日景点化、城市化或交通化后的读法分开比较。",
            260,
        ),
        "question_bridge": question.get("question") or "本封信的对应阅读问题待人工复核。",
        "answer_bridge": answer,
        "updated_in": VERSION,
    }


def reading_steps(chapter: dict[str, Any]) -> list[str]:
    route_label = chapter.get("route_label") or "本封信路线"
    return [
        f"先看路线：把“{route_label}”当作本封信的阅读骨架。",
        "再读原文摘录或原文线索，抓住作者在路上看到、想到或停留的细节。",
        "找场景变化：注意出发、途中、抵达、山水、城市或寺庙等场景如何切换。",
        "对照今日地点：区分当年旅行经验和今天景区、城市、交通节点的读法。",
        "最后回到阅读问题，用地点线索和场景线索组织自己的回答。",
    ]


def render_plan() -> str:
    return "\n".join(
        [
            "# v0.7-A13 Route Timeline and Close Reading Plan",
            "",
            "## User Feedback",
            "",
            "- Continue improving the second reading-guide page.",
            "- Make the page readable along the journey, browsable by place, and useful for close reading letter by letter.",
            "",
            "## A13 Goals",
            "",
            "- Add a 25-node route timeline.",
            "- Add a paper-map style place route index.",
            "- Add close-reading fields for every letter card.",
            "- Link reading questions back to letters, places, route context, and close-reading answers.",
            "- Improve page rhythm without changing project status.",
            "",
            "## Personal Reading Boundary",
            "",
            "The page is a personal-reading public preview. A13 organizes already-derived excerpts, scene notes, and place information; it does not publish private source files or local paths.",
            "",
            "## No Status Promotion",
            "",
            "A13 keeps `draft`, `public-preview`, and `manual-review-pending`. Manual review remains incomplete.",
            "",
            "## A14 Suggestion",
            "",
            "A14 can add real map coordinates, mobile refinements, or start real manual review result entry.",
            "",
        ]
    )


def render_report(metrics: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Route Timeline Close Reading Report v0.7-A13",
            "",
            "## Summary",
            "",
            f"- Route timeline nodes: `{metrics['route_timeline_count']}`",
            f"- Place route index places: `{metrics['place_route_index_count']}`",
            f"- Close-reading coverage: `{metrics['close_reading_count']}`",
            f"- Reading steps coverage: `{metrics['reading_steps_count']}`",
            f"- Linked questions coverage: `{metrics['linked_questions_count']}`",
            f"- Public-source places: `{metrics['public_source_count']}`",
            f"- Needs-source-review places: `{metrics['needs_source_review_count']}`",
            "- Page UI: route timeline, paper-map route index, close-reading panels, top navigation, and linked question controls.",
            "- Local build result: to be verified by `npm run build`.",
            "",
            "## Modified File Families",
            "",
            "- `projects/second-reading-guide/public/book_overview.json`",
            "- `projects/second-reading-guide/public/chapter_reading_cards.json`",
            "- `projects/second-reading-guide/public/reading_questions.json`",
            "- `web/public/projects/second-reading-guide/*.json` mirrors",
            "- `web/src/pages/ReadingGuideProjectPage.tsx`",
            "- `web/src/types/readingGuide.ts`",
            "- `web/src/styles.css`",
            "",
            "## Boundary Check",
            "",
            "- Project remains draft / public-preview / manual-review-pending.",
            "- Manual review CSV was not edited.",
            "- Private source files are not published.",
            "- No status promotion was applied.",
            "",
            "## Online URL",
            "",
            "- https://conanxin.github.io/ebook-content-lab/#/projects/second-reading-guide",
            "",
        ]
    )


def render_backlog(metrics: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Route Timeline Backlog v0.7-A13",
            "",
            "## Map and Timeline",
            "",
            "- Add verified coordinates for major places before drawing a real map.",
            "- Add a compact mobile timeline mode if the 25-node view becomes dense.",
            "- Consider grouping route nodes by travel phase after manual review.",
            "",
            "## Place Sources",
            "",
            f"- Remaining needs-source-review places: `{metrics['needs_source_review_count']}`.",
            "- Replace encyclopedia fallback sources with official tourism, museum, government, or heritage pages where possible.",
            "",
            "## Close Reading",
            "",
            "- Manually refine original excerpts and excerpt explanations.",
            "- Rewrite answers that are still too structural after human reading.",
            "- Add page/section pointers if a future compliant source locator is available.",
            "",
            "## Mobile Experience",
            "",
            "- Test timeline scrolling and card expansion on narrow screens.",
            "- Add a reading-mode toggle if the page becomes visually busy.",
            "",
        ]
    )


def build(project: str) -> dict[str, Any]:
    paths = from_project(project)
    overview = read_json(paths.book_overview_json)
    cards_data = read_json(paths.chapter_reading_cards_json)
    questions_data = read_json(paths.reading_questions_json)

    chapters = cards_data.get("chapters", [])
    questions = questions_data.get("questions", [])
    questions_by_letter: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for question in questions:
        if question.get("letter_id"):
            questions_by_letter[str(question["letter_id"])].append(question)

    timeline: list[dict[str, Any]] = []
    for chapter in chapters:
        letter_id = str(chapter.get("letter_id") or "")
        matched = questions_by_letter.get(letter_id, [])
        node = build_timeline_node(chapter, matched)
        close = build_close_reading(chapter, matched)
        steps = reading_steps(chapter)

        chapter["timeline_node"] = node
        chapter["close_reading"] = close
        chapter["reading_steps"] = steps
        chapter["linked_questions"] = [q.get("question_id") for q in matched if q.get("question_id")]
        timeline.append(node)

    chapter_by_letter = {str(ch.get("letter_id")): ch for ch in chapters}
    for question in questions:
        if question.get("scope") == "book":
            question["linked_letters"] = [str(ch.get("letter_id")) for ch in chapters if ch.get("letter_id")]
            question["route_context"] = "全书问题关联 25 封旅行书信，可先按路线时间线顺读，再回到地点索引比较。"
            question["place_context"] = "覆盖全书地点线索；重点看已补公开来源与待补来源如何分布。"
            question["then_now_context"] = overview.get("then_now_summary")
            question["close_reading_answer"] = question_answer(question)
            question["answer_steps"] = [
                "先按 25 个时间线节点重建旅行顺序。",
                "再观察哪些地点已有公开来源，哪些仍待复核。",
                "最后用章节卡中的摘录、场景和今日对照组织回答。",
            ]
        else:
            letter_id = str(question.get("letter_id") or "")
            chapter = chapter_by_letter.get(letter_id, {})
            question["linked_letters"] = [letter_id] if letter_id else []
            question["route_context"] = chapter.get("route_label") or "本题关联路线语境待复核。"
            question["place_context"] = "、".join(chapter.get("places", []) or []) or "地点线索待复核。"
            question["then_now_context"] = chapter.get("then_now_comparison") or "昔日 / 今日对照待复核。"
            question["close_reading_answer"] = short_text(
                chapter.get("answer_hint_expanded") or question_answer(question),
                "本题可结合本封信的路线、原文线索和地点对照回答。",
                320,
            )
            question["answer_steps"] = [
                "回到对应信封卡，先看路线标签和主要地点。",
                "读原文摘录或原文线索，找出场景转换。",
                "对照今日地点来源状态，区分可确认和待复核内容。",
                "用这些线索补充或修正自己的参考回答。",
            ]
        question["updated_in"] = VERSION

    place_route_index = build_place_route_index(overview, chapters)
    overview["route_timeline"] = timeline
    overview["place_route_index"] = place_route_index
    overview["route_overview"] = {
        "summary": "A13 将 25 封信组织成可顺读的旅行路线时间线，并把地点聚合成地图式索引。",
        "reading_method": "先看时间线，再看地点索引，最后展开信封卡做原文精读。",
        "then_now_note": overview.get("then_now_summary"),
        "updated_in": VERSION,
    }
    overview["close_reading_overview"] = {
        "method": "按“摘录或原文线索 → 场景 → 地点 → 昔日/今日对照 → 问题 → 回答”的顺序精读。",
        "scope": "覆盖 25 封旅行书信；当前仍是公开预览与人工复核阶段。",
        "updated_in": VERSION,
    }
    overview.setdefault("source_enrichment", {})["route_timeline_close_reading"] = {
        "version": VERSION,
        "route_timeline_count": len(timeline),
        "place_route_index_count": len(place_route_index),
        "close_reading_count": sum(1 for ch in chapters if ch.get("close_reading")),
        "reading_steps_count": sum(1 for ch in chapters if ch.get("reading_steps")),
        "question_linkage_count": sum(1 for q in questions if q.get("linked_letters") or q.get("route_context") or q.get("close_reading_answer")),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    payloads = {
        "book_overview.json": overview,
        "chapter_reading_cards.json": cards_data,
        "key_concepts.json": read_json(paths.key_concepts_json),
        "quote_index.json": read_json(paths.quote_index_json),
        "reading_questions.json": questions_data,
    }
    for name, payload in payloads.items():
        write_json(paths.public_path(name), payload)
        write_json(paths.web_project_path(name), payload)

    places = overview.get("place_then_now", []) or []
    metrics = {
        "route_timeline_count": len(timeline),
        "place_route_index_count": len(place_route_index),
        "close_reading_count": sum(1 for ch in chapters if ch.get("close_reading")),
        "reading_steps_count": sum(1 for ch in chapters if ch.get("reading_steps")),
        "linked_questions_count": sum(1 for q in questions if q.get("linked_letters") or q.get("route_context") or q.get("close_reading_answer")),
        "public_source_count": sum(1 for item in places if item.get("source_status") == "public_source"),
        "needs_source_review_count": sum(1 for item in places if item.get("source_status") == "needs_source_review"),
    }

    paths.report_path("v0.7_a13_route_timeline_close_reading_plan.md").write_text(render_plan(), encoding="utf-8")
    paths.report_path("route_timeline_close_reading_report_v0.7_a13.md").write_text(render_report(metrics), encoding="utf-8")
    paths.report_path("route_timeline_backlog_v0.7_a13.md").write_text(render_backlog(metrics), encoding="utf-8")
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    metrics = build(args.project)
    print("A13 route timeline and close reading built")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
