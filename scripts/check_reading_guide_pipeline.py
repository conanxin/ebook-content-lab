from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PUBLIC_SCAN_PATTERNS = [
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

REPORT_BODY_PATTERNS = [
    "full_text",
    "raw_text",
    "chapter_text",
]


@dataclass
class Finding:
    severity: str
    path: str
    message: str


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "scripts").is_dir() and (candidate / "web").is_dir():
            return candidate
    raise FileNotFoundError(f"Cannot find repo root above {start}")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def add(findings: list[Finding], severity: str, path: Path | str, message: str, root: Path) -> None:
    findings.append(Finding(severity, rel(path, root) if isinstance(path, Path) else path, message))


def run_inspect(repo_root: Path, project_dir: Path) -> tuple[dict[str, Any] | None, str | None]:
    script = repo_root / "scripts" / "inspect_reading_guide_pipeline.py"
    result = subprocess.run(
        [sys.executable, str(script), "--project", str(project_dir)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        return None, result.stderr or result.stdout
    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError as exc:
        return None, f"inspect output is not JSON: {exc}"


def source_type_is_epub(project_data: dict[str, Any]) -> bool:
    book = project_data.get("book")
    book_source = book.get("source_type") if isinstance(book, dict) else None
    return book_source == "epub" or project_data.get("source_type") == "epub" or project_data.get("identity_status") == "identified"


def scan_public_json(project_dir: Path, repo_root: Path, findings: list[Finding]) -> None:
    public_roots = [
        project_dir / "public",
        repo_root / "web" / "public" / "projects" / project_dir.name,
    ]
    for base in public_roots:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".json", ".md", ".txt"}:
                continue
            if path.name == "project.json":
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            lowered = text.lower()
            for pattern in PUBLIC_SCAN_PATTERNS:
                if pattern.lower() in lowered:
                    add(findings, "error", path, f"Public file contains private/full-text marker `{pattern}`.", repo_root)


def scan_reports_for_body_text(project_dir: Path, repo_root: Path, findings: list[Finding]) -> None:
    reports_dir = project_dir / "reports"
    if not reports_dir.exists():
        return
    for path in reports_dir.glob("*.md"):
        text = path.read_text(encoding="utf-8", errors="replace")
        lowered = text.lower()
        for pattern in REPORT_BODY_PATTERNS:
            if pattern.lower() in lowered:
                add(findings, "error", path, f"Report contains body-text marker `{pattern}`.", repo_root)
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if len(stripped) > 1000:
                add(findings, "warning", path, f"Line {line_no} is over 1000 chars; review for long excerpt risk.", repo_root)


def required_path(path: Path, label: str, findings: list[Finding], root: Path) -> None:
    if not path.exists():
        add(findings, "error", path, f"Missing required {label}.", root)


def report_path_for(project_dir: Path, version: str) -> Path:
    normalized = version.lower().replace("-", "_")
    return project_dir / "reports" / f"{normalized}_pipeline_check.md"


def render_report(project_dir: Path, version: str, inspect_data: dict[str, Any] | None, findings: list[Finding], root: Path) -> str:
    errors = [item for item in findings if item.severity == "error"]
    warnings = [item for item in findings if item.severity == "warning"]
    status = "pass" if not errors else "fail"

    lines = [
        "# Reading Guide Pipeline Check",
        "",
        f"Version: `{version}`",
        f"Project: `{rel(project_dir, root)}`",
        f"Status: **{status}**",
        "",
        "## R2 Baseline",
        "",
        "- This check validates EPUB intake readiness.",
        "- It does not require `reviewed-draft` status.",
        "- It does not require manual review summary artifacts.",
        "- It does not require final public content counts.",
        "",
    ]
    if inspect_data:
        lines.extend(
            [
                "## Inspect Summary",
                "",
                f"- Project status: `{inspect_data.get('status')}`",
                f"- Source type: `{inspect_data.get('source_type')}`",
                f"- Intake ready: `{inspect_data.get('intake_ready')}`",
                f"- EPUB source present: `{inspect_data.get('epub_source_present')}`",
                f"- Identity artifacts present: `{inspect_data.get('identity_artifacts_present')}`",
                f"- Public layer present: `{inspect_data.get('public_layer_present')}`",
                f"- Web mirror present: `{inspect_data.get('web_mirror_present')}`",
                f"- Privacy boundary ok: `{inspect_data.get('privacy_boundary_ok')}`",
                f"- Missing next artifacts: `{', '.join(inspect_data.get('missing_next_artifacts') or []) or 'none'}`",
                "",
            ]
        )

    lines.extend(["## Errors", ""])
    if errors:
        for item in errors:
            lines.append(f"- `{item.path}`: {item.message}")
    else:
        lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    if warnings:
        for item in warnings:
            lines.append(f"- `{item.path}`: {item.message}")
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def check_project(project_dir: Path, version: str) -> tuple[list[Finding], dict[str, Any] | None]:
    repo_root = find_repo_root(project_dir)
    findings: list[Finding] = []

    inspect_data, inspect_error = run_inspect(repo_root, project_dir)
    if inspect_error:
        add(findings, "error", repo_root / "scripts" / "inspect_reading_guide_pipeline.py", f"Inspect script failed: {inspect_error}", repo_root)

    project_json = project_dir / "project.json"
    required_path(project_json, "project.json", findings, repo_root)
    project_data: dict[str, Any] = {}
    if project_json.exists():
        try:
            project_data = read_json(project_json)
        except Exception as exc:
            add(findings, "error", project_json, f"Cannot read project.json: {exc}", repo_root)

    if project_data and not source_type_is_epub(project_data):
        add(findings, "error", project_json, "Project metadata does not indicate EPUB intake.", repo_root)

    required_path(repo_root / "scripts" / "extract_epub.py", "extract_epub.py", findings, repo_root)
    required_path(repo_root / "scripts" / "identify_book.py", "identify_book.py", findings, repo_root)
    required_path(project_dir / "working" / "book_identity.json", "working/book_identity.json", findings, repo_root)
    required_path(project_dir / "working" / "book_identity_source.json", "working/book_identity_source.json", findings, repo_root)
    required_path(project_dir / "reports" / "book_identity_report.md", "reports/book_identity_report.md", findings, repo_root)
    required_path(project_dir / "reports" / "epub_extraction_report.md", "reports/epub_extraction_report.md", findings, repo_root)

    scan_public_json(project_dir, repo_root, findings)
    scan_reports_for_body_text(project_dir, repo_root, findings)

    if inspect_data:
        if not inspect_data.get("intake_ready"):
            add(findings, "error", project_dir, "inspect reports intake_ready=false.", repo_root)
        if not inspect_data.get("privacy_boundary_ok"):
            add(findings, "error", project_dir, "inspect reports privacy_boundary_ok=false.", repo_root)

    return findings, inspect_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Check reading-guide EPUB intake pipeline baseline.")
    parser.add_argument("--project", required=True, help="Path to projects/<slug>.")
    parser.add_argument("--version", required=True, help="Pipeline version label, e.g. v0.7-R2.")
    args = parser.parse_args()

    project_dir = Path(args.project).resolve()
    repo_root = find_repo_root(project_dir)
    findings, inspect_data = check_project(project_dir, args.version)
    report_path = report_path_for(project_dir, args.version)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(project_dir, args.version, inspect_data, findings, repo_root), encoding="utf-8")

    errors = [item for item in findings if item.severity == "error"]
    warnings = [item for item in findings if item.severity == "warning"]
    print(f"Reading-guide pipeline check: {'PASS' if not errors else 'FAIL'}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Report: {report_path}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
