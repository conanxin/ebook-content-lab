# Reading Guide Pipeline

This document defines the current `reading-guide` pipeline baseline for `ebook-content-lab`.

## Current Real Baseline

- Current HEAD: `74478b1 Add EPUB intake workflow for second reading guide`.
- `projects/second-reading-guide` has an EPUB intake workflow.
- The project is **EPUB intake ready**.
- The project has **not** entered `reviewed-draft`.
- Do not assume the previous `6486c19`, `1b3c8d8`, or `v0.6.1-reading-guide-reviewed-draft` refs exist in this repository.

## Input Layer

Private source and extracted full text stay local:

- `projects/second-reading-guide/private/source/book.epub`
- `projects/second-reading-guide/private/book.md`
- `projects/second-reading-guide/private/book_sections.jsonl`
- `projects/second-reading-guide/private/book_chunks.jsonl`

The current committed intake metadata and reports are:

- `projects/second-reading-guide/working/book_identity.json`
- `projects/second-reading-guide/working/book_identity_source.json`
- `projects/second-reading-guide/reports/epub_extraction_report.md`
- `projects/second-reading-guide/reports/book_identity_report.md`

The working JSON and reports are metadata / inventory artifacts. They are not public reading-guide content.

## Existing Scripts

- `scripts/extract_epub.py`
  - Reads the private EPUB.
  - Writes extracted text only to `private/`.
  - Writes metadata summaries to `working/` and `reports/`.
  - Does not write public data.

- `scripts/identify_book.py`
  - Reads local project artifacts.
  - Supports EPUB metadata and legacy PDF/OCR projects.
  - Updates identity metadata and reports.

- `scripts/check_reading_guide_project.py`
  - Validates the reading-guide public data skeleton.
  - Allows draft projects to keep content arrays empty.

- `scripts/check_public_release.py`
  - Checks that public release files do not include private source files or high-risk public content.

## Scripts To Build Next

- `scripts/build_letters_brief.py`
- `scripts/build_reading_guide_public.py`
- `scripts/build_manual_review_tasks.py`
- `scripts/check_manual_review_tasks.py`
- `scripts/promote_status.py`

These scripts do not exist in the current R2 baseline.

## Safety Boundary

- `private/` is not public.
- EPUB files are not committed as public release material.
- `book.md`, `book_sections.jsonl`, and `book_chunks.jsonl` are not committed as public release material.
- The public layer may contain metadata, structured summaries, review prompts, and short evidence quotes only.
- Do not publish EPUB body text, complete chapter text, raw extracted text, or long copyrighted excerpts.
- `web/public/projects/<slug>/` should mirror only approved public artifacts.

## v0.7 Route

- **R2**: Rebuild the pipeline baseline around the real current state: EPUB intake ready.
- **A1**: Add `ProjectPaths` path resolver.
- **A2**: Build `letters_brief` from private EPUB extraction artifacts.
- **A3**: Build public reading-guide JSON from reviewed intermediate data.
- **B**: Add manual review workflow.
- **C**: Add status promotion.
- **D**: Tag and release after public data and review gates pass.

## Why R2 Replaces The Old Assumption

The current repository has `HEAD = origin/main = 74478b1`. The earlier expected refs `6486c19`, `1b3c8d8`, and `v0.6.1-reading-guide-reviewed-draft` are not available in this clone or in the configured origin. R2 therefore treats the committed EPUB intake workflow as the source of truth.
