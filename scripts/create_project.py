from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_TYPES = (
    "route-map",
    "timeline",
    "character-map",
    "place-index",
    "reading-guide",
    "quote-atlas",
    "knowledge-map",
    "field-guide",
)

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def validate_slug(slug: str) -> None:
    if not SLUG_RE.fullmatch(slug):
        raise ValueError(
            "Invalid slug. Use lowercase letters, numbers, and single hyphens only "
            "(for example: another-book)."
        )


def render_project_json(slug: str, title: str, book_title: str, project_type: str) -> dict[str, Any]:
    return {
        "slug": slug,
        "title": title,
        "book_title": book_title,
        "source_type": "scanned_pdf",
        "project_type": project_type,
        "status": "draft",
        "visibility": {
            "private_source_kept_in": f"projects/{slug}/private/",
            "public_artifacts_kept_in": f"projects/{slug}/public/",
            "web_public_path": f"/projects/{slug}/",
        },
        "public_files": [],
        "quality_summary": {
            "ocr": "unknown",
            "content_extraction": "unknown",
            "evidence_audit": "unknown",
            "validation": "unknown",
            "manual_review_required": True,
        },
        "route_stats": {},
        "review_status": {
            "status": "not_started",
            "notes": "新项目草稿，尚未完成 OCR、抽取、审计和人工复核。",
        },
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


def render_readme(slug: str, title: str, book_title: str, project_type: str) -> str:
    return f"""# {title}

Book: `{book_title}`

Project type: `{project_type}`

Status: `draft`

This project was created from `templates/project-template/`.

## Directories

- `private/source/`: source ebook files, such as `book.pdf`. Do not publish this directory.
- `private/ocr/`: OCR PDF and OCR engine intermediates. Do not publish this directory.
- `working/`: draft extraction, audit intermediates, and temporary structured data.
- `public/`: public artifacts that can be copied to `web/public/projects/{slug}/`.
- `reports/`: OCR, audit, validation, review, and acceptance reports.
- `review_pack/`: local manual review entrypoints and checklists.

## Next Steps

1. Put the source ebook at `projects/{slug}/private/source/book.pdf`.
2. Run OCR and text extraction.
3. Clean and chunk the OCR text.
4. Extract structured content for `{project_type}`.
5. Audit every claim against book evidence.
6. Generate public artifacts under `projects/{slug}/public/`.
7. Sync safe public files to `web/public/projects/{slug}/`.
8. Keep source PDFs, OCR PDFs, scan images, and private review material out of `web/public`.
"""


def update_project_index(root: Path, slug: str, title: str, book_title: str, project_type: str) -> None:
    index_path = root / "web" / "public" / "projects" / "index.json"
    index = load_json(index_path, {"repository": "ebook-content-lab", "projects": []})
    projects = index.setdefault("projects", [])
    if any(project.get("slug") == slug for project in projects):
        raise ValueError(f"Project already exists in {index_path}: {slug}")

    projects.append(
        {
            "slug": slug,
            "title": title,
            "book_title": book_title,
            "project_type": project_type,
            "status": "draft",
            "public_path": f"/projects/{slug}/",
            "project_json": f"/projects/{slug}/project.json",
        }
    )
    projects.sort(key=lambda item: item.get("slug", ""))
    write_json(index_path, index)


def create_project(args: argparse.Namespace) -> Path:
    validate_slug(args.slug)

    root = repo_root()
    template_dir = root / "templates" / "project-template"
    project_dir = root / "projects" / args.slug
    web_project_dir = root / "web" / "public" / "projects" / args.slug

    if not template_dir.exists():
        raise FileNotFoundError(f"Missing template directory: {template_dir}")
    if project_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing project: {project_dir}")
    if web_project_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing web project directory: {web_project_dir}")

    shutil.copytree(template_dir, project_dir)

    project_json = render_project_json(
        slug=args.slug,
        title=args.title,
        book_title=args.book_title,
        project_type=args.project_type,
    )
    write_json(project_dir / "project.json", project_json)
    (project_dir / "README.md").write_text(
        render_readme(args.slug, args.title, args.book_title, args.project_type),
        encoding="utf-8",
    )

    web_project_dir.mkdir(parents=True, exist_ok=False)
    write_json(web_project_dir / "project.json", project_json)
    update_project_index(root, args.slug, args.title, args.book_title, args.project_type)

    return project_dir


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a standard ebook-content-lab subproject.",
    )
    parser.add_argument("--slug", required=True, help="Project slug, such as another-book.")
    parser.add_argument("--title", required=True, help="Project display title.")
    parser.add_argument("--book-title", required=True, help="Original book title.")
    parser.add_argument(
        "--project-type",
        required=True,
        choices=PROJECT_TYPES,
        help="Content project type.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        project_dir = create_project(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Created project: {project_dir}")
    print(f"Updated project index: {repo_root() / 'web' / 'public' / 'projects' / 'index.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
