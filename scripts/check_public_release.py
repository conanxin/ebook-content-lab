from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


FORBIDDEN_PUBLIC_FILENAMES = {
    "book.pdf",
    "book_ocr.pdf",
    "book.md",
    "book_pages.jsonl",
    "book_pages.cleaned.jsonl",
    "book_chunks.jsonl",
}

ALLOWED_WEB_PROJECT_FILES = {
    "project.json",
    "route_segments.json",
    "route.geojson",
    "route_places.geojson",
    "route.gpx",
    "route_walkable_blocks.json",
    "field_guide.md",
    "review_index.md",
    "book_overview.json",
    "segment_reading_cards.json",
    "place_index.json",
    "book_themes.json",
    "chapter_reading_cards.json",
    "key_concepts.json",
    "quote_index.json",
    "reading_questions.json",
}

HIGH_RISK_COPY = [
    "完整可导航路线",
    "确定可走",
    "精确轨迹",
    "无需复核",
    "官方路线",
]

INTERNAL_MARKERS = [
    "OAI-MEM-CITATION",
    "MEMORY.md",
    "rollout_ids",
]

TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".jsonl",
    ".geojson",
    ".gpx",
    ".tsx",
    ".ts",
    ".js",
    ".jsx",
    ".html",
    ".css",
    ".yml",
    ".yaml",
}

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}
LARGE_SCAN_IMAGE_BYTES = 500_000
QUOTE_LIMIT = 120


@dataclass
class Finding:
    severity: str
    path: str
    message: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def add(finding_list: list[Finding], severity: str, path: Path | str, message: str, root: Path) -> None:
    path_text = rel(path, root) if isinstance(path, Path) else path
    finding_list.append(Finding(severity=severity, path=path_text, message=message))


def iter_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if not path.exists():
            continue
        if path.is_file():
            files.append(path)
        else:
            files.extend(item for item in path.rglob("*") if item.is_file())
    return files


