from __future__ import annotations

"""Extract metadata, table of contents, and chapter text from an EPUB file.

This script only writes to the project's private/ and working/ directories.
It never modifies public/ or web/public/. It does not perform OCR.
"""

import argparse
import json
import re
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


EPUB_NS = {
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
    "ncx": "http://www.daisy.org/z3986/2005/ncx/",
    "container": "urn:oasis:names:tc:opendocument:xmlns:container",
}


class _TextExtractor(HTMLParser):
    """Walk an XHTML/HTML file and emit a list of (kind, text) blocks.

    We don't try to rebuild structure; we just want clean paragraph text plus
    the heading hierarchy. Script/style/nav are dropped entirely.
    """

    BLOCK_TAGS = {"p", "div", "section", "article", "li", "blockquote"}
    SKIP_TAGS = {"script", "style", "nav", "aside", "head", "meta", "link"}
    HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._heading_stack: list[tuple[str, str]] = []  # (level, text)
        self._current_text: list[str] = []
        self._current_kind: str | None = None
        self._current_tag: str | None = None
        self.blocks: list[dict[str, Any]] = []
        self._inline_text: list[str] = []
        self._headings: list[dict[str, str]] = []

    # ---- HTMLParser callbacks ----
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        ltag = tag.lower()
        if ltag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if ltag in self.BLOCK_TAGS:
            self._flush_inline()
        if ltag in self.HEADING_TAGS:
            self._current_tag = ltag
            self._current_kind = "heading"
            self._current_text = []

    def handle_endtag(self, tag: str) -> None:
        ltag = tag.lower()
        if ltag in self.SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return
        if ltag in self.HEADING_TAGS and self._current_kind == "heading":
            text = "".join(self._current_text).strip()
            if text:
                self._headings.append({"level": ltag, "text": text})
            self._current_kind = None
            self._current_text = []
            self._current_tag = None
        if ltag in self.BLOCK_TAGS:
            self._flush_inline()

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._current_kind == "heading":
            self._current_text.append(data)
            return
        if data.strip():
            self._inline_text.append(data)

    # ---- helpers ----
    def _flush_inline(self) -> None:
        if not self._inline_text:
            return
        text = "".join(self._inline_text)
        text = re.sub(r"[ \t\u3000]+", " ", text).strip()
        if text:
            self.blocks.append({"kind": "paragraph", "text": text})
        self._inline_text = []


def read_opf(zf: zipfile.ZipFile, opf_path: str) -> dict[str, Any]:
    with zf.open(opf_path) as handle:
        tree = ET.parse(handle)
    root = tree.getroot()
    metadata: dict[str, Any] = {
        "title": None,
        "creator": None,
        "language": None,
        "publisher": None,
        "date": None,
        "identifier": None,
        "description": None,
        "rights": None,
    }
    for child in root.find("opf:metadata", EPUB_NS) or []:
        tag = child.tag.split("}", 1)[-1]
        text = (child.text or "").strip()
        if tag == "title":
            metadata["title"] = text
        elif tag == "creator":
            metadata["creator"] = text
        elif tag == "language":
            metadata["language"] = text
        elif tag == "publisher":
            metadata["publisher"] = text
        elif tag == "date":
            metadata["date"] = text
        elif tag == "description":
            metadata["description"] = text
        elif tag == "rights":
            metadata["rights"] = text
        elif tag == "identifier" and not metadata["identifier"]:
            metadata["identifier"] = text

    manifest: dict[str, str] = {}
    for item in root.find("opf:manifest", EPUB_NS) or []:
        item_id = item.attrib.get("id", "")
        href = item.attrib.get("href", "")
        media = item.attrib.get("media-type", "")
        if item_id and href:
            manifest[item_id] = {"href": href, "media_type": media}

    spine: list[str] = []
    for item in root.find("opf:spine", EPUB_NS) or []:
        idref = item.attrib.get("idref", "")
        if idref:
            spine.append(idref)

    return {"metadata": metadata, "manifest": manifest, "spine": spine}


def resolve_href(opf_path: str, href: str) -> str:
    """Resolve a relative href against the OPF file path."""
    base_dir = Path(opf_path).parent
    combined = (base_dir / href).as_posix()
    parts: list[str] = []
    for part in combined.split("/"):
        if part == "..":
            if parts:
                parts.pop()
        elif part and part != ".":
            parts.append(part)
    return "/".join(parts)


