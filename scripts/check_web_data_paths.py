from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB_SRC = ROOT / "web" / "src"
PATHS_TS = WEB_SRC / "utils" / "paths.ts"
REPORT = ROOT / "data" / "web_data_paths_report.md"

FORBIDDEN_PATTERNS = [
    (re.compile(r"fetch\(\s*['\"]\/projects"), "fetch('/projects or fetch(\"/projects"),
    (re.compile(r"fetch\(\s*`\/projects"), "fetch(`/projects"),
    (re.compile(r"fetch\(\s*['\"]\/data"), "fetch('/data or fetch(\"/data"),
    (re.compile(r"fetch\(\s*`\/data"), "fetch(`/data"),
    (re.compile(r"href\s*=\s*['\"]\/projects"), "href=\"/projects"),
    (re.compile(r"href\s*=\s*\{\s*['\"]\/projects"), "href={'/projects"),
    (re.compile(r"href\s*=\s*\{\s*`\/projects"), "href={`/projects"),
    (re.compile(r"href\s*=\s*['\"]\/data"), "href=\"/data"),
    (re.compile(r"href\s*=\s*\{\s*['\"]\/data"), "href={'/data"),
    (re.compile(r"href\s*=\s*\{\s*`\/data"), "href={`/data"),
]


def iter_source_files() -> list[Path]:
    return sorted(
        path
        for path in WEB_SRC.rglob("*")
        if path.suffix in {".ts", ".tsx", ".js", ".jsx"}
    )


def main() -> int:
    findings: list[tuple[str, int, str, str]] = []

    if not PATHS_TS.exists():
        findings.append((str(PATHS_TS.relative_to(ROOT)), 0, "missing", "web/src/utils/paths.ts is missing"))

    for path in iter_source_files():
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            for pattern, label in FORBIDDEN_PATTERNS:
                if pattern.search(line):
                    findings.append((str(path.relative_to(ROOT)), lineno, label, line.strip()))

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Web Data Paths Check",
        "",
        f"Status: {'FAIL' if findings else 'PASS'}",
        "",
        "Rules:",
        "- web/src must not fetch root-absolute /projects or /data paths.",
        "- web/src must not use root-absolute /projects or /data href values.",
        "- Project data paths should go through withBasePath, projectDataPath, or projectsIndexPath.",
        "",
    ]
    if findings:
        lines.extend(["Findings:", ""])
        for file, lineno, label, line in findings:
            loc = f"{file}:{lineno}" if lineno else file
            lines.append(f"- {loc}: {label}: `{line}`")
    else:
        lines.append("No forbidden root-absolute data paths found.")
    lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    if findings:
        print(f"FAIL: {len(findings)} forbidden path issue(s). See {REPORT}")
        return 1

    print(f"PASS: web data paths are base-path safe. See {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
