from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CONTENT_TYPE_KEYWORDS: dict[str, list[str]] = {
    "route / travel / walking": [
        "徒步",
        "步行",
        "行程",
        "出发",
        "路线",
        "古道",
        "公里",
        "里程",
        "住宿",
        "补给",
        "从",
        "到",
    ],
    "history": ["历史", "元代", "大都", "上都", "驿路", "古", "明代", "清代", "蒙古", "忽必烈"],
    "biography": ["传记", "生平", "年谱", "出生", "逝世", "回忆录"],
    "fiction": ["小说", "故事", "情节", "主人公", "虚构"],
    "geography": ["地理", "地图", "山", "河", "关", "水库", "村", "镇", "草原"],
    "essay": ["随笔", "散文", "写在", "札记", "感想"],
    "technical": ["技术", "算法", "程序", "系统", "工程", "代码"],
}

PROJECT_TYPE_MAP: dict[str, list[str]] = {
    "route / travel / walking": ["route-map", "field-guide", "place-index", "reading-guide"],
    "history": ["timeline", "knowledge-map", "reading-guide"],
    "biography": ["timeline", "character-map", "reading-guide"],
    "fiction": ["character-map", "timeline", "reading-guide"],
    "geography": ["place-index", "knowledge-map", "field-guide"],
    "essay": ["reading-guide", "quote-atlas"],
    "technical": ["knowledge-map", "reading-guide"],
    "unknown": ["reading-guide"],
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def load_jsonl(path: Path | None) -> list[dict[str, Any]]:
    """Load a JSONL file; return empty list if path missing."""
    if not path or not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
    return rows


def load_epub_artifacts(project_dir: Path) -> dict[str, Any] | None:
    """Load the EPUB extraction artifacts produced by extract_epub.py.

    Priority:
      1. private/book_sections.jsonl
      2. private/book.md
      3. working/book_identity_source.json (metadata only)
    Returns None if none of these exist; the caller then falls back to the
    PDF/OCR path.
    """
    private_dir = project_dir / "private"
    working_dir = project_dir / "working"

    sections_path = private_dir / "book_sections.jsonl"
    book_md_path = private_dir / "book.md"
    source_path = working_dir / "book_identity_source.json"

    if not (sections_path.exists() or book_md_path.exists() or source_path.exists()):
        return None

    sections = load_jsonl(sections_path) if sections_path.exists() else []
    chunks = load_jsonl(private_dir / "book_chunks.jsonl") if (private_dir / "book_chunks.jsonl").exists() else []
    source_summary = read_json(source_path) if source_path.exists() else {}
    book_md_text = book_md_path.read_text(encoding="utf-8", errors="replace") if book_md_path.exists() else ""

    full_text = "\n\n".join(section.get("text", "") for section in sections) or book_md_text
    section_titles = [section.get("title", "") for section in sections if section.get("title")]
    chunk_titles = [chunk.get("section_title", "") for chunk in chunks if chunk.get("section_title")]
    metadata = source_summary.get("metadata", {}) if isinstance(source_summary, dict) else {}

    return {
        "sections": sections,
        "chunks": chunks,
        "book_md_text": book_md_text,
        "full_text": full_text,
        "section_titles": section_titles,
        "chunk_titles": chunk_titles,
        "source_summary": source_summary,
        "metadata": metadata,
        "extraction_status": source_summary.get("extraction_status") if isinstance(source_summary, dict) else None,
        "image_count": source_summary.get("image_count") if isinstance(source_summary, dict) else None,
    }


def warn_if_epub_needs_extraction(project_dir: Path) -> str | None:
    """If book.epub exists but no extraction artifacts exist, hint to run extract_epub.py."""
    private_dir = project_dir / "private"
    epub_path = private_dir / "source" / "book.epub"
    has_artifacts = any(
        (private_dir / name).exists()
        for name in ("book_sections.jsonl", "book.md", "book_chunks.jsonl")
    ) or (project_dir / "working" / "book_identity_source.json").exists()
    if epub_path.exists() and not has_artifacts:
        return f"EPUB present at {epub_path} but no extraction artifacts found. Run scripts/extract_epub.py first."
    return None


def load_pages(path: Path | None) -> list[dict[str, Any]]:
    if not path or not path.exists():
        return []
    pages: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
            text = row.get("text") or ""
            row["text"] = text
            row["char_count"] = int(row.get("char_count") or len(text))
            pages.append(row)
    return pages


def split_lines(text: str) -> list[str]:
    return [line.strip() for line in re.split(r"[\r\n]+", text) if line.strip()]


def normalize_space(text: str) -> str:
    return re.sub(r"[ \t\u3000]+", " ", text).strip()


def inspect_pdf(pdf_path: Path | None) -> dict[str, Any]:
    info: dict[str, Any] = {
        "path": str(pdf_path) if pdf_path else None,
        "exists": bool(pdf_path and pdf_path.exists()),
        "page_count": None,
        "sample_embedded_text_chars": None,
        "is_scanned_likely": "unknown",
        "inspection_error": None,
    }
    if not pdf_path or not pdf_path.exists():
        return info
    try:
        import fitz  # type: ignore

        doc = fitz.open(pdf_path)
        info["page_count"] = doc.page_count
        sample_pages = min(doc.page_count, 10)
        embedded_chars = 0
        for index in range(sample_pages):
            embedded_chars += len(doc[index].get_text("text") or "")
        avg = embedded_chars / sample_pages if sample_pages else 0
        info["sample_embedded_text_chars"] = round(avg, 2)
        info["is_scanned_likely"] = avg < 30
    except Exception as exc:  # pragma: no cover - depends on local PDF tooling
        info["inspection_error"] = str(exc)
    return info


def detect_language(text: str) -> str:
    if not text:
        return "unknown"
    sample = text[:200_000]
    chinese = len(re.findall(r"[\u4e00-\u9fff]", sample))
    latin = len(re.findall(r"[A-Za-z]", sample))
    total_letters = chinese + latin
    if total_letters == 0:
        return "unknown"
    if chinese / total_letters > 0.7:
        return "zh-Hans"
    if latin / total_letters > 0.7:
        return "en"
    return "mixed"


def extract_identity(first_text: str, project_data: dict[str, Any]) -> dict[str, Any]:
    lines = split_lines(first_text)
    joined = "\n".join(lines)

    title: str | None = None
    author: str | None = None
    publication_info: str | None = None
    publisher: str | None = None
    publication_date: str | None = None
    isbn: str | None = None
    evidence: list[dict[str, Any]] = []

    cip_match = re.search(r"([^\n/]{2,100})/([\u4e00-\u9fff·]{2,12})\s*著", joined)
    if cip_match:
        title = normalize_space(cip_match.group(1).strip(" ：:，,。."))
        author = normalize_space(cip_match.group(2))
        evidence.append({"field": "title_author", "quote": cip_match.group(0)[:120]})

    if not title:
        heading_match = re.search(r"^#\s*(.+?)\s+OCR\s*文本", first_text, flags=re.MULTILINE)
        if heading_match:
            title = normalize_space(heading_match.group(1))
            evidence.append({"field": "title", "quote": heading_match.group(0)[:120]})

    if not title:
        for line in lines[:20]:
            clean = normalize_space(line.replace("OCR 文本", ""))
            if 2 <= len(clean) <= 50 and not re.search(r"ISBN|出版社|NEWSTAR|定价|上架建议", clean):
                title = clean
                evidence.append({"field": "title", "quote": line[:120]})
                break

    if not author:
        for line in lines[:80]:
            match = re.fullmatch(r"([\u4e00-\u9fff·]{2,12})\s*[—\-－]*\s*著", normalize_space(line))
            if match:
                author = match.group(1)
                evidence.append({"field": "author", "quote": line[:120]})
                break

    pub_match = re.search(
        r"(?P<place>[\u4e00-\u9fff]{2,12})[：:]\s*(?P<publisher>[^，,\n]{2,40}出版社)[，,]\s*(?P<date>\d{4}(?:\.\d+)?)",
        joined,
    )
    if pub_match:
        publication_info = normalize_space(pub_match.group(0))
        publisher = normalize_space(pub_match.group("publisher"))
        publication_date = pub_match.group("date")
        evidence.append({"field": "publication_info", "quote": pub_match.group(0)[:120]})
    else:
        publisher_match = re.search(r"([\u4e00-\u9fff]{2,30}出版社)", joined)
        if publisher_match:
            publisher = publisher_match.group(1)
            evidence.append({"field": "publisher", "quote": publisher_match.group(0)[:120]})

    isbn_match = re.search(r"ISBN\s*([0-9\-]{10,20})", joined)
    if isbn_match:
        isbn = isbn_match.group(1)
        evidence.append({"field": "isbn", "quote": isbn_match.group(0)[:120]})

    if not title:
        title = project_data.get("book_title") or project_data.get("title") or None

    return {
        "title": title,
        "author": author,
        "publication_info": publication_info,
        "publisher": publisher,
        "publication_date": publication_date,
        "isbn": isbn,
        "evidence": evidence,
    }


def toc_score(text: str) -> int:
    lines = split_lines(text)
    if not lines:
        return 0
    head = "".join(lines[:3])
    score = 0
    if "目录" in head or lines[0] == "目":
        score += 5
    score += min(len(re.findall(r"从.{1,30}到.{1,30}", text)), 5)
    score += min(len(re.findall(r"\d{2,3}\s*[丨|】]", text)), 4)
    score += min(text.count("写在"), 2)
    score += min(len([line for line in lines if 4 <= len(line) <= 30]), 4)
    return score


def detect_toc_and_chapters(pages: list[dict[str, Any]]) -> dict[str, Any]:
    toc_pages: list[int] = []
    first_pages = pages[:60]
    for index, page in enumerate(first_pages):
        score = toc_score(page.get("text", ""))
        prev_is_toc = bool(toc_pages and page.get("page") == toc_pages[-1] + 1)
        if score >= 8 or (prev_is_toc and score >= 5):
            toc_pages.append(int(page.get("page")))

    chapter_candidates: list[dict[str, Any]] = []
    toc_set = set(toc_pages)
    for page in pages:
        page_no = int(page.get("page") or 0)
        text = page.get("text", "")
        if page_no in toc_set:
            for line in split_lines(text):
                clean = re.sub(r"^\d{1,3}\s*[丨|】]\s*", "", line)
                clean = re.sub(r"\s*\d{1,3}\s*$", "", clean)
                clean = normalize_space(clean.strip("丨|】"))
                if clean in {"目", "目录"} or len(clean) < 4 or len(clean) > 40:
                    continue
                if re.search(r"ISBN|定价|出版社|NEWSTAR", clean):
                    continue
                chapter_candidates.append({"title": clean, "source": "toc", "page": page_no})

    for page in pages:
        text = page.get("text", "")
        page_no = int(page.get("page") or 0)
        if page.get("char_count", len(text)) <= 120:
            lines = split_lines(text)
            if 1 <= len(lines) <= 8:
                heading = " / ".join(lines[:3])
                if 4 <= len(heading) <= 80 and not re.search(r"ISBN|定价|NEWSTAR|出版社", heading):
                    chapter_candidates.append({"title": heading, "source": "heading_page", "page": page_no})

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str]] = set()
    for item in chapter_candidates:
        key = (item["title"], int(item["page"]), item["source"])
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    return {
        "toc_page_range": [min(toc_pages), max(toc_pages)] if toc_pages else None,
        "toc_pages": toc_pages,
        "chapter_candidates": deduped[:80],
    }


