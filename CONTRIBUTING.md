# Contributing

Thanks for helping improve `ebook-content-lab`. This project values evidence, uncertainty labels, and clear public/private data boundaries.

## Add a Subproject

Create a project scaffold:

```powershell
python scripts\create_project.py --slug <slug> --title "<项目标题>" --book-title "<书名>" --project-type <type>
```

Then follow:

- `docs/add-new-book-project.md`
- `docs/project-lifecycle.md`
- `docs/data-policy.md`

Do not commit source PDFs, OCR PDFs, OCR full text, scan images, or private review materials.

## Submit an Issue

Issues are welcome for:

- OCR mistakes.
- Wrong or ambiguous metadata.
- Evidence mismatches.
- Route, place, or timeline correction suggestions.
- Web UI bugs.
- Documentation improvements.

Please include:

- Project slug, such as `dadou-shangdu`.
- Affected file or page.
- Evidence or reproduction steps.
- Whether the issue is a confirmed correction or a review question.

## Submit Route Data Corrections

For route-map projects, route data changes must preserve evidence boundaries.

When proposing a correction:

- Identify the segment id, such as `seg-009`.
- State the field to change.
- Provide page number and short quote when the correction is based on the book.
- Mark uncertainty instead of filling gaps with assumptions.
- Do not use modern maps to change the book-derived route order.
- Do not remove `book_refs` or `chapter_refs`; update them only when evidence requires it.

Run route validation when relevant:

```powershell
python scripts\validate_route.py data\route_segments.json
```

For project-scoped public data, also ensure the matching `projects/<slug>/public/` and `web/public/projects/<slug>/` files stay synchronized.

## Fill Manual Review Results

Manual review checklists live in project review packs, for example:

```text
projects/dadou-shangdu/review_pack/manual_review_checklist.csv
```

Fill the `manual_result` and `notes` columns with concise results. If a review changes structured data, update the relevant data file and report.

Do not publish scan page images from review packs.

## Validation

Common checks:

```powershell
python scripts\validate_route.py data\route_segments.json
python scripts\export_gpx.py data\route_segments.json --output data\route.gpx
python scripts\check_public_release.py
cd web
npm run build
```

For non-route-map projects, use the closest available project-specific validator and always run the public release check before publishing.

## Public Release Check

Run:

```powershell
python scripts\check_public_release.py
```

The report is written to:

```text
data/public_release_report.md
```

Fix all errors before publishing. Warnings should be reviewed and either fixed or intentionally documented.