def read_ncx(zf: zipfile.ZipFile, ncx_path: str) -> list[dict[str, Any]]:
    """Read a NCX 2.0 file and return a flat list of navPoints."""
    with zf.open(ncx_path) as handle:
        tree = ET.parse(handle)
    root = tree.getroot()
    navmap = root.find("ncx:navMap", EPUB_NS)
    if navmap is None:
        return []
    entries: list[dict[str, Any]] = []

    def walk(node: ET.Element, depth: int) -> None:
        for child in node:
            if not child.tag.endswith("navPoint"):
                continue
            label = child.find("ncx:navLabel/ncx:text", EPUB_NS)
            content = child.find("ncx:content", EPUB_NS)
            title = (label.text or "").strip() if label is not None else ""
            src = (content.attrib.get("src", "") if content is not None else "").strip()
            play_order = child.attrib.get("playOrder", "")
            try:
                order = int(play_order) if play_order else len(entries) + 1
            except ValueError:
                order = len(entries) + 1
            entries.append({"title": title, "src": src, "order": order, "depth": depth})
            walk(child, depth + 1)

    walk(navmap, 1)
    return entries


def read_nav_xhtml(zf: zipfile.ZipFile, nav_path: str) -> list[dict[str, Any]]:
    """Read a nav.xhtml file (EPUB 3) and return a flat list of links."""
    with zf.open(nav_path) as handle:
        data = handle.read()
    text = data.decode("utf-8", errors="replace")
    extractor = _TextExtractor()
    extractor.feed(text)
    # Look for anchor links inside <a href="..."> to extract chapter titles
    pattern = re.compile(
        r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL
    )
    entries: list[dict[str, Any]] = []
    for match in pattern.finditer(text):
        href = match.group(1).strip()
        inner = re.sub(r"<[^>]+>", "", match.group(2))
        inner = re.sub(r"\s+", " ", inner).strip()
        if not inner or len(inner) > 200:
            continue
        entries.append({"title": inner, "src": href, "order": len(entries) + 1, "depth": 1})
    return entries


def extract_chapter_text(zf: zipfile.ZipFile, item_path: str) -> dict[str, Any]:
    """Extract a single XHTML/HTML file into paragraphs and headings."""
    with zf.open(item_path) as handle:
        data = handle.read()
    text = data.decode("utf-8", errors="replace")
    extractor = _TextExtractor()
    extractor.feed(text)
    return {
        "headings": extractor._headings,
        "paragraphs": [block["text"] for block in extractor.blocks if block["kind"] == "paragraph"],
    }


def infer_section_title(headings: list[dict[str, str]], fallback: str) -> str:
    for heading in headings:
        if heading.get("level") in {"h1", "h2"} and heading.get("text"):
            return heading["text"]
    for heading in headings:
        if heading.get("text"):
            return heading["text"]
    return fallback


