from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_PUBLIC_FILES = [
    "book_overview.json",
    "chapter_reading_cards.json",
    "key_concepts.json",
    "quote_index.json",
    "reading_questions.json",
]

QUOTE_LIMIT = 120


@dataclass
class Finding:
    severity: str
    path: str
    message: str


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def repo_relative(path: Path) -> tuple[str, bool]:
    """Best-effort: return the project path relative to the repo root as a POSIX string.

    Returns (relative_path, is_repo_relative). When the project lives outside the
    repo (e.g. CI cache, /tmp), we fall back to the directory name and flag a
    warning via is_repo_relative=False — never emit a platform-specific absolute
    path, since that would create noise diffs between WSL and PowerShell.
    """
    resolved = path.resolve()
    cwd = Path.cwd().resolve()
    for candidate in (resolved, resolved.parent):
        try:
            return candidate.relative_to(cwd).as_posix(), True
        except ValueError:
            continue
    return resolved.name, False


def add(findings: list[Finding], severity: str, path: Path | str, message: str, root: Path) -> None:
    findings.append(Finding(severity=severity, path=rel(path, root) if isinstance(path, Path) else path, message=message))


def walk_evidence_refs(value: Any) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if {"page", "quote", "note"}.issubset(value.keys()):
            refs.append(value)
        for child in value.values():
            refs.extend(walk_evidence_refs(child))
    elif isinstance(value, list):
        for item in value:
            refs.extend(walk_evidence_refs(item))
    return refs


def status_of(data: Any) -> str:
    if isinstance(data, dict):
        value = data.get("status")
        if isinstance(value, str):
            return value
    return "unknown"


def validate_json_file(path: Path, root: Path, findings: list[Finding]) -> Any | None:
    if not path.exists():
        add(findings, "error", path, "Missing required reading-guide public file.", root)
        return None
    try:
        data = read_json(path)
    except Exception as exc:
        add(findings, "error", path, f"JSON parse failed: {exc}", root)
        return None
    if not isinstance(data, dict):
        add(findings, "error", path, "Top-level JSON value must be an object.", root)
        return None
    return data


def validate_evidence_refs(path: Path, data: Any, root: Path, findings: list[Finding]) -> None:
    for ref in walk_evidence_refs(data):
        quote = ref.get("quote")
        note = ref.get("note")
        page = ref.get("page")
        if not isinstance(quote, str):
            add(findings, "error", path, "evidence_ref.quote must be a string.", root)
        elif len(quote) > QUOTE_LIMIT:
            add(findings, "warning", path, f"evidence_ref.quote is {len(quote)} chars, over {QUOTE_LIMIT}.", root)
        if not isinstance(note, str) or not note.strip():
            add(findings, "error", path, "evidence_ref.note is required.", root)
        if page is not None and not isinstance(page, int):
            add(findings, "error", path, "evidence_ref.page must be an integer or null.", root)


def validate_non_draft(public_dir: Path, loaded: dict[str, Any], root: Path, findings: list[Finding]) -> None:
    cards = loaded.get("chapter_reading_cards.json")
    cards_path = public_dir / "chapter_reading_cards.json"
    chapters = cards.get("chapters") if isinstance(cards, dict) else None
    if not isinstance(chapters, list) or not chapters:
        add(findings, "error", cards_path, "Non-draft reading-guide projects must include chapter cards.", root)
        return

    for index, chapter in enumerate(chapters, start=1):
        if not isinstance(chapter, dict):
            add(findings, "error", cards_path, f"Chapter card #{index} must be an object.", root)
            continue
        refs = chapter.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            chapter_id = chapter.get("chapter_id") or f"#{index}"
            add(findings, "error", cards_path, f"Chapter {chapter_id} has no evidence_refs.", root)


