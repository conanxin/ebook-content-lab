#!/usr/bin/env python3
"""Build real short source excerpts for the reading-guide public preview.

The script reads private working text, selects short section-local excerpts, and
writes only curated snippets into public JSON. It does not copy private files,
paths, or full sections into public output.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from scripts.lib.project_paths import from_project
except ModuleNotFoundError:
    from lib.project_paths import from_project


VERSION = "v0.7-A18"
REVIEW_STATUS = "source-excerpt-draft"

PLACEHOLDER_MARKERS = [
    "用于定位本封信的场景和语气",
    "不作为全文替代",
    "结构证据",
    "structural_no_quote",
    "Structural reference only",
    "No source quote is published",
    "Derived from title",
    "Derived from letter order",
    "基于标题、地点线索、结构摘要",
]

TYPE_LABELS = {
    "opening_scene": "开篇场景",
    "route_movement": "路线移动",
    "place_description": "地点描写",
    "travel_observation": "旅途观察",
    "reflection": "感受反思",
    "closing_moment": "收束时刻",
    "other": "阅读线索",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_paragraphs(text: str, title: str) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n+", text) if p.strip()]
    usable: list[str] = []
    for paragraph in paragraphs:
        compact = normalize_text(paragraph)
        if not compact:
            continue
        if compact == title or compact.startswith(title):
            continue
        if re.match(r"^第\d+封\s", compact):
            continue
        if len(compact) <= 18 and compact.endswith(("：", ":")):
            continue
        if compact in {"父母大人台鉴：", "阿晖［笔者的妻子］：", "又开动啦，15:15。"}:
            continue
        usable.append(compact)
    return usable


def sentence_candidates(paragraphs: list[str]) -> list[str]:
    candidates: list[str] = []
    for paragraph in paragraphs:
        pieces = re.split(r"(?<=[。！？；])", paragraph)
        for piece in pieces:
            piece = piece.strip()
            if not piece:
                continue
            if 20 <= len(piece) <= 160:
                candidates.append(piece)
            elif len(piece) > 160:
                clipped = clip_long_piece(piece)
                if clipped:
                    candidates.append(clipped)
    return candidates


def clip_long_piece(piece: str) -> str | None:
    for mark in ["。", "；", "，", "、"]:
        pos = piece.find(mark, 48)
        if 48 <= pos <= 150:
            return piece[: pos + 1].strip()
    if len(piece) >= 80:
        return piece[:120].strip()
    return None


def classify_excerpt(text: str, places: list[str], index: int, total: int) -> str:
    if index == 0:
        return "opening_scene"
    if index == total - 1:
        return "closing_moment"
    if any(place and place in text for place in places):
        return "place_description"
    if re.search(r"下车|上车|车厢|火车|汽车|船|甲板|公路|铁路|路上|上路|赶路|走到|到达|抵达|经过|驶|航|乘|出发|进城|沿着|沿", text):
        return "route_movement"
    if re.search(r"看|见|山|水|树|风|雨|城|寺|庙|街|江|海|湖|岩|峰", text):
        return "travel_observation"
    if re.search(r"觉得|感到|想|心|喜欢|忧郁|寂寞|兴奋|可惜|难忘", text):
        return "reflection"
    return "other"


def score_candidate(text: str, places: list[str]) -> int:
    score = 0
    score += min(len(text), 120)
    if any(place and place in text for place in places):
        score += 45
    if re.search(r"下车|上车|车厢|火车|汽车|船|甲板|公路|铁路|路上|上路|赶路|走到|到达|抵达|经过|驶|航|乘|出发|进城|沿着|沿", text):
        score += 35
    if re.search(r"山|水|风|雨|城|寺|庙|街|江|海|湖|岩|峰|树|云", text):
        score += 30
    if re.search(r"觉得|感到|想|心|喜欢|忧郁|寂寞|兴奋|可惜|难忘", text):
        score += 25
    if re.search(r"第\d+封|台鉴|阿晖|目录|版权|ISBN", text):
        score -= 200
    if any(marker in text for marker in PLACEHOLDER_MARKERS):
        score -= 500
    return score


def select_excerpts(section: dict[str, Any], places: list[str]) -> list[dict[str, Any]]:
    text = section.get("text", "")
    title = section.get("title", "")
    paragraphs = split_paragraphs(text, title)
    candidates = sentence_candidates(paragraphs)

    seen: set[str] = set()
    ranked: list[tuple[int, int, str]] = []
    for idx, candidate in enumerate(candidates):
        clean = normalize_text(candidate)
        if clean in seen:
            continue
        seen.add(clean)
        if len(clean) < 20:
            continue
        ranked.append((score_candidate(clean, places), idx, clean))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    selected: list[str] = []
    type_targets = ["opening_scene", "route_movement", "place_description", "travel_observation", "reflection", "closing_moment"]

    for target in type_targets:
        for _score, original_idx, candidate in ranked:
            if candidate in selected:
                continue
            if classify_excerpt(candidate, places, original_idx, max(len(candidates), 1)) == target:
                selected.append(candidate)
                break
        if len(selected) >= 4:
            break

    for _score, _idx, candidate in ranked:
        if len(selected) >= 4:
            break
        if candidate not in selected:
            selected.append(candidate)

    if len(selected) < 4:
        for paragraph in paragraphs:
            fallback = clip_long_piece(paragraph) or paragraph[:120].strip()
            if len(fallback) >= 20 and fallback not in selected:
                selected.append(fallback)
            if len(selected) >= 4:
                break

    excerpts: list[dict[str, Any]] = []
    total_candidates = max(len(candidates), 1)
    for idx, excerpt in enumerate(selected[:4], start=1):
        original_index = candidates.index(excerpt) if excerpt in candidates else idx - 1
        excerpt_type = classify_excerpt(excerpt, places, original_index, total_candidates)
        excerpts.append(
            {
                "anchor_id": "",
                "text": excerpt,
                "note": make_note(excerpt_type, excerpt, places),
                "reading_use": make_reading_use(excerpt_type),
                "excerpt_type": excerpt_type,
                "section_id": section.get("section_id"),
                "review_status": REVIEW_STATUS,
                "source_mode": "real_source_excerpt",
            }
        )
    return excerpts


def make_note(excerpt_type: str, excerpt: str, places: list[str]) -> str:
    label = TYPE_LABELS.get(excerpt_type, "阅读线索")
    place_hits = [place for place in places if place and place in excerpt]
    if place_hits:
        return f"{label}：这段直接触及{'、'.join(place_hits[:3])}，适合作为理解本封信地点经验的文本入口。"
    if excerpt_type == "route_movement":
        return "路线移动：这段能看到作者在交通、道路或抵达过程中的实际感受。"
    if excerpt_type == "travel_observation":
        return "旅途观察：这段保留了风景、城市或环境的现场感，适合先读再看今昔对照。"
    if excerpt_type == "reflection":
        return "感受反思：这段把旅程中的情绪和判断露出来，可作为精读切入点。"
    if excerpt_type == "opening_scene":
        return "开篇场景：这段把本封信的行旅现场打开，适合作为快速浏览的第一处文本锚。"
    if excerpt_type == "closing_moment":
        return "收束时刻：这段可帮助读者把本封信的移动、观察和回望合在一起。"
    return "阅读线索：这段来自本封信正文，可帮助读者把导读说明落回原书文字。"


def make_reading_use(excerpt_type: str) -> str:
    if excerpt_type == "route_movement":
        return "先看移动方式和空间转换，再回到路线结构。"
    if excerpt_type == "place_description":
        return "先圈出地点名，再对照本封信中的今日景点说明。"
    if excerpt_type == "travel_observation":
        return "先读景物和环境，再看场景说明如何解释这种观察。"
    if excerpt_type == "reflection":
        return "先抓住情绪和判断，再回答阅读问题。"
    return "先读原文，再看下方场景、路线、今昔对照和参考回答。"


def update_questions(questions: dict[str, Any], chapters: list[dict[str, Any]]) -> int:
    by_letter = {chapter.get("letter_id"): chapter for chapter in chapters}
    first_three = chapters[:3]
    coverage = 0
    for question in questions.get("questions", []):
        letter_id = question.get("letter_id")
        if letter_id and letter_id in by_letter:
            chapter = by_letter[letter_id]
            excerpt = (chapter.get("core_source_excerpts") or chapter.get("source_excerpts") or [{}])[0]
            question["source_anchor"] = {
                "anchor_type": "real_source_excerpt",
                "letter_id": chapter.get("letter_id"),
                "chapter_id": chapter.get("chapter_id"),
                "section_id": chapter.get("section_id"),
                "anchor_id": excerpt.get("anchor_id"),
                "excerpt_type": excerpt.get("excerpt_type"),
                "note": "这个问题先回到对应信封卡的原文选段，再展开场景、路线和今昔对照。",
            }
            question["quick_answer"] = make_quick_answer(chapter, excerpt)
            question["deep_answer"] = make_deep_answer(chapter, excerpt)
        else:
            anchors = []
            for chapter in first_three:
                excerpt = (chapter.get("core_source_excerpts") or chapter.get("source_excerpts") or [{}])[0]
                anchors.append(
                    {
                        "letter_id": chapter.get("letter_id"),
                        "chapter_id": chapter.get("chapter_id"),
                        "section_id": chapter.get("section_id"),
                        "anchor_id": excerpt.get("anchor_id"),
                        "excerpt_type": excerpt.get("excerpt_type"),
                    }
                )
            question["source_anchor"] = {
                "anchor_type": "real_source_excerpt_route_sample",
                "anchors": anchors,
                "note": "全书问题先连接前三封信的真实原文选段，再回到 25 封书信整体路线。",
            }
            question["quick_answer"] = "参考回答：可以先读前三封信的真实原文选段，看到路线如何从具体交通、地点和观察中展开。"
            question["deep_answer"] = "参考回答：这 25 封信不是抽象路线表，而是由一段段具体行旅文字推进。先读前三封信的原文选段，再顺着时间线看地点、交通、风景和感受如何逐步连成旅行经验。"
        question["basis"] = "基于真实原文选段、地点线索与公开导读信息生成，待人工复核。"
        question["updated_in"] = VERSION
        if question.get("source_anchor"):
            coverage += 1
    return coverage


def make_quick_answer(chapter: dict[str, Any], excerpt: dict[str, Any]) -> str:
    title = chapter.get("title") or "本封信"
    text = excerpt.get("text") or ""
    short = text[:46] + ("..." if len(text) > 46 else "")
    return f"参考回答：先读“{short}”，再把《{title}》中的地点和移动线索连起来看。"


def make_deep_answer(chapter: dict[str, Any], excerpt: dict[str, Any]) -> str:
    places = "、".join((chapter.get("places") or [])[:4]) or "本封信的地点"
    note = excerpt.get("note") or "这段原文适合作为精读入口。"
    return f"参考回答：这封信可从核心原文选段进入。{note} 再结合 {places} 的路线顺序，就能把原文中的现场感、移动过程和今日对照放在同一条阅读线上。"


def mirror_public(paths: Any, names: list[str]) -> None:
    for name in names:
        paths.web_project_path(name).write_text(paths.public_path(name).read_text(encoding="utf-8"), encoding="utf-8")


def render_plan() -> str:
    return "\n".join(
        [
            "# v0.7-A18 Real Source Excerpts Plan",
            "",
            "## User Feedback",
            "",
            "The public preview had source-anchor modules, but many visible anchors were explanatory placeholders rather than real book text.",
            "",
            "## Goal",
            "",
            "Replace placeholder-like anchors with curated short excerpts from the private working text layer, while keeping the page a guided personal-reading preview rather than a full-text reader.",
            "",
            "## Excerpt Strategy",
            "",
            "- Select four short excerpts for each of the 25 body letters.",
            "- Prefer scenes, movement, place description, travel observation, reflection, and closing moments.",
            "- Avoid titles, greetings, metadata, directory text, and generic placeholder language.",
            "- Keep excerpts short and attach a reader-facing note to every excerpt.",
            "",
            "## Field Design",
            "",
            "- `source_excerpts`: all selected real excerpts for the letter.",
            "- `core_source_excerpts`: two excerpts shown by default.",
            "- `extra_source_excerpts`: folded additional excerpts.",
            "- `source_anchor_layer`: marks the letter as real-source-backed.",
            "- reading questions point back to real excerpt anchors.",
            "",
            "## UI Strategy",
            "",
            "Rename source-anchor presentation to `原文选段`, show two excerpts first, and fold the remaining snippets under `更多原文片段`.",
            "",
            "## Personal Reading Note",
            "",
            "This phase follows the user's personal-reading requirement. The repository still does not commit private source files or full working text files.",
            "",
            "## Private Boundary",
            "",
            "Only curated short excerpts are written to public JSON. Private source files, local paths, and full-section text are not written to public output.",
            "",
            "## Status",
            "",
            "No status promotion is performed. The project remains `draft`, `public-preview`, and `manual-review-pending`.",
            "",
            "## A19 Recommendation",
            "",
            "Use the A18 excerpt layer for manual excerpt refinement, then consider a focused whole-letter reader mode if the user wants longer personal reading sessions.",
            "",
        ]
    )


def render_report(stats: dict[str, Any]) -> str:
    lines = [
        "# Real Source Excerpts Report v0.7-A18",
        "",
        "## Modified Files",
        "",
        "- `projects/second-reading-guide/public/chapter_reading_cards.json`",
        "- `projects/second-reading-guide/public/book_overview.json`",
        "- `projects/second-reading-guide/public/reading_questions.json`",
        "- `web/public/projects/second-reading-guide/*.json` mirrors",
        "",
        "## Counts",
        "",
        f"- source_excerpts total: `{stats['source_total']}`",
        f"- core_source_excerpts total: `{stats['core_total']}`",
        f"- extra_source_excerpts total: `{stats['extra_total']}`",
        f"- per-letter min/max: `{stats['min_per_letter']}` / `{stats['max_per_letter']}`",
        f"- reading question source_anchor coverage: `{stats['question_anchor_coverage']}`",
        "",
        "## Excerpt Type Counts",
        "",
    ]
    for key, value in sorted(stats["type_counts"].items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Placeholder Cleanup",
            "",
            f"- placeholder markers remaining in excerpt text: `{stats['placeholder_hits']}`",
            "",
            "## Status And Boundary",
            "",
            "- public preview status remains `draft` / `public-preview` / `manual-review-pending`.",
            "- No private source file, local path, or full working text file is written to public JSON.",
            "- Local build should be verified after this builder runs.",
            "- Online URL: https://conanxin.github.io/ebook-content-lab/#/projects/second-reading-guide",
            "",
        ]
    )
    return "\n".join(lines)


def render_backlog(chapters: list[dict[str, Any]]) -> str:
    lines = [
        "# Real Source Excerpts Backlog v0.7-A18",
        "",
        "Items below are candidates for later human refinement.",
        "",
        "| letter | item | reason |",
        "|---|---|---|",
    ]
    for chapter in chapters:
        excerpts = chapter.get("source_excerpts") or []
        for excerpt in excerpts:
            text = excerpt.get("text", "")
            reason = ""
            if len(text) < 28:
                reason = "excerpt is short; confirm it is representative"
            elif len(text) > 145:
                reason = "excerpt is near the upper length target; consider trimming"
            elif excerpt.get("excerpt_type") == "other":
                reason = "type is generic; consider replacing with a stronger scene"
            if reason:
                preview = text[:32].replace("|", "｜")
                lines.append(f"| {chapter.get('letter_id')} | {preview} | {reason} |")
    if len(lines) == 5:
        lines.append("| all | none | no immediate mechanical backlog items |")
    lines.append("")
    return "\n".join(lines)


def build(project: str) -> dict[str, Any]:
    paths = from_project(project)
    sections_path = paths.private_dir / "book_sections.jsonl"
    chunks_path = paths.private_dir / "book_chunks.jsonl"
    sections = {row.get("section_id"): row for row in load_jsonl(sections_path)}
    _chunks = load_jsonl(chunks_path)

    book = read_json(paths.book_overview_json)
    chapters_payload = read_json(paths.chapter_reading_cards_json)
    questions = read_json(paths.reading_questions_json)
    chapters = chapters_payload.get("chapters", [])

    type_counts: Counter[str] = Counter()
    per_letter_counts: list[int] = []
    placeholder_hits = 0

    for chapter in chapters:
        section_id = chapter.get("section_id")
        section = sections.get(section_id)
        if not section:
            raise SystemExit(f"Missing private section text for {section_id}")
        excerpts = select_excerpts(section, chapter.get("places") or [])
        for idx, excerpt in enumerate(excerpts, start=1):
            excerpt["anchor_id"] = f"{chapter.get('letter_id')}-real-source-{idx:02d}"
            type_counts[excerpt["excerpt_type"]] += 1
            if any(marker in excerpt["text"] for marker in PLACEHOLDER_MARKERS):
                placeholder_hits += 1

        chapter["source_excerpts"] = excerpts
        chapter["core_source_excerpts"] = excerpts[:2]
        chapter["extra_source_excerpts"] = excerpts[2:]
        chapter["source_anchor_layer"] = {
            "version": VERSION,
            "mode": "real_source_excerpt",
            "core_excerpt_count": len(excerpts[:2]),
            "extra_excerpt_count": len(excerpts[2:]),
            "review_status": REVIEW_STATUS,
        }
        chapter["source_anchor_layer_ready"] = True
        chapter["updated_in"] = VERSION
        if isinstance(chapter.get("close_reading"), dict):
            chapter["close_reading"]["excerpt_focus"] = excerpts[0]["text"]
            chapter["close_reading"]["why_it_matters"] = excerpts[0]["note"]
            chapter["close_reading"]["updated_in"] = VERSION
        if isinstance(chapter.get("letter_reading_unit"), dict):
            unit = chapter["letter_reading_unit"]
            unit["source_excerpts"] = excerpts
            unit["core_source_excerpts"] = excerpts[:2]
            unit["extra_source_excerpts"] = excerpts[2:]
            unit.setdefault("secondary_details", {})["evidence_refs"] = [
                {
                    "anchor_id": excerpt["anchor_id"],
                    "excerpt_type": excerpt["excerpt_type"],
                    "note": excerpt["note"],
                }
                for excerpt in excerpts
            ]
        per_letter_counts.append(len(excerpts))

    question_anchor_coverage = update_questions(questions, chapters)

    book["source_anchor_layer"] = {
        "version": VERSION,
        "mode": "real_source_excerpt",
        "letters_with_source_excerpts": sum(1 for chapter in chapters if chapter.get("source_excerpts")),
        "min_excerpts_per_letter": min(per_letter_counts),
        "question_source_anchor_count": question_anchor_coverage,
        "reading_order": ["原文选段", "场景说明", "路线结构", "今昔对照", "阅读问题", "参考答案"],
        "updated_in": VERSION,
    }
    book["real_source_excerpt_summary"] = {
        "version": VERSION,
        "source_excerpts_total": sum(per_letter_counts),
        "core_source_excerpts_total": sum(len(chapter.get("core_source_excerpts") or []) for chapter in chapters),
        "extra_source_excerpts_total": sum(len(chapter.get("extra_source_excerpts") or []) for chapter in chapters),
        "display_label": "原文选段",
        "review_status": REVIEW_STATUS,
    }
    book["updated_in"] = VERSION

    write_json(paths.book_overview_json, book)
    write_json(paths.chapter_reading_cards_json, chapters_payload)
    write_json(paths.reading_questions_json, questions)
    mirror_public(paths, ["book_overview.json", "chapter_reading_cards.json", "reading_questions.json"])

    stats = {
        "source_total": sum(per_letter_counts),
        "core_total": sum(len(chapter.get("core_source_excerpts") or []) for chapter in chapters),
        "extra_total": sum(len(chapter.get("extra_source_excerpts") or []) for chapter in chapters),
        "min_per_letter": min(per_letter_counts),
        "max_per_letter": max(per_letter_counts),
        "type_counts": dict(type_counts),
        "question_anchor_coverage": question_anchor_coverage,
        "placeholder_hits": placeholder_hits,
    }

    paths.report_path("v0.7_a18_real_source_excerpts_plan.md").write_text(render_plan(), encoding="utf-8")
    paths.report_path("real_source_excerpts_report_v0.7_a18.md").write_text(render_report(stats), encoding="utf-8")
    paths.report_path("real_source_excerpts_backlog_v0.7_a18.md").write_text(render_backlog(chapters), encoding="utf-8")
    return stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", default=VERSION)
    args = parser.parse_args()
    stats = build(args.project)
    print("Real source excerpts built")
    for key in ["source_total", "core_total", "extra_total", "min_per_letter", "max_per_letter", "question_anchor_coverage"]:
        print(f"{key}: {stats[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
