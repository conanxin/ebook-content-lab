#!/usr/bin/env python3
"""Build longer source reading blocks for each reading-guide letter.

This A20 builder reads private working text, extracts paragraph-sized public
reading blocks, and leaves the private source files themselves untouched.
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


VERSION = "v0.7-A20"
REVIEW_STATUS = "source-reading-block-draft"

ROLE_LABELS = {
    "opening_scene": "开篇场景",
    "route_movement": "路线移动",
    "place_observation": "地点观察",
    "travel_detail": "旅途细节",
    "reflection": "感受反思",
    "turning_point": "旅程转折",
    "closing_moment": "收束时刻",
    "other": "阅读片段",
}

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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_paragraphs(text: str, title: str) -> list[str]:
    paragraphs = [normalize_text(item) for item in re.split(r"\n+", text) if normalize_text(item)]
    usable: list[str] = []
    for paragraph in paragraphs:
        if paragraph == title or paragraph.startswith(title):
            continue
        if re.match(r"^第\d+封\s", paragraph):
            continue
        if len(paragraph) <= 24 and (paragraph.endswith(("：", ":")) or "台鉴" in paragraph):
            continue
        if any(marker in paragraph for marker in PLACEHOLDER_MARKERS):
            continue
        usable.append(paragraph)
    return usable


def sentence_units(paragraph: str) -> list[str]:
    pieces = [item.strip() for item in re.split(r"(?<=[。！？；])", paragraph) if item.strip()]
    return pieces or [paragraph]


def block_from_paragraph(paragraph: str) -> str:
    if 80 <= len(paragraph) <= 320:
        return paragraph
    sentences = sentence_units(paragraph)
    block = ""
    for sentence in sentences:
        candidate = f"{block}{sentence}" if block else sentence
        if len(candidate) <= 320:
            block = candidate
        elif len(block) >= 80:
            break
        else:
            block = candidate[:320]
            break
        if len(block) >= 160:
            break
    if len(block) < 80 and len(paragraph) > len(block):
        block = paragraph[: min(len(paragraph), 260)]
    return block.strip()


def combined_blocks(paragraphs: list[str]) -> list[str]:
    blocks: list[str] = []
    for paragraph in paragraphs:
        block = block_from_paragraph(paragraph)
        if 70 <= len(block) <= 340:
            blocks.append(block)
    return blocks


def classify_block(text: str, places: list[str], index: int, total: int) -> str:
    if index == 0:
        return "opening_scene"
    if index >= total - 2:
        return "closing_moment"
    if re.search(r"忽然|突然|可是|然而|但|却|转|改|终于|后来", text):
        return "turning_point"
    if any(place and place in text for place in places):
        return "place_observation"
    if re.search(r"下车|上车|车厢|火车|汽车|船|甲板|公路|铁路|路上|赶路|走到|到达|抵达|经过|驶|航|乘|出发|进城|沿着|沿", text):
        return "route_movement"
    if re.search(r"觉得|感到|想|心|喜欢|忧郁|寂寞|兴奋|可惜|难忘|以为|看来", text):
        return "reflection"
    if re.search(r"饭|宿|住|店|人|朋友|先生|师傅|买|问|说|谈|睡|醒", text):
        return "travel_detail"
    return "other"


def score_block(text: str, places: list[str], role: str) -> int:
    score = min(len(text), 240)
    if 100 <= len(text) <= 260:
        score += 50
    if any(place and place in text for place in places):
        score += 55
    if role in {"route_movement", "place_observation", "travel_detail", "reflection"}:
        score += 35
    if role == "other":
        score -= 20
    if re.search(r"目录|版权|ISBN|第\d+封", text):
        score -= 200
    return score


def select_blocks(section: dict[str, Any], places: list[str]) -> list[dict[str, Any]]:
    text = section.get("text", "")
    title = section.get("title", "")
    paragraphs = split_paragraphs(text, title)
    candidates = combined_blocks(paragraphs)
    scored: list[tuple[int, int, str, str]] = []
    for index, block in enumerate(candidates):
        role = classify_block(block, places, index, len(candidates))
        scored.append((score_block(block, places, role), index, role, block))

    selected: list[tuple[int, str, str]] = []
    role_targets = ["opening_scene", "route_movement", "place_observation", "travel_detail", "reflection", "turning_point", "closing_moment"]
    for target in role_targets:
        matches = [item for item in scored if item[2] == target and item[3] not in {selected_item[2] for selected_item in selected}]
        if matches:
            matches.sort(key=lambda item: (-item[0], item[1]))
            selected.append((matches[0][1], matches[0][2], matches[0][3]))
        if len(selected) >= 5:
            break

    if len(selected) < 5:
        for _score, index, role, block in sorted(scored, key=lambda item: (-item[0], item[1])):
            if block not in {selected_item[2] for selected_item in selected}:
                selected.append((index, role, block))
            if len(selected) >= 5:
                break

    selected.sort(key=lambda item: item[0])
    blocks: list[dict[str, Any]] = []
    for idx, (_source_index, role, block_text) in enumerate(selected[:5], start=1):
        blocks.append(
            {
                "block_id": "",
                "text": block_text,
                "guide_note": guide_note(role, block_text, places),
                "reading_role": role,
                "source_scope": "paragraph" if block_text in paragraphs else "paragraph_group",
                "section_id": section.get("section_id"),
                "review_status": REVIEW_STATUS,
            }
        )
    return blocks


def guide_note(role: str, text: str, places: list[str]) -> str:
    label = ROLE_LABELS.get(role, "阅读片段")
    place_hits = [place for place in places if place and place in text]
    if place_hits:
        return f"{label}：这段把{'、'.join(place_hits[:3])}放进具体行旅语境中，适合先读原文再看地点对照。"
    if role == "opening_scene":
        return "开篇场景：这段比短摘更完整地打开本封信的时间、状态或出发处境。"
    if role == "route_movement":
        return "路线移动：这段保留了交通、道路或抵达过程，可帮助读者顺着旅程阅读。"
    if role == "travel_detail":
        return "旅途细节：这段呈现途中人物、住宿、交通或日常细节，让旅行不只是地点列表。"
    if role == "reflection":
        return "感受反思：这段把作者的判断和情绪放出来，适合作为精读问题的依据。"
    if role == "turning_point":
        return "旅程转折：这段显示叙述或情绪的转向，适合对照前后段落阅读。"
    if role == "closing_moment":
        return "收束时刻：这段帮助读者理解本封信如何结束或回望这一段旅程。"
    return "阅读片段：这段来自本封信正文，可作为个人阅读导览中的连续原文入口。"


def make_question_answer(chapter: dict[str, Any], block: dict[str, Any]) -> tuple[str, str]:
    title = chapter.get("title") or "本封信"
    preview = block.get("text", "")[:58] + ("..." if len(block.get("text", "")) > 58 else "")
    quick = f"参考回答：先读这段原文节选“{preview}”，再回到《{title}》的路线和地点关系。"
    deep = f"参考回答：这封信现在可以先从一个较完整的原文阅读块进入。{block.get('guide_note')} 读完这段后，再把下方场景说明、今昔对照和问题回答连起来看，会比只看一句短摘更接近原书的阅读节奏。"
    return quick, deep


def update_questions(questions: dict[str, Any], chapters: list[dict[str, Any]]) -> int:
    by_letter = {chapter.get("letter_id"): chapter for chapter in chapters}
    coverage = 0
    for question in questions.get("questions", []):
        letter_id = question.get("letter_id")
        if letter_id and letter_id in by_letter:
            chapter = by_letter[letter_id]
        else:
            chapter = chapters[0]
        blocks = chapter.get("core_source_reading_blocks") or chapter.get("source_reading_blocks") or []
        block = blocks[0] if blocks else {}
        question["source_anchor"] = {
            "anchor_type": "source_reading_block",
            "letter_id": chapter.get("letter_id"),
            "chapter_id": chapter.get("chapter_id"),
            "section_id": chapter.get("section_id"),
            "block_id": block.get("block_id"),
            "reading_role": block.get("reading_role"),
            "note": "这个问题优先回到对应书信的原文节选阅读块，再展开场景、路线和今昔对照。",
        }
        quick, deep = make_question_answer(chapter, block)
        question["quick_answer"] = quick
        question["deep_answer"] = deep
        question["updated_in"] = VERSION
        coverage += 1
    return coverage


def mirror(paths: Any, names: list[str]) -> None:
    for name in names:
        paths.web_project_path(name).write_text(paths.public_path(name).read_text(encoding="utf-8"), encoding="utf-8")


def render_plan() -> str:
    return "\n".join(
        [
            "# v0.7-A20 Source Reading Blocks Plan",
            "",
            "## User Feedback",
            "",
            "The real source excerpts added in A18 solved the missing-anchor problem, but many visible snippets still felt like one-sentence anchors rather than readable original text.",
            "",
            "## Goal",
            "",
            "Add paragraph-sized source reading blocks for each of the 25 letters, keeping quick mode readable and deep mode richer.",
            "",
            "## Extraction Strategy",
            "",
            "- Read the private working text layer locally.",
            "- Select five paragraph or paragraph-group excerpts per letter.",
            "- Prefer opening scene, route movement, place observation, travel detail, reflection, turning point, or closing moment.",
            "- Keep the existing A18 short excerpts for compatibility.",
            "",
            "## Field Design",
            "",
            "- `source_reading_blocks`: all five reading blocks.",
            "- `core_source_reading_blocks`: two blocks shown first.",
            "- `extra_source_reading_blocks`: folded additional blocks.",
            "",
            "## UI Strategy",
            "",
            "The letter card should prioritize `原文节选` / `原文阅读片段` and use the new block fields before the shorter A18 excerpts.",
            "",
            "## Personal Reading Note",
            "",
            "The user manages copyright for personal reading. This phase still does not commit private working files or full source files.",
            "",
            "## Private Boundary",
            "",
            "Only selected reading blocks are written to public JSON. Private working files and local paths are not written to public output.",
            "",
            "## Status",
            "",
            "No promotion is performed. The project remains `draft`, `public-preview`, and `manual-review-pending`.",
            "",
            "## A21 Recommendation",
            "",
            "Review the blocks on the live page, then decide whether to build a whole-letter reader mode or run manual block refinement.",
            "",
        ]
    )


def render_report(stats: dict[str, Any]) -> str:
    lines = [
        "# Source Reading Blocks Report v0.7-A20",
        "",
        "## Modified Files",
        "",
        "- `projects/second-reading-guide/public/book_overview.json`",
        "- `projects/second-reading-guide/public/chapter_reading_cards.json`",
        "- `projects/second-reading-guide/public/reading_questions.json`",
        "- web mirror JSON for the same files",
        "- `web/src/pages/ReadingGuideProjectPage.tsx`",
        "- `web/src/types/readingGuide.ts`",
        "- `web/src/styles.css`",
        "",
        "## Counts",
        "",
        f"- source_reading_blocks total: `{stats['total_blocks']}`",
        f"- core_source_reading_blocks total: `{stats['core_total']}`",
        f"- extra_source_reading_blocks total: `{stats['extra_total']}`",
        f"- per-letter min/max: `{stats['min_per_letter']}` / `{stats['max_per_letter']}`",
        f"- average block length: `{stats['average_length']}`",
        f"- reading question source_anchor coverage: `{stats['question_anchor_coverage']}`",
        "",
        "## Role Counts",
        "",
    ]
    for key, value in sorted(stats["role_counts"].items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Page Display",
            "",
            "- The page now prioritizes `原文节选` over one-sentence source anchors.",
            "- Quick mode shows core reading blocks.",
            "- Deep mode opens additional reading blocks.",
            "",
            "## Boundary",
            "",
            "- Status remains draft / public-preview / manual-review-pending.",
            "- No private working file or local path is exported.",
            "- Local build should be verified after this phase.",
            "- Online URL: https://conanxin.github.io/ebook-content-lab/#/projects/second-reading-guide",
            "",
        ]
    )
    return "\n".join(lines)


def render_backlog(chapters: list[dict[str, Any]]) -> str:
    lines = [
        "# Source Reading Blocks Backlog v0.7-A20",
        "",
        "| letter | block | reason |",
        "|---|---|---|",
    ]
    for chapter in chapters:
        for block in chapter.get("source_reading_blocks") or []:
            text = block.get("text", "")
            reason = ""
            if len(text) < 90:
                reason = "may still be short for a reading block"
            elif len(text) > 300:
                reason = "near the upper length target; review page rhythm"
            elif block.get("reading_role") == "other":
                reason = "generic role; consider replacing with a more vivid block"
            if reason:
                preview = text[:36].replace("|", "｜")
                lines.append(f"| {chapter.get('letter_id')} | {preview} | {reason} |")
    if len(lines) == 4:
        lines.append("| all | none | no immediate mechanical backlog items |")
    lines.append("")
    return "\n".join(lines)


def build(project: str, version: str) -> dict[str, Any]:
    paths = from_project(project)
    sections = {row.get("section_id"): row for row in load_jsonl(paths.private_dir / "book_sections.jsonl")}
    book = read_json(paths.book_overview_json)
    chapters_payload = read_json(paths.chapter_reading_cards_json)
    questions = read_json(paths.reading_questions_json)
    chapters = chapters_payload.get("chapters", [])

    lengths: list[int] = []
    role_counts: Counter[str] = Counter()
    per_letter: list[int] = []

    for chapter in chapters:
        section = sections.get(chapter.get("section_id"))
        if not section:
            raise SystemExit(f"Missing working section for {chapter.get('section_id')}")
        blocks = select_blocks(section, chapter.get("places") or [])
        for index, block in enumerate(blocks, start=1):
            block["block_id"] = f"{chapter.get('letter_id')}-reading-block-{index:02d}"
            lengths.append(len(block["text"]))
            role_counts[block["reading_role"]] += 1
        chapter["source_reading_blocks"] = blocks
        chapter["core_source_reading_blocks"] = blocks[:2]
        chapter["extra_source_reading_blocks"] = blocks[2:]
        chapter["source_reading_blocks_ready"] = True
        chapter["updated_in"] = VERSION
        if isinstance(chapter.get("letter_reading_unit"), dict):
            chapter["letter_reading_unit"]["source_reading_blocks"] = blocks
            chapter["letter_reading_unit"]["core_source_reading_blocks"] = blocks[:2]
            chapter["letter_reading_unit"]["extra_source_reading_blocks"] = blocks[2:]
        if isinstance(chapter.get("close_reading"), dict) and blocks:
            chapter["close_reading"]["excerpt_focus"] = blocks[0]["text"]
            chapter["close_reading"]["why_it_matters"] = blocks[0]["guide_note"]
            chapter["close_reading"]["updated_in"] = VERSION
        per_letter.append(len(blocks))

    question_anchor_coverage = update_questions(questions, chapters)

    book["source_reading_blocks"] = {
        "version": VERSION,
        "mode": "paragraph_reading_blocks",
        "letters_with_blocks": len([chapter for chapter in chapters if chapter.get("source_reading_blocks")]),
        "min_blocks_per_letter": min(per_letter),
        "total_blocks": sum(per_letter),
        "average_block_length": round(sum(lengths) / len(lengths), 1),
        "display_label": "原文节选",
        "review_status": REVIEW_STATUS,
    }
    book["updated_in"] = VERSION

    write_json(paths.book_overview_json, book)
    write_json(paths.chapter_reading_cards_json, chapters_payload)
    write_json(paths.reading_questions_json, questions)
    mirror(paths, ["book_overview.json", "chapter_reading_cards.json", "reading_questions.json"])

    stats = {
        "total_blocks": sum(per_letter),
        "core_total": sum(len(chapter.get("core_source_reading_blocks") or []) for chapter in chapters),
        "extra_total": sum(len(chapter.get("extra_source_reading_blocks") or []) for chapter in chapters),
        "min_per_letter": min(per_letter),
        "max_per_letter": max(per_letter),
        "average_length": round(sum(lengths) / len(lengths), 1),
        "question_anchor_coverage": question_anchor_coverage,
        "role_counts": dict(role_counts),
    }
    paths.report_path("v0.7_a20_source_reading_blocks_plan.md").write_text(render_plan(), encoding="utf-8")
    paths.report_path("source_reading_blocks_report_v0.7_a20.md").write_text(render_report(stats), encoding="utf-8")
    paths.report_path("source_reading_blocks_backlog_v0.7_a20.md").write_text(render_backlog(chapters), encoding="utf-8")
    return stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", default=VERSION)
    args = parser.parse_args()
    stats = build(args.project, args.version)
    print("Source reading blocks built")
    for key in ["total_blocks", "core_total", "extra_total", "min_per_letter", "max_per_letter", "average_length", "question_anchor_coverage"]:
        print(f"{key}: {stats[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
