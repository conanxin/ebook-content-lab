from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PARA_RE = re.compile(r"\n\s*\n+")


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def emit_chunk(chunks: list[dict], parts: list[tuple[int, str]]) -> None:
    if not parts:
        return
    text = "\n\n".join(part for _, part in parts).strip()
    pages = [page for page, _ in parts]
    chunk_id = f"chunk-{len(chunks) + 1:04d}"
    chunks.append(
        {
            "chunk_id": chunk_id,
            "page_start": min(pages),
            "page_end": max(pages),
            "text": text,
            "char_count": len(text),
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-chars", type=int, default=3500)
    args = parser.parse_args()

    rows = read_jsonl(args.input)
    chunks: list[dict] = []
    current: list[tuple[int, str]] = []
    current_len = 0

    for row in rows:
        page = row["page"]
        text = row.get("text", "").strip()
        paragraphs = [p.strip() for p in PARA_RE.split(text) if p.strip()] or ([text] if text else [])
        for paragraph in paragraphs:
            para_len = len(paragraph)
            if current and current_len + para_len + 2 > args.max_chars:
                emit_chunk(chunks, current)
                current = []
                current_len = 0
            if para_len > args.max_chars:
                for start in range(0, para_len, args.max_chars):
                    piece = paragraph[start : start + args.max_chars]
                    if current:
                        emit_chunk(chunks, current)
                        current = []
                        current_len = 0
                    emit_chunk(chunks, [(page, piece)])
            else:
                current.append((page, paragraph))
                current_len += para_len + 2
    emit_chunk(chunks, current)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    print(f"Wrote {args.output} ({len(chunks)} chunks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
