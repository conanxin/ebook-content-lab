from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


PAGE_NUMBER_RE = re.compile(r"^\s*[-—–]?\s*\d{1,4}\s*[-—–]?\s*$")
SPACE_RE = re.compile(r"[ \t\u3000]+")
BLANK_RE = re.compile(r"\n{3,}")


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def clean_text(text: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    original_len = len(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    lines = []
    for raw in text.splitlines():
        line = SPACE_RE.sub(" ", raw).strip()
        if PAGE_NUMBER_RE.match(line):
            notes.append("removed isolated page number")
            continue
        # Drop very short repeated ornamental lines, but keep Chinese text.
        if len(line) <= 2 and line in {"|", "||", "_", "__", "·", "•"}:
            notes.append("removed ornamental noise")
            continue
        lines.append(line)
    text = "\n".join(lines)
    text = re.sub(r"([，。；：、！？])\s+", r"\1", text)
    text = re.sub(r"\s+([，。；：、！？])", r"\1", text)
    text = BLANK_RE.sub("\n\n", text).strip()
    if len(text) < original_len * 0.5 and original_len > 200:
        notes.append("large cleanup delta")
    return text, sorted(set(notes))


def suspect_text(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < 80:
        return True
    bad = sum(1 for ch in stripped if ch in "�□■◆◇")
    latin = sum(1 for ch in stripped if ch.isascii() and ch.isalpha())
    chinese = sum(1 for ch in stripped if "\u4e00" <= ch <= "\u9fff")
    return bad > 5 or (latin > chinese * 1.2 and chinese < 50)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rows = read_jsonl(args.input)
    cleaned = []
    note_counter: Counter[str] = Counter()
    review_pages = []
    for row in rows:
        text, notes = clean_text(row.get("text", ""))
        needs_review = bool(row.get("needs_review")) or suspect_text(text)
        if needs_review:
            review_pages.append(row["page"])
        for note in notes:
            note_counter[note] += 1
        cleaned.append(
            {
                **row,
                "text": text,
                "char_count": len(text),
                "needs_review": needs_review,
                "cleaning_notes": notes,
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output, cleaned)

    total_chars = sum(r["char_count"] for r in cleaned)
    report = [
        "# OCR 清洗报告",
        "",
        f"- Generated at: {datetime.now().isoformat(timespec='seconds')}",
        f"- 输入: `{args.input}`",
        f"- 输出: `{args.output}`",
        f"- 页数: {len(cleaned)}",
        f"- 清洗后总字符数: {total_chars}",
        f"- 需复核页数: {len(review_pages)}",
        "",
        "## 清洗动作统计",
        "",
    ]
    if note_counter:
        for note, count in note_counter.most_common():
            report.append(f"- {note}: {count}")
    else:
        report.append("- 无明显清洗动作")
    report.extend(["", "## 需复核页码", "", ", ".join(map(str, review_pages[:300])) if review_pages else "无"])
    (ROOT / "data" / "ocr_cleaning_report.md").write_text("\n".join(report), encoding="utf-8")
    print(f"Wrote {args.output}")
    print(f"Wrote {ROOT / 'data' / 'ocr_cleaning_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
