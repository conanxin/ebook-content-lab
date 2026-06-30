#!/usr/bin/env python3
"""Build a private working letters_brief.json for a reading-guide project.

This builder reads private EPUB intake artifacts but writes only structured
metadata, section counts, chunk IDs, conservative title-derived briefs, and
non-quoting evidence references. It must not expose full text or long excerpts.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.lib.project_paths import from_project
except ModuleNotFoundError:
    from lib.project_paths import from_project


BODY_START = 6
BODY_END = 30
VERSION = "v0.7-A2"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
    return rows


def section_number(section_id: str) -> int | None:
    match = re.fullmatch(r"sec-(\d{3})", section_id or "")
    return int(match.group(1)) if match else None


def is_body_letter(section: dict[str, Any]) -> bool:
    n = section_number(str(section.get("section_id", "")))
    return n is not None and BODY_START <= n <= BODY_END


def safe_title(title: str) -> str:
    return " ".join((title or "").split()).strip()


def derive_brief(title: str) -> str:
    title = safe_title(title)
    if not title:
        return "本节为一封书信正文，当前 brief 仅依据结构元数据生成，待后续人工细读。"
    return f"本节对应《旅行人信札》中的“{title}”，当前 brief 仅依据标题与结构元数据生成，待后续人工细读。"


def derive_places(title: str) -> list[str]:
    title = safe_title(title)
    if not title:
        return []
    # Title-only heuristic: remove leading "第N封" and split by common separators.
    cleaned = re.sub(r"^第[一二三四五六七八九十百\d]+封\s*", "", title)
    cleaned = re.sub(r"\d+月\d+日|\d+日|[年月]", " ", cleaned)
    parts = re.split(r"[，,、/／—\-→：:\s]+", cleaned)
    places: list[str] = []
    for part in parts:
        part = part.strip(" 　。；;（）()[]【】")
        if len(part) >= 2 and part not in {"第", "封", "上", "下"} and part not in places:
            places.append(part)
    return places[:6]


def derive_themes(title: str, char_count: int, chunk_count: int) -> list[str]:
    themes = ["旅行书信"]
    if char_count >= 5000:
        themes.append("长篇行旅记录")
    if chunk_count >= 5:
        themes.append("多段叙述")
    if any(word in title for word in ["山", "峰", "岭", "峨嵋", "黄山", "雁荡"]):
        themes.append("山水行旅")
    if any(word in title for word in ["京", "沪", "苏州", "广州", "福州", "青岛", "西安", "成都", "昆明"]):
        themes.append("城市与旅途")
    return themes


def build_letters(project: str) -> dict[str, Any]:
    paths = from_project(project)
    sections_path = paths.private_dir / "book_sections.jsonl"
    chunks_path = paths.private_dir / "book_chunks.jsonl"
    if not sections_path.exists():
        raise FileNotFoundError(f"Missing required private intake artifact: {sections_path}")
    if not chunks_path.exists():
        raise FileNotFoundError(f"Missing required private intake artifact: {chunks_path}")

    sections = read_jsonl(sections_path)
    chunks = read_jsonl(chunks_path)

    chunks_by_section: dict[str, list[dict[str, Any]]] = {}
    for chunk in chunks:
        chunks_by_section.setdefault(str(chunk.get("section_id", "")), []).append(chunk)

    body_sections = [s for s in sections if is_body_letter(s)]
    body_sections.sort(key=lambda s: int(s.get("order", 0)))

    letters: list[dict[str, Any]] = []
    for idx, section in enumerate(body_sections, start=1):
        section_id = str(section["section_id"])
        title = safe_title(str(section.get("title", "")))
        section_chunks = sorted(
            chunks_by_section.get(section_id, []),
            key=lambda c: int(c.get("order", 0)),
        )
        chunk_ids = [str(c.get("chunk_id", "")) for c in section_chunks if c.get("chunk_id")]
        char_count = int(section.get("char_count", 0) or 0)
        paragraph_count = int(section.get("paragraph_count", 0) or 0)
        chunk_count = int(section.get("chunk_count", len(section_chunks)) or len(section_chunks))

        evidence_refs = [
            {
                "ref_id": f"{section_id}-structure",
                "section_id": section_id,
                "chunk_ids": chunk_ids[:3],
                "note": "Structural evidence only; no source text excerpt is included.",
            }
        ]

        letters.append(
            {
                "letter_id": f"letter-{idx:03d}",
                "section_id": section_id,
                "order": idx,
                "title": title,
                "char_count": char_count,
                "paragraph_count": paragraph_count,
                "chunk_count": chunk_count,
                "chunk_ids": chunk_ids,
                "brief": derive_brief(title),
                "places": derive_places(title),
                "themes": derive_themes(title, char_count, chunk_count),
                "evidence_refs": evidence_refs,
                "review_status": "auto_structural_draft",
            }
        )

    return {
        "project": paths.slug,
        "source_type": "epub",
        "status": "working-draft",
        "builder_version": VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "letter_count": len(letters),
        "section_range": {"start": "sec-006", "end": "sec-030"},
        "source_artifacts": {
            "sections": "private/book_sections.jsonl",
            "chunks": "private/book_chunks.jsonl",
            "identity": "working/book_identity.json",
            "identity_source": "working/book_identity_source.json",
        },
        "privacy_boundary": {
            "contains_full_text": False,
            "contains_long_excerpts": False,
            "evidence_mode": "structural_no_quote",
        },
        "letters": letters,
    }


def render_report(data: dict[str, Any]) -> str:
    letters = data.get("letters", [])
    lines = [
        "# Letters Brief Report v0.7-A2",
        "",
        f"- Project: `{data.get('project')}`",
        f"- Source type: `{data.get('source_type')}`",
        f"- Status: `{data.get('status')}`",
        f"- Letter count: `{data.get('letter_count')}`",
        f"- Section range: {data.get('section_range', {}).get('start')} → `{data.get('section_range', {}).get('end')}`",
        "",
        "## Privacy Boundary",
        "",
        "- No EPUB file is copied.",
        "- No full section text is included.",
        "- No long excerpts are included.",
        "- Evidence references are structural and non-quoting.",
        "",
        "## Letters",
        "",
        "| letter_id | section_id | title | chars | chunks | review_status |",
        "|---|---:|---|---:|---:|---|",
    ]
    for letter in letters:
        title = str(letter.get("title", "")).replace("|", "｜")
        lines.append(
            f"| {letter.get('letter_id')} | {letter.get('section_id')} | {title} | "
            f"{letter.get('char_count')} | {letter.get('chunk_count')} | {letter.get('review_status')} |"
        )
    lines.extend(
        [
            "",
            "## Next Step",
            "",
            "Run check_letters_brief.py to validate coverage and privacy boundary before any public JSON builder is introduced.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    args = parser.parse_args()

    paths = from_project(args.project)
    data = build_letters(args.project)

    output_path = paths.working_path("letters_brief.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report_path = paths.report_path("letters_brief_report_v0.7_a2.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(data), encoding="utf-8")

    print(f"Wrote: {output_path}")
    print(f"Wrote: {report_path}")
    print(f"Letters: {data['letter_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())