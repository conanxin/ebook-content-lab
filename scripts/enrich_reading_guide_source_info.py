#!/usr/bin/env python3
"""Build source-informed public-preview enrichment for the reading-guide project.

The script reads local source-derived working material, but writes only curated
guide summaries, short clues, and place comparison metadata to public outputs.
It never writes source-layer file names or local paths into public JSON.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.lib.project_paths import from_project
except ModuleNotFoundError:
    from lib.project_paths import from_project


PUBLIC_FILES = [
    "book_overview.json",
    "chapter_reading_cards.json",
    "key_concepts.json",
    "quote_index.json",
    "reading_questions.json",
]

SCENE_GROUPS: list[tuple[str, list[str], str]] = [
    ("交通", ["车", "站", "火车", "隧道", "桥", "路", "船", "航"], "交通与移动方式"),
    ("山水", ["山", "峰", "岭", "瀑", "溪", "江", "河", "湖", "海"], "山水地貌与自然景观"),
    ("古迹", ["寺", "祠", "碑", "亭", "阁", "陵", "园", "书院", "佛", "塔"], "历史建筑与文化遗迹"),
    ("城市", ["城", "街", "市", "大学", "车站", "饭店"], "城市空间与停留节点"),
    ("途中", ["夜", "宿", "饭", "雨", "风", "雾", "晨", "暮"], "旅途时间、天气与日常经验"),
]

PLACE_SOURCES: dict[str, dict[str, str]] = {
    "青城山": {
        "source_name": "UNESCO World Heritage Centre - Mount Qingcheng and the Dujiangyan Irrigation System",
        "source_url": "https://whc.unesco.org/en/list/1001/",
        "today_reading": "今日可按世界遗产语境中的道教名山与历史景观来理解，实际游览信息仍需查当日官方公告。",
    },
    "乐山大佛": {
        "source_name": "UNESCO World Heritage Centre - Mount Emei Scenic Area, including Leshan Giant Buddha Scenic Area",
        "source_url": "https://whc.unesco.org/en/list/779/",
        "today_reading": "今日多被理解为峨眉山-乐山大佛遗产景观的一部分，和当年行旅中的山水、佛教场景形成对照。",
    },
    "峨嵋山脚": {
        "source_name": "UNESCO World Heritage Centre - Mount Emei Scenic Area, including Leshan Giant Buddha Scenic Area",
        "source_url": "https://whc.unesco.org/en/list/779/",
        "today_reading": "今日可按峨眉山遗产景区外围和登山入口语境理解，具体线路与交通需另查现行信息。",
    },
    "石林": {
        "source_name": "UNESCO World Heritage Centre - South China Karst",
        "source_url": "https://whc.unesco.org/en/list/1248/",
        "today_reading": "今日可按喀斯特自然景观和景区化游览节点理解，和书信中的途中观看经验形成对照。",
    },
    "鼓浪屿": {
        "source_name": "UNESCO World Heritage Centre - Kulangsu, a Historic International Settlement",
        "source_url": "https://whc.unesco.org/en/list/1541/",
        "today_reading": "今日可按历史国际社区与城市文化景观理解，适合和书信中的海岛、城市经验对读。",
    },
    "黄山天都峰排云亭": {
        "source_name": "UNESCO World Heritage Centre - Mount Huangshan",
        "source_url": "https://whc.unesco.org/en/list/547/",
        "today_reading": "今日可按黄山世界遗产和山岳景区语境理解，登临条件需以现行景区公告为准。",
    },
    "苏州园林": {
        "source_name": "UNESCO World Heritage Centre - Classical Gardens of Suzhou",
        "source_url": "https://whc.unesco.org/en/list/813/",
        "today_reading": "今日可按古典园林遗产景观理解，适合和书信中的城市、园林审美经验对读。",
    },
    "苏州天平山沧浪亭": {
        "source_name": "UNESCO World Heritage Centre - Classical Gardens of Suzhou",
        "source_url": "https://whc.unesco.org/en/list/813/",
        "today_reading": "今日可按苏州园林与山水游览线索综合理解，具体地点开放状态需另查现行信息。",
    },
    "泉州": {
        "source_name": "UNESCO World Heritage Centre - Quanzhou: Emporium of the World in Song-Yuan China",
        "source_url": "https://whc.unesco.org/en/list/1561/",
        "today_reading": "今日可按海上贸易城市和历史遗产节点理解，和书信中的沿海行旅形成对照。",
    },
}


@dataclass
class BuildStats:
    chapters: int = 0
    source_summaries: int = 0
    excerpts: int = 0
    scene_notes: int = 0
    then_now: int = 0
    questions: int = 0
    question_answers: int = 0
    source_covered_places: int = 0
    needs_source_review_places: int = 0
    needs_source_review_chapters: int = 0


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_section_texts(project_dir: Path) -> dict[str, str]:
    # Local source-derived files are read but never named in public outputs.
    sections = read_jsonl(project_dir / "private" / "book_sections.jsonl")
    texts: dict[str, str] = {}
    for row in sections:
        section_id = str(row.get("section_id") or "")
        text = str(row.get("text") or "")
        if section_id and text:
            texts[section_id] = text
    return texts


def clean_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def split_sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", "", text or "")
    parts = re.split(r"(?<=[。！？；])", cleaned)
    return [part for part in parts if len(part) >= 12]


def scene_tags(text: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for label, keys, note in SCENE_GROUPS:
        if any(key in text for key in keys):
            found.append((label, note))
    return found


def pick_excerpts(text: str, places: list[str], title: str) -> list[dict[str, str]]:
    cleaned = clean_text(text)
    probes = [place for place in places if place] + [key for _, keys, _ in SCENE_GROUPS for key in keys]
    snippets: list[str] = []
    for probe in probes:
        index = cleaned.find(probe)
        if index < 0:
            continue
        start = max(0, index - 10)
        end = min(len(cleaned), index + len(probe) + 16)
        snippet = cleaned[start:end]
        if len(snippet) > 42:
            snippet = snippet[:42]
        if snippet and snippet not in snippets:
            snippets.append(snippet)
        if len(snippets) >= 2:
            break
    if not snippets:
        snippets = [title[:28]]
    return [
        {
            "excerpt": snippet,
            "note": "用于定位本封信的场景和语气，不作为全文替代。",
            "mode": "short_original_clue",
        }
        for snippet in snippets[:2]
    ]


def build_scene_notes(text: str, places: list[str], themes: list[str], title: str) -> list[str]:
    tags = scene_tags(text)
    notes = [f"原书信息中可见{note}线索，适合作为细读入口。" for _, note in tags[:4]]
    if places:
        notes.append(f"标题和正文线索把{ '、'.join(places[:4]) }组织成本封信的空间骨架。")
    if themes:
        notes.append(f"结构主题提示读者关注{ '、'.join(themes[:3]) }。")
    if not notes:
        notes.append(f"本封信以“{title}”为主要定位，具体场景仍待人工复核。")
    deduped: list[str] = []
    for note in notes:
        if note not in deduped:
            deduped.append(note)
    while len(deduped) < 3:
        deduped.append("本条导读仍处于公开预览阶段，需要回到原书继续校订。")
    return deduped[:6]


def today_reading_for(place: str) -> dict[str, Any]:
    if place in PLACE_SOURCES:
        source = PLACE_SOURCES[place]
        return {
            "name": place,
            "today_reading": source["today_reading"],
            "source_status": "public_source",
            "source_name": source["source_name"],
            "source_url": source["source_url"],
            "review_status": "needs_field_check",
        }
    if any(key in place for key in ["山", "峰", "岭", "瀑"]):
        category = "自然景观或山岳游览节点"
    elif any(key in place for key in ["寺", "祠", "碑", "亭", "阁", "陵", "园", "书院", "佛", "关"]):
        category = "历史文化或遗址景观节点"
    elif any(key in place for key in ["江", "河", "溪", "湖", "海"]):
        category = "水系或滨水景观节点"
    elif any(key in place for key in ["站", "线", "桥", "隧道", "车站"]):
        category = "交通节点"
    else:
        category = "城市或地名节点"
    return {
        "name": place,
        "today_reading": f"今日可暂按{category}理解；具体景点状态、开放信息和交通条件待公开来源复核。",
        "source_status": "needs_source_review",
        "source_name": "待补充公开来源",
        "source_url": None,
        "review_status": "needs_source_review",
    }


def enrich_chapters(cards: dict[str, Any], section_texts: dict[str, str]) -> tuple[dict[str, Any], list[dict[str, Any]], BuildStats]:
    stats = BuildStats()
    place_rows: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for chapter in cards.get("chapters", []):
        stats.chapters += 1
        section_id = chapter.get("section_id")
        text = section_texts.get(str(section_id), "")
        places = list(chapter.get("places") or [])
        themes = list(chapter.get("themes") or [])
        title = str(chapter.get("title") or "本封书信")
        char_count = chapter.get("char_count") or len(text)
        paragraph_count = chapter.get("paragraph_count") or 0
        tags = scene_tags(text)
        tag_labels = [label for label, _ in tags] or ["行旅"]
        route = " → ".join(places) if places else "地点线索待复核"

        chapter["source_enrichment_status"] = "source-enriched-public-preview"
        chapter["source_informed_summary"] = (
            f"这封信围绕“{title}”展开，原书信息显示它不是单纯的地名列表，而是把{route}放进一次具体行旅中。"
            f"本封约 {char_count} 字、{paragraph_count} 个段落，场景线索集中在{ '、'.join(tag_labels[:4]) }。"
            f"读者可以先看地点移动，再看作者如何把途中所见、停留节点和主题感受组织成一封旅行书信。"
        )
        chapter["original_excerpt"] = pick_excerpts(text, places, title)
        chapter["original_scene_notes"] = build_scene_notes(text, places, themes, title)
        chapter["route_then"] = {
            "places": places,
            "route_label": route,
            "note": "当年旅行路径按标题、正文地点线索和结构化导读整理，仍待人工复核。",
        }
        route_now = [today_reading_for(place) for place in places]
        chapter["route_now"] = route_now
        needs_review = any(item["source_status"] == "needs_source_review" for item in route_now)
        chapter["needs_source_review"] = needs_review
        if needs_review:
            stats.needs_source_review_chapters += 1
        chapter["then_now_comparison"] = (
            "当年书信更强调移动中的观看和停留；今天读者往往会通过景区、城市节点或交通节点重新理解这些地点。"
            "已列公开来源的地点可先作现代参照，未列来源的地点只作为待复核的今日读法。"
        )
        chapter["reading_focus_expanded"] = (
            f"细读时先抓住{route}这条空间线，再观察{ '、'.join(themes[:3]) if themes else '主题线索' }"
            "如何改变作者对途中景物、城市和时间的感受。"
        )
        chapter["answer_hint_expanded"] = (
            f"参考回答：本封信可以从{route}进入，结合原书中的{ '、'.join(tag_labels[:3]) }线索，"
            "把地点理解为旅行经验的组织方式，而不是孤立景点清单。"
        )
        chapter["review_notice"] = "公开预览 / 个人阅读增强版：摘录、地点说明和今日对照仍待人工复核。"

        if chapter.get("source_informed_summary"):
            stats.source_summaries += 1
        if chapter.get("original_excerpt"):
            stats.excerpts += 1
        if chapter.get("original_scene_notes"):
            stats.scene_notes += 1
        if chapter.get("then_now_comparison") and chapter.get("route_now"):
            stats.then_now += 1

        for item in route_now:
            name = item["name"]
            if name not in place_rows:
                place_rows[name] = {
                    "place": name,
                    "letters": [],
                    "then_context": [],
                    "today_reading": item["today_reading"],
                    "source_status": item["source_status"],
                    "source_name": item["source_name"],
                    "source_url": item["source_url"],
                    "review_status": item["review_status"],
                }
            place_rows[name]["letters"].append(chapter.get("letter_id"))
            place_rows[name]["then_context"].append(title)

    for row in place_rows.values():
        if row["source_status"] == "public_source":
            stats.source_covered_places += 1
        else:
            stats.needs_source_review_places += 1
    return cards, list(place_rows.values()), stats


def enrich_questions(questions: dict[str, Any], chapters: list[dict[str, Any]]) -> tuple[dict[str, Any], int]:
    by_section = {chapter.get("section_id"): chapter for chapter in chapters}
    enhanced = 0
    for question in questions.get("questions", []):
        if question.get("scope") == "book":
            question["answer_hint_expanded"] = (
                "参考回答：这本书可以看作一组按行程推进的旅行书信。读者可以先看地点从北方关隘、关中城市、"
                "西南山水、东南沿海一路展开，再看作者如何在不同景观中调整观看方式。这个回答仍是导读提示。"
            )
            question["source_clues"] = ["25 封书信标题", "章节地点线索", "结构化主题"]
            question["place_clues"] = []
            question["then_now_hint"] = "全书的今日对照应按每封信的地点分别核验。"
        else:
            chapter = by_section.get(question.get("section_id"))
            if chapter:
                places = chapter.get("places") or []
                scene_notes = chapter.get("original_scene_notes") or []
                route = chapter.get("route_label") or "地点线索"
                question["answer_hint_expanded"] = (
                    f"参考回答：可先把{route}作为空间顺序，再结合原书场景线索"
                    f"（如{ '；'.join(scene_notes[:2]) }）理解这封信。今日对照应优先看已列公开来源，"
                    "未列来源的地点只作待复核提示。"
                )
                question["source_clues"] = scene_notes[:3]
                question["place_clues"] = places
                question["then_now_hint"] = chapter.get("then_now_comparison")
            else:
                question["answer_hint_expanded"] = "参考回答：先从对应章节标题、地点线索和主题标签入手；具体解释待人工复核。"
                question["source_clues"] = []
                question["place_clues"] = []
                question["then_now_hint"] = "今日对照待补充。"
        question["basis"] = "基于原书信息、地点线索、结构摘要与公开导读信息生成，待人工复核。"
        question["review_notice"] = "公开预览 / 个人阅读增强版：参考回答不是最终标准答案。"
        if question.get("answer_hint_expanded"):
            enhanced += 1
    return questions, enhanced


def write_place_report(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Place Then/Now Sources v0.7-A11",
        "",
        "| place | letters | today source status | source | review status |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        letters = ", ".join(str(item) for item in row["letters"] if item)
        source = row["source_name"]
        if row.get("source_url"):
            source = f"[{source}]({row['source_url']})"
        lines.append(
            f"| {row['place']} | {letters} | {row['source_status']} | {source} | {row['review_status']} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_report(path: Path, stats: BuildStats, place_rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Source Enrichment Report v0.7-A11",
        "",
        "## Summary",
        "",
        "- Page URL: `https://conanxin.github.io/ebook-content-lab/#/projects/second-reading-guide`",
        "- Status remains: `draft`",
        "- Release phase remains: `public-preview`",
        "- Review status remains: `manual-review-pending`",
        "",
        "## Coverage",
        "",
        f"- Chapter cards: `{stats.chapters}`",
        f"- Source-informed summaries: `{stats.source_summaries}`",
        f"- Original excerpt / clue coverage: `{stats.excerpts}`",
        f"- Original scene notes coverage: `{stats.scene_notes}`",
        f"- Then/now comparison coverage: `{stats.then_now}`",
        f"- Reading questions: `{stats.questions}`",
        f"- Enhanced answer coverage: `{stats.question_answers}`",
        f"- Places with public source coverage: `{stats.source_covered_places}`",
        f"- Places needing source review: `{stats.needs_source_review_places}`",
        f"- Chapters containing at least one place needing source review: `{stats.needs_source_review_chapters}`",
        "",
        "## Changed Areas",
        "",
        "- Enriched the 25 letter cards with source-informed summaries, original clues, scene notes, route-then and route-now fields.",
        "- Enriched all reading questions with expanded answer hints.",
        "- Added place comparison data to the book overview.",
        "- Kept all public data in draft public preview state.",
        "",
        "## Boundary",
        "",
        "- No source book files are published.",
        "- No source-layer paths are written to public JSON.",
        "- Manual review remains incomplete.",
        "- Promotion remains blocked as expected.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def mirror_public(paths) -> None:
    for name in PUBLIC_FILES:
        data = read_json(paths.public_path(name))
        write_json(paths.web_project_path(name), data)


def build(project: str) -> BuildStats:
    paths = from_project(project)
    section_texts = load_section_texts(paths.project_dir)

    overview = read_json(paths.book_overview_json)
    cards = read_json(paths.chapter_reading_cards_json)
    concepts = read_json(paths.key_concepts_json)
    quotes = read_json(paths.quote_index_json)
    questions = read_json(paths.reading_questions_json)

    for payload in [overview, cards, concepts, quotes, questions]:
        payload["status"] = "draft"
        payload["visibility"] = "public"
        payload["release_phase"] = "public-preview"
        payload["review_status"] = "manual-review-pending"
        payload["preview_mode"] = "personal-reading-source-enriched-preview"
        payload.setdefault("book", {})["source_type"] = "ebook"

    cards, place_rows, stats = enrich_chapters(cards, section_texts)
    questions, enhanced_answers = enrich_questions(questions, cards.get("chapters", []))
    stats.questions = len(questions.get("questions", []))
    stats.question_answers = enhanced_answers

    overview["source_enrichment"] = {
        "version": "v0.7-A11",
        "mode": "personal-reading-source-enriched-preview",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "chapter_cards": stats.chapters,
        "source_informed_summaries": stats.source_summaries,
        "original_clue_coverage": stats.excerpts,
        "scene_notes_coverage": stats.scene_notes,
        "then_now_coverage": stats.then_now,
        "question_answer_coverage": stats.question_answers,
    }
    overview["place_then_now"] = place_rows
    overview["then_now_summary"] = (
        "昔日旅程按书信中的移动和观看经验展开；今日景点对照只作为阅读参照。"
        "列出公开来源的地点可先作为现代参照，未列来源的地点保留待复核状态。"
    )

    quotes["reader_note"] = (
        "原文摘录与阅读线索：当前页面作为个人阅读导览，补充来自原书的短摘录、场景摘要、"
        "地点线索和阅读提示。页面仍处于公开预览与人工复核阶段。"
    )
    quotes["source_enrichment_mode"] = "original-clues-without-fulltext"

    write_json(paths.book_overview_json, overview)
    write_json(paths.chapter_reading_cards_json, cards)
    write_json(paths.key_concepts_json, concepts)
    write_json(paths.quote_index_json, quotes)
    write_json(paths.reading_questions_json, questions)
    mirror_public(paths)

    write_place_report(paths.report_path("place_then_now_sources_v0.7_a11.md"), place_rows)
    write_report(paths.report_path("source_enrichment_report_v0.7_a11.md"), stats, place_rows)
    return stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    stats = build(args.project)
    print("Source enrichment complete")
    print(f"chapters={stats.chapters}")
    print(f"source_summaries={stats.source_summaries}")
    print(f"excerpt_coverage={stats.excerpts}")
    print(f"scene_notes={stats.scene_notes}")
    print(f"then_now={stats.then_now}")
    print(f"questions={stats.questions}")
    print(f"enhanced_answers={stats.question_answers}")
    print(f"source_covered_places={stats.source_covered_places}")
    print(f"needs_source_review_places={stats.needs_source_review_places}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