def render_report(project_dir: Path, project: dict[str, Any] | None, loaded: dict[str, Any], findings: list[Finding]) -> str:
    errors = [item for item in findings if item.severity == "error"]
    warnings = [item for item in findings if item.severity == "warning"]
    status = "pass" if not errors else "fail"
    project_status = project.get("status", "unknown") if isinstance(project, dict) else "unknown"

    lines = [
        "# Reading Guide Validation Report",
        "",
        f"Project: `{project_dir.as_posix()}`",
        f"Status: **{status}**",
        f"Project status: `{project_status}`",
        "",
        "## Required Public Files",
        "",
    ]
    for name in REQUIRED_PUBLIC_FILES:
        file_status = "ok" if name in loaded else "missing"
        file_data_status = status_of(loaded.get(name)) if name in loaded else "unknown"
        lines.append(f"- `{name}`: {file_status}, data status `{file_data_status}`")

    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Errors: {len(errors)}",
            f"- Warnings: {len(warnings)}",
            "",
        ]
    )

    if errors:
        lines.extend(["## Errors", ""])
        for item in errors:
            lines.append(f"- `{item.path}`: {item.message}")
        lines.append("")
    else:
        lines.extend(["## Errors", "", "- None", ""])

    if warnings:
        lines.extend(["## Warnings", ""])
        for item in warnings:
            lines.append(f"- `{item.path}`: {item.message}")
        lines.append("")
    else:
        lines.extend(["## Warnings", "", "- None", ""])

    lines.extend(
        [
            "## Rules",
            "",
            "- `project.json` must exist and declare `project_type: reading-guide`.",
            "- Draft projects may keep content arrays empty.",
            "- Non-draft projects must include chapter cards with evidence references.",
            "- Evidence quotes should be short and no longer than 120 characters.",
            "",
        ]
    )
    return "\n".join(lines)


def validate_project(project_dir: Path) -> tuple[dict[str, Any] | None, dict[str, Any], list[Finding]]:
    root = project_dir.parent.parent if project_dir.parent.name == "projects" else project_dir.parent
    findings: list[Finding] = []
    loaded: dict[str, Any] = {}

    project_json = project_dir / "project.json"
    project: dict[str, Any] | None = None
    if not project_json.exists():
        add(findings, "error", project_json, "Missing project.json.", root)
    else:
        try:
            project_data = read_json(project_json)
            if not isinstance(project_data, dict):
                add(findings, "error", project_json, "project.json must be an object.", root)
            else:
                project = project_data
                if project.get("project_type") != "reading-guide":
                    add(findings, "error", project_json, "project_type must be reading-guide.", root)
        except Exception as exc:
            add(findings, "error", project_json, f"Cannot read project.json: {exc}", root)

    public_dir = project_dir / "public"
    for name in REQUIRED_PUBLIC_FILES:
        path = public_dir / name
        data = validate_json_file(path, root, findings)
        if data is None:
            continue
        loaded[name] = data
        validate_evidence_refs(path, data, root, findings)

    project_status = project.get("status", "unknown") if isinstance(project, dict) else "unknown"
    if project_status != "draft":
        validate_non_draft(public_dir, loaded, root, findings)

    return project, loaded, findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a reading-guide project skeleton or public dataset.")
    parser.add_argument("--project", required=True, help="Path to projects/<slug>.")
    args = parser.parse_args()

    project_dir = Path(args.project).resolve()
    project, loaded, findings = validate_project(project_dir)

    report_path = project_dir / "reports" / "reading_guide_validation_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_text = render_report(project_dir, project, loaded, findings)

    # Stabilise the Project line so WSL vs PowerShell doesn't churn the report.
    # We only rewrite the single `Project:` line that render_report just emitted;
    # everything else is byte-for-byte identical to the prior version.
    display_path, is_repo_relative = repo_relative(project_dir)
    if is_repo_relative:
        report_text = report_text.replace(
            f"Project: `{project_dir.as_posix()}`",
            f"Project: `{display_path}`",
            1,
        )
    else:
        # Fall back to the project directory name (no absolute path) and append
        # a one-line warning so the report still records the situation.
        report_text = report_text.replace(
            f"Project: `{project_dir.as_posix()}`",
            f"Project: `{display_path}`",
            1,
        )
        report_text += f"\n<!-- path-warning: project dir is outside the repo ({project_dir.as_posix()}). Report shows directory name only. -->\n"

    report_path.write_text(report_text, encoding="utf-8")

    errors = [item for item in findings if item.severity == "error"]
    warnings = [item for item in findings if item.severity == "warning"]
    print(f"Reading-guide validation: {'PASS' if not errors else 'FAIL'}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Report: {report_path}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
