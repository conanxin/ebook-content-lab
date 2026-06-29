# EPUB Extraction Report

Status: **ok**

## Source

- EPUB: `private/source/book.epub`
- File size: 343251 bytes
- mimetype: `application/epub+zip`

## Structure

- container.xml present: True
- OPF: `content.opf`
- nav.xhtml present: False
- toc.ncx present: True
- TOC entries: 29
- Image files: 2

## Content

- Section count: 31
- Chunk count: 97
- Total characters: 93937

## Identified Metadata

- title: `旅行人信札`
- creator: `陈嘉映`
- language: `zh`
- publisher: `上海文艺出版社`
- date: `2021-12-31T16:00:00+00:00`
- identifier: `d3671844-e97c-499e-855a-8753809f0381`
- description: `unknown`
- rights: `Copyrights as per source stories`

## Findings

- [info] toc.ncx found with 29 entries.
- [info] book.md written (274708 bytes).
- [info] book_sections.jsonl written (31 sections).
- [info] book_chunks.jsonl written (97 chunks).

## Suitability

- Suitable for reading-guide: **True**
- Image count threshold: <50 (got 2)
- Section count threshold: 5-60 (got 31)

## Private Outputs

- `private/book.md` (full extracted text, NOT for public release)
- `private/book_sections.jsonl` (per-section structured data, NOT for public release)
- `private/book_chunks.jsonl` (chunked text, NOT for public release)

## Public Boundary

- This script writes only to `private/`, `working/`, and `reports/`.
- It does NOT write to `public/`, `web/public/`, or `web/dist/`.
- It does NOT perform OCR.
- It does NOT translate, summarize, or paraphrase the source text.