def score_content_types(text: str) -> dict[str, int]:
    sample = text[:500_000]
    scores: dict[str, int] = {}
    for content_type, keywords in CONTENT_TYPE_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in {"从", "到"}:
                continue
            score += sample.count(keyword)
        if content_type == "route / travel / walking":
            score += len(re.findall(r"从.{1,25}到.{1,25}", sample)) * 3
            score += len(re.findall(r"\d+(?:\.\d+)?\s*(?:公里|千米|里)", sample))
        if content_type == "history" and re.search(r"上架建议[：:].*历史", sample):
            score += 100
        if content_type == "essay" and re.search(r"上架建议[：:].*随笔", sample):
            score += 100
        scores[content_type] = score
    return scores


def suggest_content_types(scores: dict[str, int]) -> list[str]:
    max_score = max(scores.values()) if scores else 0
    threshold = max(50, int(max_score * 0.08))
    selected = [content_type for content_type, score in scores.items() if score >= threshold]
    priority = [
        "route / travel / walking",
        "history",
        "geography",
        "essay",
        "biography",
        "fiction",
        "technical",
    ]
    selected.sort(key=lambda item: priority.index(item) if item in priority else len(priority))
    return selected[:5] or ["unknown"]


def suggest_project_types(content_types: list[str]) -> list[str]:
    suggestions: list[str] = []
    for content_type in content_types:
        for project_type in PROJECT_TYPE_MAP.get(content_type, []):
            if project_type not in suggestions:
                suggestions.append(project_type)
    return suggestions or PROJECT_TYPE_MAP["unknown"]


