# Architecture

`ebook-content-lab` is organized as a reusable platform plus independent ebook subprojects.

## Top-Level Areas

```text
docs/                         platform documentation
schemas/                      data schemas and project metadata schemas
scripts/                      OCR, extraction, audit, validation, publishing checks
templates/                    reusable project scaffold
projects/                     ebook subprojects
web/                          Vite + React frontend
web/public/projects/          frontend-readable public project data
```

## Project Index

The web portal starts from:

```text
web/public/projects/index.json
```

Each entry points to:

```text
web/public/projects/<slug>/project.json
```

The React app uses hash routes:

```text
#/
#/projects/<slug>
```

`ProjectPage` reads project metadata and dispatches to a project-type-specific page. Currently `route-map` is implemented.

## Subproject Layout

Each ebook project lives under:

```text
projects/<slug>/
```

Standard directories:

- `private/`
- `working/`
- `public/`
- `reports/`
- `review_pack/`

## private/

Local-only material:

- Source ebook files.
- OCR PDFs.
- OCR full text.
- OCR page JSONL and chunks.
- Other source-derived bulk material.

This directory is ignored by git and should not be copied to `web/public/`.

## working/

Intermediate work products:

- Draft structured data.
- Extraction candidates.
- Evidence-audited drafts.
- Unsupported claim lists.
- Citation mismatch lists.

Files here may be useful for review, but they are not automatically safe for public release.

## public/

Curated public artifacts:

- Structured JSON.
- GeoJSON.
- GPX.
- Public guides.
- Project metadata.

These files can be mirrored to:

```text
web/public/projects/<slug>/
```

## reports/

Project reports:

- OCR reports.
- Evidence audit reports.
- Validation reports.
- Continuity or consistency reports.
- Final acceptance reports.

Reports may still contain sensitive or long source-derived content, so review before publishing.

## review_pack/

Manual review support:

- HTML review entrypoint.
- Checklist CSV.
- Review index.
- Local scan page images when needed.

Scan page images stay local and are not published.

## scripts/

Scripts provide repeatable processing:

- `create_project.py`: create subproject scaffolds.
- `identify_book.py`: identify local book metadata and content type.
- `ocr_pdf.py`: OCR scanned PDF inputs.
- `clean_ocr_text.py` and `chunk_book.py`: prepare OCR text.
- `audit_route_evidence.py` and `resolve_evidence_warnings.py`: route evidence audit workflow.
- `validate_route.py`, `build_geojson.py`, `export_gpx.py`: route-map output checks and exports.
- `check_public_release.py`: open-source release boundary check.

## schemas/

Schemas document expected data shapes. They are intended for validation and future tooling as more project types are added.
