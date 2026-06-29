from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB_SRC = ROOT / "web" / "src"
REPORT = ROOT / "data" / "web_hash_routes_report.md"

FORBIDDEN_TEXT = [
    'href="#reading-detail"',
    "href='#reading-detail'",
    'href="#place-index"',
    "href='#place-index'",
    'href="#field-guide"',
    "href='#field-guide'",
    'href="#overview"',
    "href='#overview'",
    'href="#map-route"',
    "href='#map-route'",
    "window.location.hash = \"reading-detail\"",
    "window.location.hash = 'reading-detail'",
    "window.location.hash = \"place-index\"",
    "window.location.hash = 'place-index'",
    "window.location.hash = \"field-guide\"",
    "window.location.hash = 'field-guide'",
    "window.location.hash = \"overview\"",
    "window.location.hash = 'overview'",
    "window.location.hash = \"map-route\"",
    "window.location.hash = 'map-route'",
]

REQUIRED_ROUTE_MAP_TOKENS = [
    "getActiveTab",
    "setProjectTab",
    "projectTabUrl",
    "reading-detail",
    "place-index",
    "field-guide",
]

REQUIRED_HASH_ROUTE_TOKENS = [
    "getRouteQuery",
    "projectTabUrl",
    "legacyProjectTabUrl",
    "getLegacyTabFromHash",
]


def source_files() -> list[Path]:
    return sorted(path for path in WEB_SRC.rglob("*") if path.suffix in {".ts", ".tsx", ".js", ".jsx"})


def main() -> int:
    findings: list[str] = []

    for path in source_files():
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_TEXT:
            if token in text:
                findings.append(f"{path.relative_to(ROOT).as_posix()}: forbidden bare hash token `{token}`")

    route_page = WEB_SRC / "pages" / "RouteMapProjectPage.tsx"
    route_page_text = route_page.read_text(encoding="utf-8") if route_page.exists() else ""
    if not route_page.exists():
        findings.append("web/src/pages/RouteMapProjectPage.tsx is missing")
    else:
        for token in REQUIRED_ROUTE_MAP_TOKENS:
            if token not in route_page_text:
                findings.append(f"RouteMapProjectPage.tsx does not appear to support query tab token `{token}`")

    hash_route = WEB_SRC / "utils" / "hashRoute.ts"
    hash_route_text = hash_route.read_text(encoding="utf-8") if hash_route.exists() else ""
    if not hash_route.exists():
        findings.append("web/src/utils/hashRoute.ts is missing")
    else:
        for token in REQUIRED_HASH_ROUTE_TOKENS:
            if token not in hash_route_text:
                findings.append(f"hashRoute.ts missing `{token}`")
        if "?tab=" not in hash_route_text:
            findings.append("hashRoute.ts does not construct ?tab= URLs")

    app = WEB_SRC / "App.tsx"
    app_text = app.read_text(encoding="utf-8") if app.exists() else ""
    if "legacyProjectTabUrl" not in app_text or "legacy-tab" not in app_text:
        findings.append("App.tsx does not appear to handle legacy bare tab hashes")
    if r"(?:\?.*)?" not in app_text:
        findings.append("App.tsx route parser does not appear to accept hash-route query strings")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Web Hash Routes Report",
        "",
        f"Status: {'FAIL' if findings else 'PASS'}",
        "",
        "## Rules",
        "",
        "- Tab navigation must use `#/projects/<slug>?tab=<tab>`.",
        "- Bare hashes such as `#reading-detail` are not allowed in links.",
        "- Legacy bare hashes should be redirected or handled without showing NotFound.",
        "",
        "## Findings",
        "",
    ]
    lines.extend([f"- {finding}" for finding in findings] if findings else ["- None"])
    lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    if findings:
        print(f"Hash route check: FAIL ({len(findings)} findings)")
        print(f"Report: {REPORT}")
        return 1
    print("Hash route check: PASS")
    print(f"Report: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