def ocr_status(pages: list[dict[str, Any]], book_md_path: Path | None, ocr_pdf_path: Path | None) -> dict[str, Any]:
    if not pages and not book_md_path:
        return {
            "status": "missing",
            "page_count": None,
            "needs_review_pages": [],
            "empty_pages": [],
            "average_chars_per_page": None,
            "ocr_pdf_exists": bool(ocr_pdf_path and ocr_pdf_path.exists()),
        }

    needs_review = [int(page.get("page")) for page in pages if page.get("needs_review")]
    empty_pages = [int(page.get("page")) for page in pages if not (page.get("text") or "").strip()]
    avg_chars = round(sum(page.get("char_count", 0) for page in pages) / len(pages), 2) if pages else None
    return {
        "status": "available",
        "page_count": len(pages) or None,
        "needs_review_pages": needs_review,
        "empty_pages": empty_pages,
        "average_chars_per_page": avg_chars,
        "ocr_pdf_exists": bool(ocr_pdf_path and ocr_pdf_path.exists()),
    }


def _epub_section(epub_summary: dict[str, Any] | None) -> str:
    if not epub_summary:
        return ""
    return f"""## EPUB Summary

- Extraction status: `{epub_summary.get('extraction_status') or 'unknown'}`
- Image count: `{epub_summary.get('image_count')}`
- Chapter count: `{epub_summary.get('chapter_count')}`
- Chunk count: `{epub_summary.get('chunk_count')}`
- Text char count: `{epub_summary.get('text_char_count')}`

"""


