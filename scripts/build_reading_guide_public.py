#!/usr/bin/env python3
"""Build conservative public reading-guide JSON files from letters_brief.

This builder intentionally avoids copying EPUB text, section text, long excerpts,
or private absolute paths. Public outputs are metadata-derived structural drafts.
"""

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


SCHEMA_VERSION = "reading-guide.v0.2"
STATUS = "draft"
VERSION = "v0.7-A3"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def safe_book(identity: dict[str, Any], identity_source: dict[str, Any]) -> dict[str, Any]:
    book = identity.get("book", {}) if isinstance(identity.get("book"), dict) else {}
    metadata = identity_source.get("metadata", {}) if isinstance(identity_source.get("metadata"), dict) else {}
    return {
        "title": book.get("title") or metadata.get("title") or "旅行人信札",
        "author": book.get("author") or metadata.get("creator") or "陈嘉映",
        "language": book.get("language") or metadata.get("language") or "zh-Hans",
        "publisher": book.get("publisher") or metadata.get("publisher"),
        "date": book.get("date") or metadata.get("date"),
        "isbn": book.get("isbn") or metadata.get("identifier"),
        "source_type": "epub",
    }


def structural_ref(ref_id: str, section_id: str | None = None, letter_id: str | None = None) -> dict[str, Any]:
    ref: dict[str, Any] = {
        "ref_id": ref_id,
        "evidence_mode": "structural_no_quote",
        "note": "Structural reference only; no source text excerpt is included.",
    }
    if section_id:
        ref["section_id"] = section_id
    if letter_id:
        ref["letter_id"] = letter_id
    return ref


def build_book_overview(book: dict[str, Any], letters: list[dict[str, Any]]) -> dict[str, Any]:
    place_count = len({p for letter in letters for p in letter.get("places", [])})
    theme_count = len({t for letter in letters for t in letter.get("themes", [])})
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "book": book,
        "one_sentence_summary": f"《{book.get('title', '旅行人信札')}》当前公开导读基于 EPUB 结构与 {len(letters)} 封正文书信的标题、章节统计和工作层结构摘要生成。",
        "reading_purpose": "帮助读者先按书信顺序、地点线索和主题标签建立阅读骨架；当前版本不替代逐章细读。",
        "structure_overview": {
            "body_letter_count": len(letters),
            "section_range": {"start": "sec-006", "end": "sec-030"},
            "place_count_from_titles": place_count,
            "theme_count_from_structural_tags": theme_count,
            "source_mode": "metadata_and_letters_brief",
        },
        "how_to_use": [
            "先浏览章节导读卡，了解 25 封书信的顺序与地点线索。",
            "再查看主题概念，观察哪些主题在多封信中反复出现。",
            "问题列表适合作为初读提示，不作为最终学术判断。",
        ],
        "limitations": [
            "当前为 draft：内容由结构化元数据和 working/letters_brief.json 生成。",
            "没有公开 EPUB 正文、完整章节正文或长段摘录。",
            "概念、问题和结构说明仍需后续人工复核。",
        ],
        "evidence_refs": [
            structural_ref("overview-letters-brief"),
            structural_ref("overview-book-identity"),
        ],
    }


def build_chapter_cards(letters: list[dict[str, Any]]) -> dict[str, Any]:
    cards: list[dict[str, Any]] = []
    for letter in letters:
        cards.append(
            {
                "chapter_id": f"chapter-{int(letter.get('order', 0)):03d}",
                "letter_id": letter.get("letter_id"),
                "section_id": letter.get("section_id"),
                "order": letter.get("order"),
                "title": letter.get("title"),
                "summary": letter.get("brief"),
                "places": letter.get("places", []),
                "themes": letter.get("themes", []),
                "char_count": letter.get("char_count"),
                "paragraph_count": letter.get("paragraph_count"),
                "chunk_count": letter.get("chunk_count"),
                "evidence_refs": letter.get(
                    "evidence_refs",
                    [structural_ref("chapter-structural", letter.get("section_id"), letter.get("letter_id"))],
                ),
                "review_status": "auto_structural_draft",
            }
        )
    return {"chapters": cards}


def build_key_concepts(letters: list[dict[str, Any]]) -> dict[str, Any]:
    theme_to_letters: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for letter in letters:
        for theme in letter.get("themes", []):
            theme_to_letters[str(theme)].append(letter)

    concepts = []
    for idx, (theme, related) in enumerate(sorted(theme_to_letters.items(), key=lambda kv: (-len(kv[1]), kv[0])), start=1):
        concepts.append(
            {
                "concept_id": f"concept-{idx:03d}",
                "label": theme,
                "description": f"结构化主题“{theme}”由章节标题、篇幅和 A2 working 层主题标签聚合而来，需后续人工复核。",
                "related_letters": [
                    {
                        "letter_id": letter.get("letter_id"),
                        "section_id": letter.get("section_id"),
                        "title": letter.get("title"),
                    }
                    for letter in related
                ],
                "evidence_refs": [
                    structural_ref(f"concept-{idx:03d}-structural", letter.get("section_id"), letter.get("letter_id"))
                    for letter in related[:5]
                ],
                "review_status": "auto_structural_draft",
            }
        )
    return {"concepts": concepts}


