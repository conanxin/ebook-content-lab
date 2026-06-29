# Open Source Release Report

Generated at: 2026-06-29 11:17 Asia/Shanghai

Status: **v0.5-open-source-ready**

## Overall Result

- Can publish as open source: **yes**
- Can publish to GitHub Pages: **yes**
- Blocking issues found: **none**

## Repository Structure

Required top-level structure is present:

- `docs/`
- `schemas/`
- `scripts/`
- `templates/`
- `projects/dadou-shangdu/`
- `web/`
- `.github/workflows/pages.yml`
- `README.md`
- `LICENSE`
- `LICENSE-CONTENT.md`
- `CONTRIBUTING.md`
- `.gitignore`

## dadou-shangdu Project Files

Required project files are present:

- `projects/dadou-shangdu/project.json`
- `projects/dadou-shangdu/public/route_segments.json`
- `projects/dadou-shangdu/public/route.geojson`
- `projects/dadou-shangdu/public/route_places.geojson`
- `projects/dadou-shangdu/public/route.gpx`
- `projects/dadou-shangdu/public/route_walkable_blocks.json`
- `projects/dadou-shangdu/public/field_guide.md`
- `projects/dadou-shangdu/reports/final_acceptance_report.md`

## Web Public Data

Required web public files are present:

- `web/public/projects/index.json`
- `web/public/projects/dadou-shangdu/project.json`
- `web/public/projects/dadou-shangdu/route_segments.json`
- `web/public/projects/dadou-shangdu/route.geojson`
- `web/public/projects/dadou-shangdu/route_places.geojson`
- `web/public/projects/dadou-shangdu/route.gpx`
- `web/public/projects/dadou-shangdu/route_walkable_blocks.json`
- `web/public/projects/dadou-shangdu/field_guide.md`

The public project index currently lists:

- `dadou-shangdu`: 《从大都到上都》徒步路线图解, `route-map`, status `v0.4-local-accepted-needs-manual-review`

## Command Results

### Public Release Check

Command:

```powershell
python scripts\check_public_release.py
```

Result: **pass**

- Errors: 0
- Warnings: 0
- Report: `data/public_release_report.md`

### Route Validation

Command:

```powershell
python scripts\validate_route.py data\route_segments.json
```

Result: **pass**

- Segments: 15
- Errors: 0
- Warnings: 0
- Info: 15

### GPX Export

Command:

```powershell
python scripts\export_gpx.py data\route_segments.json --output data\route.gpx
```

Result: **pass**

- Waypoints exported: 99
- Track segments exported: 8
- Skipped / do-not-connect segments: 7
- `do_not_connect_in_gpx=true`: `seg-003`, `seg-008`, `seg-010`, `seg-011`, `seg-013`, `seg-014`, `seg-015`

Note: the regenerated compatibility file `data/route.gpx` differs from `projects/dadou-shangdu/public/route.gpx` only in the GPX `<time>` metadata. Waypoint and track counts match.

### Web Build

Command:

```powershell
cd web
npm run build
```

Result: **pass**

- TypeScript build passed.
- Vite production build passed.
- Output directory: `web/dist/`

## Public Path and Routing Checks

- `web/src` does not depend on legacy `/data/` paths.
- The multi-project portal reads `/projects/index.json`.
- The `dadou-shangdu` project page reads `/projects/dadou-shangdu/`.
- Hash routes are used:
  - `#/`
  - `#/projects/dadou-shangdu`

## Private Data Boundary Checks

No forbidden private source/OCR files were found in `web/public/` or `projects/*/public/`.

Checked forbidden examples:

- `book.pdf`
- `book_ocr.pdf`
- `book_pages.jsonl`
- `book_pages.cleaned.jsonl`
- `book_chunks.jsonl`
- `review_pack/pages/*.png`

These files may exist locally under `projects/*/private/` or legacy `data/` compatibility paths, but they are not present in public release directories.

## Internal Marker Checks

Targeted release-candidate scan found none of the three requested internal marker patterns.

The targeted scan covered release-relevant paths such as root docs, `docs/`, `scripts/`, `templates/`, `projects/dadou-shangdu/public/`, `web/src/`, and `web/public/projects/`.

## Page Copy Checks

No high-risk page copy was found in `web/src` or `web/public/projects`:

- `完整可导航路线`
- `精确轨迹`
- `无需复核`
- `官方路线`

The page continues to state that the route map is based on book descriptions, coordinates are modern auxiliary positioning, and the page is not an unverified outdoor navigation route.

## Online Page Entrypoints

After GitHub Pages deployment, expected URLs are:

```text
https://<username>.github.io/<repo-name>/#/
https://<username>.github.io/<repo-name>/#/projects/dadou-shangdu
```

For a root user site such as `<username>.github.io`, set `VITE_BASE=/` in the workflow and use:

```text
https://<username>.github.io/#/
https://<username>.github.io/#/projects/dadou-shangdu
```

## Local Run Commands

Install and run locally:

```powershell
cd web
npm install
npm run dev -- --host 127.0.0.1
```

Build locally:

```powershell
cd web
npm run build
```

Release checks:

```powershell
python scripts\check_public_release.py
python scripts\validate_route.py data\route_segments.json
python scripts\export_gpx.py data\route_segments.json --output data\route.gpx
```

## GitHub Publishing Steps

1. Create a GitHub repository.
2. Add the remote and push `main`.
3. In GitHub Settings -> Pages, choose GitHub Actions as the source.
4. Confirm `.github/workflows/pages.yml` runs successfully.
5. Confirm `VITE_BASE` matches the deployment path:
   - normal project site: `/<repo-name>/`
   - root user site or custom domain root: `/`

## Remaining Manual Items Before Actual Publication

No blocking technical issue was found.

Manual operator steps still required:

- Create or choose the GitHub repository.
- Push the repository to `main`.
- Enable GitHub Pages with GitHub Actions.
- Confirm the intended public license posture is acceptable: code under MIT, curated documentation/structured data under CC BY 4.0, private source/OCR materials excluded.
- Optionally review `dadou-shangdu` content caveats before public announcement: the route page deliberately marks historical place uncertainty, OCR review needs, route gaps, mixed walking/vehicle segments, and modern road-condition review needs.