def check_gitignore(root: Path, findings: list[Finding]) -> None:
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        add(findings, "error", gitignore, "Missing .gitignore.", root)
        return

    lines = {
        line.strip().replace("\\", "/")
        for line in gitignore.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    required = {
        "projects/*/private/",
        "projects/*/review_pack/pages/",
        "source/",
        "data/ocr/",
        "data/book.md",
        "data/book_pages.jsonl",
        "data/book_pages.cleaned.jsonl",
        "data/book_chunks.jsonl",
        "data/review_pack/pages/",
        "web/dist/",
        "web/node_modules/",
        "__pycache__/",
        "*.pyc",
        ".venv/",
        "node_modules/",
        ".DS_Store",
        "Thumbs.db",
        ".vscode/",
    }
    missing = sorted(required - lines)
    for pattern in missing:
        add(findings, "error", gitignore, f"Missing required ignore pattern: {pattern}", root)

    for private_dir in (root / "projects").glob("*/private"):
        if private_dir.is_dir() and "projects/*/private/" not in lines:
            add(findings, "error", private_dir, "Private project directory exists but is not ignored.", root)


def is_review_pack_page(path: Path) -> bool:
    normalized = path.as_posix().lower()
    return "/review_pack/pages/" in normalized and path.suffix.lower() == ".png"


def check_forbidden_public_files(root: Path, findings: list[Finding]) -> None:
    public_roots = [root / "web" / "public"]
    public_roots.extend((root / "projects").glob("*/public"))

    for path in iter_files(public_roots):
        name = path.name.lower()
        suffix = path.suffix.lower()
        size = path.stat().st_size
        if name in FORBIDDEN_PUBLIC_FILENAMES:
            add(findings, "error", path, "Private source/OCR file appears in a public directory.", root)
        if is_review_pack_page(path):
            add(findings, "error", path, "Rendered review pack scan page appears in a public directory.", root)
        if suffix in IMAGE_SUFFIXES and (size >= LARGE_SCAN_IMAGE_BYTES or re.match(r"page_\d+\.(png|jpg|jpeg|webp)$", name)):
            add(findings, "error", path, "Large or page-numbered scan image appears in a public directory.", root)


def check_web_public_projects(root: Path, findings: list[Finding]) -> list[dict[str, Any]]:
    index_path = root / "web" / "public" / "projects" / "index.json"
    projects: list[dict[str, Any]] = []
    if not index_path.exists():
        add(findings, "error", index_path, "Missing web public project index.", root)
        return projects

    try:
        index = read_json(index_path)
    except Exception as exc:
        add(findings, "error", index_path, f"Cannot read project index: {exc}", root)
        return projects

    if not isinstance(index.get("projects"), list):
        add(findings, "error", index_path, "Project index does not contain a projects list.", root)
        return projects

    for item in index["projects"]:
        if not isinstance(item, dict) or not item.get("slug"):
            add(findings, "error", index_path, "Project index contains an invalid project entry.", root)
            continue
        slug = str(item["slug"])
        project_dir = root / "web" / "public" / "projects" / slug
        project_json = project_dir / "project.json"
        if not project_json.exists():
            add(findings, "error", project_json, "Missing public project.json.", root)
            continue
        try:
            project_data = read_json(project_json)
        except Exception as exc:
            add(findings, "error", project_json, f"Cannot read public project.json: {exc}", root)
            continue
        projects.append(project_data)

        for file_path in project_dir.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.name not in ALLOWED_WEB_PROJECT_FILES:
                add(findings, "error", file_path, "Unexpected file in web/public/projects/<slug>/.", root)
            if file_path.name == "review_index.md":
                text = file_path.read_text(encoding="utf-8", errors="replace")
                if has_long_text_excerpt(text):
                    add(findings, "warning", file_path, "review_index.md may contain long source excerpts; review before publishing.", root)

        public_files = project_data.get("public_files") or []
        if not isinstance(public_files, list):
            add(findings, "error", project_json, "public_files must be a list.", root)
        else:
            for public_file in public_files:
                if not isinstance(public_file, str):
                    add(findings, "error", project_json, "public_files contains a non-string entry.", root)
                    continue
                target = project_dir / public_file
                if not target.exists():
                    add(findings, "error", target, "public_files entry is missing from web public project directory.", root)

    return projects


def has_long_text_excerpt(text: str) -> bool:
    quote_like_lines = [
        line.strip()
        for line in text.splitlines()
        if any(marker in line for marker in ["摘", "quote", "引文", "原文"])
    ]
    return any(len(line) > 180 for line in quote_like_lines)


def walk_refs(value: Any) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if {"page", "quote"}.issubset(value.keys()):
            refs.append(value)
        for child in value.values():
            refs.extend(walk_refs(child))
    elif isinstance(value, list):
        for item in value:
            refs.extend(walk_refs(item))
    return refs


def check_quotes(root: Path, findings: list[Finding]) -> None:
    route_files = list((root / "web" / "public" / "projects").glob("*/route_segments.json"))
    route_files.extend((root / "projects").glob("*/public/route_segments.json"))
    seen: set[Path] = set()
    for route_file in route_files:
        route_file = route_file.resolve()
        if route_file in seen:
            continue
        seen.add(route_file)
        try:
            data = read_json(route_file)
        except Exception as exc:
            add(findings, "error", route_file, f"Cannot read route segments JSON: {exc}", root)
            continue
        for segment in data if isinstance(data, list) else []:
            segment_id = segment.get("id", "unknown") if isinstance(segment, dict) else "unknown"
            for ref in walk_refs(segment):
                quote = str(ref.get("quote") or "")
                if len(quote) > QUOTE_LIMIT:
                    add(
                        findings,
                        "warning",
                        route_file,
                        f"{segment_id} quote is {len(quote)} chars, over {QUOTE_LIMIT}.",
                        root,
                    )


def should_scan_text_file(path: Path, root: Path) -> bool:
    rel_path = rel(path, root)
    skip_parts = [
        ".git/",
        "web/node_modules/",
        "node_modules/",
        "web/dist/",
        "projects/dadou-shangdu/private/",
        "source/",
        "data/ocr/",
        "data/review_pack/pages/",
    ]
    if any(rel_path.startswith(part) for part in skip_parts):
        return False
    if rel_path == "scripts/check_public_release.py":
        return False
    # Skip files that are (a) not tracked by git AND (b) ignored by .gitignore.
    # This lets local-only audit / review notes live in the working tree
    # without being scanned as release candidates. Tracked files are always
    # scanned, even if they happen to match a .gitignore pattern.
    if not _is_tracked_by_git(root, rel_path) and _is_ignored_by_git(root, rel_path):
        return False
    return path.suffix.lower() in TEXT_SUFFIXES


def _is_tracked_by_git(root: Path, rel_path: str) -> bool:
    """Return True if `rel_path` is tracked by git in this repository."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", rel_path],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        # git not on PATH — fall back to scanning the file (safe default).
        return True
    return result.returncode == 0


def _is_ignored_by_git(root: Path, rel_path: str) -> bool:
    """Return True if `rel_path` is ignored by .gitignore in this repository."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "-q", "--", rel_path],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return False
    return result.returncode == 0


def check_text_markers(root: Path, findings: list[Finding]) -> None:
    scan_roots = [
        root / "README.md",
        root / "docs",
        root / "scripts",
        root / "web" / "src",
        root / "web" / "public",
        root / "projects",
        root / "data",
        root / ".github",
    ]
    for path in iter_files(scan_roots):
        if not should_scan_text_file(path, root):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in INTERNAL_MARKERS:
            if marker in text:
                add(findings, "error", path, "Internal marker found in release candidate file.", root)
        if rel(path, root).startswith("web/src/"):
            for phrase in HIGH_RISK_COPY:
                if phrase in text:
                    add(findings, "error", path, f"High-risk page copy found: {phrase}", root)


def render_report(findings: list[Finding], project_count: int) -> str:
    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    status = "pass" if not errors else "fail"

    lines = [
        "# Public Release Report",
        "",
        f"Status: **{status}**",
        "",
        "## Summary",
        "",
        f"- Projects in web/public/projects/index.json: {project_count}",
        f"- Errors: {len(errors)}",
        f"- Warnings: {len(warnings)}",
        "",
    ]

    if errors:
        lines.extend(["## Errors", ""])
        for finding in errors:
            lines.append(f"- `{finding.path}`: {finding.message}")
        lines.append("")
    else:
        lines.extend(["## Errors", "", "- None", ""])

    if warnings:
        lines.extend(["## Warnings", ""])
        for finding in warnings:
            lines.append(f"- `{finding.path}`: {finding.message}")
        lines.append("")
    else:
        lines.extend(["## Warnings", "", "- None", ""])

    lines.extend(
        [
            "## Checks",
            "",
            "- Private source and OCR filenames are absent from public directories.",
            "- Project private directories are expected to be ignored by `.gitignore`.",
            "- `web/public/projects/index.json` is readable.",
            "- Public project `project.json` files exist.",
            "- `public_files` entries resolve in `web/public/projects/<slug>/`.",
            "- Route evidence quotes are checked for length warnings.",
            "- Public-facing text is checked for internal markers and high-risk navigation claims.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    root = repo_root()
    findings: list[Finding] = []

    check_gitignore(root, findings)
    check_forbidden_public_files(root, findings)
    projects = check_web_public_projects(root, findings)
    check_quotes(root, findings)
    check_text_markers(root, findings)

    report_path = root / "data" / "public_release_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    # Write in binary mode with explicit UTF-8 encoding so the line endings
    # are stable across invocation environments (PowerShell on Windows
    # triggers CRLF when text mode is used, breaking `git status`).
    report_path.write_bytes(render_report(findings, len(projects)).encode("utf-8"))

    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    print(f"Public release check: {'PASS' if not errors else 'FAIL'}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Report: {report_path}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