def build_report(identity: dict[str, Any]) -> str:
    book = identity["book"]
    ocr = identity["ocr_status"]
    toc = identity["toc"]
    sources = identity["sources"]

    def value(item: Any) -> str:
        if item is None or item == "" or item == []:
            return "unknown"
        return str(item)

    evidence_lines = []
    for item in book.get("evidence", []):
        evidence_lines.append(f"- `{item['field']}`: {item['quote']}")
    if not evidence_lines:
        evidence_lines.append("- unknown")

    chapter_lines = []
    for item in toc.get("chapter_candidates", [])[:40]:
        chapter_lines.append(f"- p{item['page']} [{item['source']}]: {item['title']}")
    if not chapter_lines:
        chapter_lines.append("- unknown")

    content_scores = "\n".join(
        f"- {name}: {score}" for name, score in sorted(identity["content_type_scores"].items(), key=lambda x: x[1], reverse=True)
    )

    needs_review_pages = ocr.get("needs_review_pages") or []
    needs_review_summary = ", ".join(str(page) for page in needs_review_pages[:40])
    if len(needs_review_pages) > 40:
        needs_review_summary += f" ... (+{len(needs_review_pages) - 40})"

    return f"""# Book Identity Report

Generated at: `{identity['generated_at']}`

Project: `{identity['project_slug']}`

## Sources

- PDF: `{value(sources.get('pdf'))}`
- Book Markdown: `{value(sources.get('book_md'))}`
- Cleaned pages JSONL: `{value(sources.get('book_pages_cleaned'))}`
- OCR PDF: `{value(sources.get('ocr_pdf'))}`
- EPUB: `{value(sources.get('epub'))}`
- EPUB sections JSONL: `{value(sources.get('epub_sections'))}`
- EPUB chunks JSONL: `{value(sources.get('epub_chunks'))}`
- EPUB source summary: `{value(sources.get('epub_source_summary'))}`

{f'''> ⚠️ {identity['extraction_warning']}''' if identity.get('extraction_warning') else ''}

## Identified Book

- Title: {value(book.get('title'))}
- Author: {value(book.get('author'))}
- Publisher: {value(book.get('publisher'))}
- Publication info: {value(book.get('publication_info'))}
- Publication date: {value(book.get('publication_date'))}
- ISBN: {value(book.get('isbn'))}
- Language: {value(book.get('language'))}
- Source type: {value(book.get('source_type'))}
- Scanned PDF likely: {value(book.get('is_scanned_likely'))}
- Total pages: {value(book.get('total_pages'))}
- Identity status: {value(identity.get('identity_status'))}

## Local Evidence

{chr(10).join(evidence_lines)}

## OCR Status

- Status: {value(ocr.get('status'))}
- OCR page count: {value(ocr.get('page_count'))}
- OCR PDF exists: {value(ocr.get('ocr_pdf_exists'))}
- Empty text pages: {len(ocr.get('empty_pages') or [])}
- Needs review pages: {len(needs_review_pages)}
- Needs review page sample: {value(needs_review_summary)}
- Average chars per page: {value(ocr.get('average_chars_per_page'))}

## Table of Contents and Chapters

- TOC page range: {value(toc.get('toc_page_range'))}
- TOC pages: {value(toc.get('toc_pages'))}

Chapter candidates:

{chr(10).join(chapter_lines)}

## Content Type Suggestions

Suggested content types:

{chr(10).join(f'- {item}' for item in identity.get('suggested_content_types', []))}

Scores:

{content_scores}

Suggested project types:

{chr(10).join(f'- {item}' for item in identity.get('suggested_project_types', []))}

{_epub_section(identity.get('epub_summary'))}

## Notes

- This report uses only local project files and does not perform external web search.
- Unknown fields are left as `unknown` or `null`; no author, publisher, route, or content claim is invented.
- OCR review flags come from the existing cleaned OCR page data.
"""


