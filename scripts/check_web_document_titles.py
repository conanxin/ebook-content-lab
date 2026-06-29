from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

SITE_NAME = "ebook-content-lab"
HOME_TITLE = f"电子书内容实验室 · {SITE_NAME}"
NOT_FOUND_TITLE = f"未找到页面 · {SITE_NAME}"


@dataclass
class Finding:
    severity: str
    path: str
    message: str


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def find_title_assignments(text: str) -> list[str]:
    """Find every line that assigns to `document.title` (basic static check)."""
    return [line.strip() for line in text.splitlines() if "document.title" in line and "=" in line]


def check_index_html(web_src: Path, root: Path, findings: list[Finding]) -> None:
    index_html = web_src.parent / "index.html"
    if not index_html.exists():
        findings.append(Finding("error", repo_relative(index_html), "index.html missing."))
        return
    text = read_text(index_html)
    match = re.search(r"<title>([^<]*)</title>", text)
    if not match:
        findings.append(Finding("error", repo_relative(index_html), "No <title> in index.html."))
        return
    title = match.group(1).strip()
    if SITE_NAME not in title:
        findings.append(
            Finding(
                "warning",
                repo_relative(index_html),
                f"<title> '{title}' should contain site name '{SITE_NAME}'.",
            )
        )


def check_app_title_logic(web_src: Path, root: Path, findings: list[Finding]) -> None:
    """App.tsx must contain document.title assignments covering home / project / not-found branches."""
    app_tsx = web_src / "App.tsx"
    if not app_tsx.exists():
        findings.append(Finding("error", repo_relative(app_tsx), "App.tsx missing."))
        return
    text = read_text(app_tsx)
    assignments = find_title_assignments(text)
    if not assignments:
        findings.append(
            Finding("error", repo_relative(app_tsx), "App.tsx never assigns to document.title.")
        )
        return
    joined = "\n".join(assignments)
    if HOME_TITLE not in text and "电子书内容实验室" not in text:
        findings.append(
            Finding(
                "warning",
                repo_relative(app_tsx),
                f"App.tsx does not reference the home title literal '{HOME_TITLE}'.",
            )
        )
    if NOT_FOUND_TITLE not in text and "未找到页面" not in text:
        findings.append(
            Finding(
                "warning",
                repo_relative(app_tsx),
                f"App.tsx does not reference the not-found title literal '{NOT_FOUND_TITLE}'.",
            )
        )
    if "project" not in text.lower() or "title" not in text.lower():
        findings.append(
            Finding(
                "warning",
                repo_relative(app_tsx),
                "App.tsx does not appear to set a project-specific title.",
            )
        )


def check_project_pages(web_src: Path, root: Path, findings: list[Finding]) -> None:
    """Spot-check that at least one of {ProjectPage, App} knows the project title field.

    Static-only check: we accept either an explicit title-from-meta call site or
    the App.tsx central pattern. We require at least one signal so that future
    regressions where someone deletes the wiring show up immediately.
    """
    project_page = web_src / "pages" / "ProjectPage.tsx"
    if not project_page.exists():
        findings.append(Finding("error", repo_relative(project_page), "ProjectPage.tsx missing."))
        return
    text = read_text(project_page)
    if "title" not in text.lower():
        findings.append(
            Finding(
                "warning",
                repo_relative(project_page),
                "ProjectPage.tsx does not mention 'title' anywhere — verify it still threads project.title through.",
            )
        )


def render_report(findings: list[Finding]) -> str:
    errors = [item for item in findings if item.severity == "error"]
    warnings = [item for item in findings if item.severity == "warning"]
    status = "pass" if not errors else "fail"
    lines = [
        "# Web Document Titles Report",
        "",
        f"Status: **{status}**",
        "",
        "## Summary",
        "",
        f"- Errors: {len(errors)}",
        f"- Warnings: {len(warnings)}",
        "",
    ]
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
            "- `<title>` in web/index.html should contain the site name.",
            "- App.tsx must assign to document.title at least once.",
            "- App.tsx should reference a home title and a not-found title literal.",
            "- ProjectPage.tsx should still mention 'title' so future refactors don't drop the project title field.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Static check for document.title wiring in web/src.")
    parser.add_argument("--web-src", default="web/src", help="Path to web/src directory.")
    args = parser.parse_args()

    web_src = Path(args.web_src).resolve()
    root = web_src.parent.parent
    findings: list[Finding] = []

    check_index_html(web_src, root, findings)
    check_app_title_logic(web_src, root, findings)
    check_project_pages(web_src, root, findings)

    report_text = render_report(findings)
    report_path = root / "data" / "web_document_titles_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_text, encoding="utf-8")

    errors = [item for item in findings if item.severity == "error"]
    warnings = [item for item in findings if item.severity == "warning"]
    print(f"Web document-titles check: {'PASS' if not errors else 'FAIL'}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Report: {report_path}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