def build_quote_index(letters: list[dict[str, Any]]) -> dict[str, Any]:
    entries = []
    for letter in letters:
        entries.append(
            {
                "quote_id": f"quote-placeholder-{int(letter.get('order', 0)):03d}",
                "letter_id": letter.get("letter_id"),
                "section_id": letter.get("section_id"),
                "quote_mode": "structural_no_quote",
                "quote": "",
                "note": "No source quote is published in v0.7-A3; this entry preserves structural reference only.",
                "evidence_refs": [structural_ref("quote-structural-no-quote", letter.get("section_id"), letter.get("letter_id"))],
                "review_status": "awaiting_manual_quote_review",
            }
        )
    return {
        "quote_mode": "structural_no_quote",
        "quotes": entries,
    }


def build_reading_questions(letters: list[dict[str, Any]]) -> dict[str, Any]:
    questions = [
        {
            "question_id": "book-question-001",
            "scope": "book",
            "question": "这 25 封书信如何按照行程顺序展开出一条阅读路线？",
            "basis": "Derived from letter order and title-level route structure.",
            "review_status": "auto_structural_draft",
        }
    ]
    for letter in letters:
        title = letter.get("title") or "本封书信"
        places = letter.get("places", [])
        place_hint = "、".join(places[:3]) if places else "标题中的地点线索"
        questions.append(
            {
                "question_id": f"letter-question-{int(letter.get('order', 0)):03d}",
                "scope": "letter",
                "letter_id": letter.get("letter_id"),
                "section_id": letter.get("section_id"),
                "question": f"阅读“{title}”时，可以如何把 {place_hint} 与本封书信的行旅结构联系起来？",
                "basis": "Derived from title, places, and structural themes only.",
                "review_status": "auto_structural_draft",
            }
        )
    return {"questions": questions}


def wrap_payload(book: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "book": book,
        **payload,
    }


def render_report(outputs: dict[str, dict[str, Any]]) -> str:
    lines = [
        "# Reading Guide Public Report v0.7-A3",
        "",
        "- Status: `draft`",
        "- Schema version: `reading-guide.v0.2`",
        "- Source mode: `letters_brief_structural`",
        "",
        "## Generated Files",
        "",
        "| file | main count |",
        "|---|---:|",
        f"| book_overview.json | 1 |",
        f"| chapter_reading_cards.json | {len(outputs['chapter_reading_cards.json'].get('chapters', []))} |",
        f"| key_concepts.json | {len(outputs['key_concepts.json'].get('concepts', []))} |",
        f"| quote_index.json | {len(outputs['quote_index.json'].get('quotes', []))} |",
        f"| reading_questions.json | {len(outputs['reading_questions.json'].get('questions', []))} |",
        "",
        "## Privacy Boundary",
        "",
        "- No EPUB text is copied.",
        "- No full section text is copied.",
        "- Quote index uses `structural_no_quote` mode.",
        "- Private source paths are not exported.",
        "",
    ]
    return "\n".join(lines)


def build(project: str) -> dict[str, dict[str, Any]]:
    paths = from_project(project)
    letters_brief = read_json(paths.working_path("letters_brief.json"))
    identity = read_json(paths.book_identity_json)
    identity_source = read_json(paths.book_identity_source_json)

    letters = letters_brief.get("letters", [])
    book = safe_book(identity, identity_source)

    outputs = {
        "book_overview.json": build_book_overview(book, letters),
        "chapter_reading_cards.json": wrap_payload(book, build_chapter_cards(letters)),
        "key_concepts.json": wrap_payload(book, build_key_concepts(letters)),
        "quote_index.json": wrap_payload(book, build_quote_index(letters)),
        "reading_questions.json": wrap_payload(book, build_reading_questions(letters)),
    }

    for name, payload in outputs.items():
        write_json(paths.public_path(name), payload)
        write_json(paths.web_project_path(name), payload)

    report_path = paths.report_path("reading_guide_public_report_v0.7_a3.md")
    report_path.write_text(render_report(outputs), encoding="utf-8")

    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    args = parser.parse_args()

    outputs = build(args.project)
    print("Wrote public reading-guide files:")
    for name in outputs:
        print(f"- {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