def chunk_paragraphs(paragraphs: list[str], section_id: str, section_title: str, target_chars: int = 1200) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    buffer: list[str] = []
    buffer_chars = 0
    chunk_index = 0

    def flush() -> None:
        nonlocal buffer, buffer_chars, chunk_index
        if not buffer:
            return
        joined = "\n\n".join(buffer).strip()
        if not joined:
            buffer = []
            buffer_chars = 0
            return
        chunk_index += 1
        chunks.append(
            {
                "chunk_id": f"chunk-{section_id}-{chunk_index:03d}",
                "section_id": section_id,
                "section_title": section_title,
                "order": chunk_index,
                "text": joined,
                "char_count": len(joined),
            }
        )
        buffer = []
        buffer_chars = 0

    for paragraph in paragraphs:
        if not paragraph:
            continue
        if buffer_chars + len(paragraph) > target_chars and buffer:
            flush()
        buffer.append(paragraph)
        buffer_chars += len(paragraph)
    flush()
    return chunks


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract metadata, TOC, and chapter text from an EPUB.")
    parser.add_argument("--project", required=True, help="Path to projects/<slug>.")
    args = parser.parse_args()

    project_dir = Path(args.project).resolve()
    epub_path = project_dir / "private" / "source" / "book.epub"
    if not epub_path.exists():
        print(f"ERROR: EPUB not found: {epub_path}", file=sys.stderr)
        return 1

    private_dir = project_dir / "private"
    working_dir = project_dir / "working"
    reports_dir = project_dir / "reports"
    private_dir.mkdir(parents=True, exist_ok=True)
    working_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    findings: list[dict[str, str]] = []
    image_count = 0
    file_size = epub_path.stat().st_size

    try:
        with zipfile.ZipFile(epub_path) as zf:
            names = zf.namelist()
            mimetype_files = [n for n in names if n == "mimetype"]
            mimetype_content = zf.read("mimetype").decode("ascii", errors="replace").strip() if mimetype_files else ""
            container_xml = "META-INF/container.xml" in names
            try:
                container_tree = ET.fromstring(zf.read("META-INF/container.xml"))
            except Exception as exc:
                findings.append({"severity": "error", "message": f"container.xml parse failed: {exc}"})
                container_tree = None

            opf_path: str | None = None
            if container_tree is not None:
                for rootfiles in container_tree.findall("container:rootfiles", EPUB_NS):
                    for rootfile in rootfiles.findall("container:rootfile", EPUB_NS):
                        full_path = rootfile.attrib.get("full-path", "")
                        if full_path:
                            opf_path = full_path
                            break
                    if opf_path:
                        break

            if not opf_path or opf_path not in names:
                findings.append({"severity": "error", "message": "OPF not found inside EPUB."})
                return _write_reports(project_dir, working_dir, reports_dir, findings, file_size, 0, 0, 0, image_count, [])

            opf = read_opf(zf, opf_path)
            manifest = opf["manifest"]
            spine_ids = opf["spine"]
            metadata = opf["metadata"]

            rights_files = [n for n in names if n.startswith("META-INF/rights.xml")]
            if rights_files:
                findings.append({"severity": "warning", "message": "META-INF/rights.xml present — possible DRM."})

            image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
            for name in names:
                if Path(name).suffix.lower() in image_extensions:
                    image_count += 1

            ncx_id = next((item_id for item_id, info in manifest.items() if info["media_type"] == "application/x-dtbncx+xml"), None)
            nav_id = next(
                (
                    item_id
                    for item_id, info in manifest.items()
                    if info["media_type"] == "application/xhtml+xml" and "nav" in info["href"].lower()
                ),
                None,
            )

            toc_entries: list[dict[str, Any]] = []
            if nav_id and nav_id in manifest:
                toc_entries = read_nav_xhtml(zf, resolve_href(opf_path, manifest[nav_id]["href"]))
                findings.append({"severity": "info", "message": f"nav.xhtml found with {len(toc_entries)} entries."})
            elif ncx_id and ncx_id in manifest:
                toc_entries = read_ncx(zf, resolve_href(opf_path, manifest[ncx_id]["href"]))
                findings.append({"severity": "info", "message": f"toc.ncx found with {len(toc_entries)} entries."})
            else:
                findings.append({"severity": "warning", "message": "No nav.xhtml or toc.ncx found; falling back to spine."})

            sections: list[dict[str, Any]] = []
            for index, item_id in enumerate(spine_ids, start=1):
                info = manifest.get(item_id)
                if not info or info["media_type"] != "application/xhtml+xml":
                    continue
                item_path = resolve_href(opf_path, info["href"])
                if item_path not in names:
                    findings.append({"severity": "warning", "message": f"Spine item missing: {item_path}"})
                    continue
                extracted = extract_chapter_text(zf, item_path)
                title = infer_section_title(extracted["headings"], info["href"])
                body = "\n\n".join(extracted["paragraphs"]).strip()
                section_id = f"sec-{index:03d}"
                section = {
                    "section_id": section_id,
                    "order": index,
                    "title": title,
                    "href": info["href"],
                    "text": body,
                    "char_count": len(body),
                    "paragraph_count": len(extracted["paragraphs"]),
                }
                sections.append(section)

            if not sections:
                findings.append({"severity": "error", "message": "No spine sections could be parsed."})

            toc_lookup: dict[str, str] = {entry["src"]: entry["title"] for entry in toc_entries}
            for section in sections:
                if section["href"] in toc_lookup and toc_lookup[section["href"]]:
                    section["title"] = toc_lookup[section["href"]]

            chunks: list[dict[str, Any]] = []
            for section in sections:
                paragraphs = re.split(r"\n\n+", section["text"]) if section["text"] else []
                paragraphs = [p.strip() for p in paragraphs if p.strip()]
                section_chunks = chunk_paragraphs(paragraphs, section["section_id"], section["title"])
                chunks.extend(section_chunks)
                section["chunk_count"] = len(section_chunks)
                if "chunk_count" not in section:
                    section["chunk_count"] = 0

            total_chars = sum(section["char_count"] for section in sections)

            book_md_path = private_dir / "book.md"
            with book_md_path.open("w", encoding="utf-8") as out:
                for section in sections:
                    out.write(f"<!-- section: {section['section_id']} -->\n")
                    out.write(f"# {section['title']}\n\n")
                    out.write(section["text"])
                    out.write("\n\n")
            findings.append({"severity": "info", "message": f"book.md written ({book_md_path.stat().st_size} bytes)."})

            sections_path = private_dir / "book_sections.jsonl"
            with sections_path.open("w", encoding="utf-8") as out:
                for section in sections:
                    out.write(json.dumps(section, ensure_ascii=False) + "\n")
            findings.append({"severity": "info", "message": f"book_sections.jsonl written ({len(sections)} sections)."})

            chunks_path = private_dir / "book_chunks.jsonl"
            with chunks_path.open("w", encoding="utf-8") as out:
                for chunk in chunks:
                    out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
            findings.append({"severity": "info", "message": f"book_chunks.jsonl written ({len(chunks)} chunks)."})

            source_summary = {
                "generated_at": _now_iso(),
                "epub_path": str(epub_path),
                "file_size_bytes": file_size,
                "mimetype": mimetype_content,
                "container_xml_present": container_xml,
                "opf_path": opf_path,
                "nav_xhtml_present": bool(nav_id),
                "toc_ncx_present": bool(ncx_id),
                "toc_entry_count": len(toc_entries),
                "image_count": image_count,
                "metadata": metadata,
                "chapter_titles": [
                    {"section_id": section["section_id"], "title": section["title"], "href": section["href"]}
                    for section in sections
                ],
                "section_count": len(sections),
                "chunk_count": len(chunks),
                "text_char_count": total_chars,
                "extraction_status": "ok" if sections else "failed",
                "identity_status": "identified" if metadata.get("title") and metadata.get("creator") else "partial",
                "findings": findings,
            }
            working_json = working_dir / "book_identity_source.json"
            working_json.write_text(json.dumps(source_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            return _write_reports(
                project_dir,
                working_dir,
                reports_dir,
                findings,
                file_size,
                len(sections),
                len(chunks),
                total_chars,
                image_count,
                toc_entries,
                source_summary=source_summary,
                mimetype=mimetype_content,
            )
    except zipfile.BadZipFile as exc:
        print(f"ERROR: not a valid zip/epub: {exc}", file=sys.stderr)
        return 1


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_reports(
    project_dir: Path,
    working_dir: Path,
    reports_dir: Path,
    findings: list[dict[str, str]],
    file_size: int,
    section_count: int,
    chunk_count: int,
    total_chars: int,
    image_count: int,
    toc_entries: list[dict[str, Any]],
    source_summary: dict[str, Any] | None = None,
    mimetype: str = "",
) -> int:
    errors = [f for f in findings if f.get("severity") == "error"]
    warnings = [f for f in findings if f.get("severity") == "warning"]
    infos = [f for f in findings if f.get("severity") == "info"]
    extraction_status = "ok" if not errors and section_count else "failed"
    suitable_for_reading_guide = extraction_status == "ok" and image_count < 50 and 5 <= section_count <= 60

    report_lines = [
        "# EPUB Extraction Report",
        "",
        f"Status: **{extraction_status}**",
        "",
        "## Source",
        "",
        f"- EPUB: `private/source/book.epub`",
        f"- File size: {file_size} bytes",
        f"- mimetype: `{mimetype}`",
        "",
        "## Structure",
        "",
        f"- container.xml present: {source_summary['container_xml_present'] if source_summary else False}",
        f"- OPF: `{source_summary['opf_path'] if source_summary else ''}`",
        f"- nav.xhtml present: {source_summary['nav_xhtml_present'] if source_summary else False}",
        f"- toc.ncx present: {source_summary['toc_ncx_present'] if source_summary else False}",
        f"- TOC entries: {len(toc_entries)}",
        f"- Image files: {image_count}",
        "",
        "## Content",
        "",
        f"- Section count: {section_count}",
        f"- Chunk count: {chunk_count}",
        f"- Total characters: {total_chars}",
        "",
        "## Identified Metadata",
        "",
    ]
    if source_summary:
        for key, value in source_summary.get("metadata", {}).items():
            report_lines.append(f"- {key}: `{value or 'unknown'}`")
    report_lines += [
        "",
        "## Findings",
        "",
    ]
    for finding in findings:
        report_lines.append(f"- [{finding.get('severity', 'info')}] {finding.get('message', '')}")
    report_lines += [
        "",
        "## Suitability",
        "",
        f"- Suitable for reading-guide: **{suitable_for_reading_guide}**",
        f"- Image count threshold: <50 (got {image_count})",
        f"- Section count threshold: 5-60 (got {section_count})",
        "",
        "## Private Outputs",
        "",
        "- `private/book.md` (full extracted text, NOT for public release)",
        "- `private/book_sections.jsonl` (per-section structured data, NOT for public release)",
        "- `private/book_chunks.jsonl` (chunked text, NOT for public release)",
        "",
        "## Public Boundary",
        "",
        "- This script writes only to `private/`, `working/`, and `reports/`.",
        "- It does NOT write to `public/`, `web/public/`, or `web/dist/`.",
        "- It does NOT perform OCR.",
        "- It does NOT translate, summarize, or paraphrase the source text.",
        "",
    ]
    (reports_dir / "epub_extraction_report.md").write_text("\n".join(report_lines), encoding="utf-8")

    print(f"EPUB extraction: {extraction_status}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Info: {len(infos)}")
    print(f"Sections: {section_count}")
    print(f"Chunks: {chunk_count}")
    print(f"Total chars: {total_chars}")
    print(f"Images: {image_count}")
    print(f"Suitable for reading-guide: {suitable_for_reading_guide}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