def identify(project_dir: Path, output_path: Path) -> dict[str, Any]:
    root = repo_root()
    project_dir = project_dir.resolve()
    project_json_path = project_dir / "project.json"
    if not project_json_path.exists():
        raise FileNotFoundError(f"Missing project.json: {project_json_path}")

    project_data = read_json(project_json_path)
    private_dir = project_dir / "private"

    epub_artifacts = load_epub_artifacts(project_dir)
    extraction_warning = warn_if_epub_needs_extraction(project_dir)

    # dadou-shangdu (PDF/OCR) projects have their artefacts in the global data/
    # directory; second-reading-guide (EPUB) is self-contained in private/.
    # Only fall back to global data/ when this project has no EPUB and no
    # project-private artefacts, to avoid cross-project contamination.
    is_legacy_pdf_project = (
        not epub_artifacts
        and not (private_dir / "book.md").exists()
        and not (private_dir / "book_pages.cleaned.jsonl").exists()
    )

    pdf_path = first_existing([private_dir / "source" / "book.pdf"])
    if is_legacy_pdf_project:
        # dadou-shangdu legacy: its PDF lives at <repo>/source/book.pdf.
        pdf_path = first_existing([private_dir / "source" / "book.pdf", root / "source" / "book.pdf"])
    book_md_path = first_existing([private_dir / "book.md"])
    pages_path = first_existing([private_dir / "book_pages.cleaned.jsonl"])
    ocr_pdf_path = first_existing([private_dir / "ocr" / "book_ocr.pdf"])
    epub_path = first_existing([private_dir / "source" / "book.epub"])

    if is_legacy_pdf_project:
        book_md_path = first_existing([private_dir / "book.md", root / "data" / "book.md"])
        pages_path = first_existing([private_dir / "book_pages.cleaned.jsonl", root / "data" / "book_pages.cleaned.jsonl"])
        ocr_pdf_path = first_existing([private_dir / "ocr" / "book_ocr.pdf", root / "data" / "ocr" / "book_ocr.pdf"])

    pages = load_pages(pages_path)
    book_md_text = book_md_path.read_text(encoding="utf-8", errors="replace") if book_md_path and book_md_path.exists() else ""
    page_text = "\n".join(page.get("text", "") for page in pages)
    epub_full_text = epub_artifacts.get("full_text", "") if epub_artifacts else ""
    full_text = epub_full_text or book_md_text or page_text
    first_text = (
        "\n".join(page.get("text", "") for page in pages[:20])
        if pages
        else (epub_full_text[:30_000] if epub_full_text else (book_md_text[:30_000] if book_md_text else ""))
    )

    pdf_info = inspect_pdf(pdf_path)
    identity_fields: dict[str, Any]
    if epub_artifacts and epub_artifacts.get("metadata"):
        # EPUB projects: trust the EPUB OPF metadata. extract_identity's heuristics
        # are tuned for PDF/OCR front-matter and can latch onto chapter titles.
        epub_meta = epub_artifacts["metadata"]
        identity_fields = {
            "title": epub_meta.get("title") or None,
            "author": epub_meta.get("creator") or None,
            "publication_info": epub_meta.get("description") or None,
            "publisher": epub_meta.get("publisher") or None,
            "publication_date": epub_meta.get("date") or None,
            "isbn": epub_meta.get("identifier") or None,
            "evidence": [
                {"field": "epub_opf", "quote": f"{key}={value}"}
                for key, value in epub_meta.items()
                if value
            ],
        }
    else:
        identity_fields = extract_identity(first_text, project_data)
        # If extract_identity fell back to a short, non-book-like title (e.g. a
        # section heading), and the OPF metadata does NOT agree, prefer
        # whatever the project.json already has.
        if identity_fields.get("title") and len(identity_fields["title"]) <= 8:
            fallback_title = project_data.get("book_title") or project_data.get("title")
            if fallback_title and fallback_title not in identity_fields["title"]:
                identity_fields["title"] = fallback_title
        # Cross-fill from OPF metadata if available (defensive, even if not EPUB).
        if epub_artifacts:
            metadata = epub_artifacts.get("metadata", {}) or {}
            for key, mapped in {
                "title": "title",
                "creator": "author",
                "language": "language",
                "publisher": "publisher",
                "date": "publication_date",
                "identifier": "isbn",
                "description": "publication_info",
            }.items():
                value = metadata.get(key)
                if value and not identity_fields.get(mapped):
                    identity_fields[mapped] = value
    language = detect_language(full_text) if full_text else "unknown"

    ocr = ocr_status(pages, book_md_path, ocr_pdf_path)
    toc = detect_toc_and_chapters(pages)
    if epub_artifacts and epub_artifacts.get("sections"):
        # Build TOC candidates from EPUB sections so we don't depend on PDF/OCR
        # heuristics. The first section can be a cover/titlepage with empty text;
        # skip blank titles.
        toc = {
            "toc_page_range": None,
            "toc_pages": [],
            "chapter_candidates": [
                {
                    "title": section.get("title") or f"sec-{index + 1:03d}",
                    "source": "epub_section",
                    "page": index + 1,
                }
                for index, section in enumerate(epub_artifacts["sections"])
                if (section.get("title") or "").strip()
            ][:80],
        }
    content_scores = score_content_types(full_text)
    content_types = suggest_content_types(content_scores)
    project_types = suggest_project_types(content_types)

    total_pages = pdf_info.get("page_count") or ocr.get("page_count")
    source_type = project_data.get("source_type") or "unknown"
    if pdf_info.get("is_scanned_likely") is True:
        source_type = "scanned_pdf"
    elif epub_artifacts and epub_path and epub_path.exists():
        # EPUB takes precedence when it is the actual source.
        source_type = "epub"
        if epub_artifacts.get("extraction_status") == "ok" and not total_pages:
            total_pages = len(epub_artifacts.get("sections", []))

    book = {
        "title": identity_fields.get("title"),
        "author": identity_fields.get("author"),
        "publication_info": identity_fields.get("publication_info"),
        "publisher": identity_fields.get("publisher"),
        "publication_date": identity_fields.get("publication_date"),
        "isbn": identity_fields.get("isbn"),
        "source_type": source_type,
        "language": language,
        "is_scanned_likely": pdf_info.get("is_scanned_likely"),
        "total_pages": total_pages,
        "evidence": identity_fields.get("evidence", []),
    }

    if book["title"] and book["author"]:
        identity_status = "identified"
    elif book["title"] or book["author"]:
        identity_status = "partial"
    else:
        identity_status = "unknown"

    result = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "project_slug": project_dir.name,
        "identity_status": identity_status,
        "sources": {
            "pdf": str(pdf_path) if pdf_path else None,
            "book_md": str(book_md_path) if book_md_path else None,
            "book_pages_cleaned": str(pages_path) if pages_path else None,
            "ocr_pdf": str(ocr_pdf_path) if ocr_pdf_path else None,
            "epub": str(epub_path) if epub_path else None,
            "epub_sections": str(private_dir / "book_sections.jsonl") if (private_dir / "book_sections.jsonl").exists() else None,
            "epub_chunks": str(private_dir / "book_chunks.jsonl") if (private_dir / "book_chunks.jsonl").exists() else None,
            "epub_source_summary": str(project_dir / "working" / "book_identity_source.json") if (project_dir / "working" / "book_identity_source.json").exists() else None,
        },
        "extraction_warning": extraction_warning,
        "book": book,
        "pdf_inspection": pdf_info,
        "ocr_status": ocr,
        "toc": toc,
        "content_type_scores": content_scores,
        "suggested_content_types": content_types,
        "suggested_project_types": project_types,
        "epub_summary": {
            "extraction_status": epub_artifacts.get("extraction_status") if epub_artifacts else None,
            "image_count": epub_artifacts.get("image_count") if epub_artifacts else None,
            "chapter_count": len(epub_artifacts.get("sections", [])) if epub_artifacts else 0,
            "chunk_count": len(epub_artifacts.get("chunks", [])) if epub_artifacts else 0,
            "text_char_count": sum(
                len(section.get("text", "")) for section in (epub_artifacts.get("sections", []) if epub_artifacts else [])
            ),
        }
        if epub_artifacts
        else None,
    }

    working_json_path = project_dir / "working" / "book_identity.json"
    write_json(working_json_path, result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_report(result), encoding="utf-8")

    project_data["book"] = {key: value for key, value in book.items() if key != "evidence"}
    project_data["suggested_content_types"] = content_types
    project_data["suggested_project_types"] = project_types
    project_data["identity_status"] = identity_status
    write_json(project_json_path, project_data)

    return result


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Identify ebook metadata and content type from local project files.")
    parser.add_argument("--project", required=True, help="Project directory, for example projects/dadou-shangdu.")
    parser.add_argument("--output", required=True, help="Markdown report path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        result = identify(Path(args.project), Path(args.output))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Identity status: {result['identity_status']}")
    print(f"Title: {result['book'].get('title') or 'unknown'}")
    print(f"Author: {result['book'].get('author') or 'unknown'}")
    print("Suggested content types: " + ", ".join(result.get("suggested_content_types", [])))
    print("Suggested project types: " + ", ".join(result.get("suggested_project_types", [])))
    print(f"Report: {Path(args.output)}")
    print(f"JSON: {Path(args.project) / 'working' / 'book_identity.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
