from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.lib.project_paths import ProjectPaths
except ModuleNotFoundError:  # Direct execution: python scripts/inspect_*.py
    from lib.project_paths import ProjectPaths


PUBLIC_FILES = [
    "book_overview.json",
    "chapter_reading_cards.json",
    "key_concepts.json",
    "quote_index.json",
    "reading_questions.json",
]

NEXT_SCRIPTS = [
    "build_letters_brief.py",
    "build_reading_guide_public.py",
    "build_manual_review_tasks.py",
    "check_manual_review_tasks.py",
    "promote_status.py",
]

PRIVATE_PUBLIC_PATTERNS = [
    "private/",
    "private\\",
    "private/source",
    "book.epub",
    "book.md",
    "book_sections.jsonl",
    "book_chunks.jsonl",
    "full_text",
    "raw_text",
    "chapter_text",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def exists_map(paths: dict[str, Path]) -> dict[str, bool]:
    return {key: path.exists() for key, path in paths.items()}


def count_files(path: Path) -> int:
    if not path.exists() or not path.is_dir():
        return 0
    return sum(1 for item in path.iterdir() if item.is_file())


def scan_public_boundary(paths: list[Path]) -> tuple[bool, list[str]]:
    findings: list[str] = []
    for base in paths:
        if not base.exists() or not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".json", ".md", ".txt"}:
                continue
            if path.name == "project.json":
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            lowered = text.lower()
            for pattern in PRIVATE_PUBLIC_PATTERNS:
                if pattern.lower() in lowered:
                    findings.append(f"{path.as_posix()}: contains `{pattern}`")
    return not findings, findings


def source_type(project_data: dict[str, Any]) -> str:
    book = project_data.get("book")
    if isinstance(book, dict) and book.get("source_type"):
        return str(book["source_type"])
    if project_data.get("source_type"):
        return str(project_data["source_type"])
    return "unknown"


def inspect_project(project_path: str | Path) -> dict[str, Any]:
    paths = ProjectPaths.from_project(project_path)

    project_data = read_json(paths.project_json) if paths.project_json.exists() else {}

    scripts = {
        "extract_epub": paths.repo_root / "scripts" / "extract_epub.py",
        "identify_book": paths.repo_root / "scripts" / "identify_book.py",
        "check_reading_guide_project": paths.repo_root / "scripts" / "check_reading_guide_project.py",
        "check_public_release": paths.repo_root / "scripts" / "check_public_release.py",
    }
    next_scripts = {name: paths.repo_root / "scripts" / name for name in NEXT_SCRIPTS}

    identity_files = {
        "book_identity": paths.book_identity_json,
        "book_identity_source": paths.book_identity_source_json,
    }
    intake_reports = {
        "book_identity_report": paths.book_identity_report,
        "epub_extraction_report": paths.epub_extraction_report,
    }

    public_files_present = [name for name in PUBLIC_FILES if paths.public_path(name).exists()]
    web_public_files_present = [name for name in PUBLIC_FILES if paths.web_project_path(name).exists()]
    privacy_ok, privacy_findings = scan_public_boundary([paths.public_dir, paths.web_project_dir])

    script_presence = exists_map(scripts)
    identity_presence = exists_map(identity_files)
    report_presence = exists_map(intake_reports)
    missing_next_scripts = [name for name, path in next_scripts.items() if not path.exists()]

    identity_artifacts_present = all(identity_presence.values()) and all(report_presence.values())
    public_layer_present = paths.public_dir.exists()
    web_mirror_present = paths.web_project_dir.exists()
    intake_ready = (
        paths.project_json.exists()
        and script_presence["extract_epub"]
        and script_presence["identify_book"]
        and paths.epub_path.exists()
        and identity_artifacts_present
        and privacy_ok
    )

    recommended_next_actions = []
    if missing_next_scripts:
        recommended_next_actions.append("Implement the missing next-stage scripts listed in missing_next_artifacts.")
    if not intake_ready:
        recommended_next_actions.append("Complete EPUB intake artifacts before building public reading-guide data.")
    else:
        recommended_next_actions.append("Proceed to v0.7-A2 letters brief builder.")

    return {
        "project": {
            "slug": paths.slug,
            "path": paths.project_dir.relative_to(paths.repo_root).as_posix(),
            "project_type": project_data.get("project_type"),
            "title": project_data.get("title"),
        },
        "status": project_data.get("status", "unknown"),
        "source_type": source_type(project_data),
        "intake_ready": intake_ready,
        "epub_source_present": paths.epub_path.exists(),
        "identity_artifacts_present": identity_artifacts_present,
        "public_layer_present": public_layer_present,
        "web_mirror_present": web_mirror_present,
        "counts": {
            "public_files_present": len(public_files_present),
            "web_public_files_present": len(web_public_files_present),
            "public_dir_file_count": count_files(paths.public_dir),
            "web_project_file_count": count_files(paths.web_project_dir),
            "identity_working_files_present": sum(1 for present in identity_presence.values() if present),
            "intake_reports_present": sum(1 for present in report_presence.values() if present),
            "missing_next_scripts": len(missing_next_scripts),
        },
        "privacy_boundary_ok": privacy_ok,
        "privacy_boundary_findings": privacy_findings,
        "script_presence": script_presence,
        "identity_file_presence": identity_presence,
        "intake_report_presence": report_presence,
        "public_files_present": public_files_present,
        "web_public_files_present": web_public_files_present,
        "missing_next_artifacts": missing_next_scripts,
        "recommended_next_actions": recommended_next_actions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect reading-guide pipeline readiness without reading EPUB body text.")
    parser.add_argument("--project", required=True, help="Path to projects/<slug>.")
    args = parser.parse_args()
    print(json.dumps(inspect_project(args.project), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
