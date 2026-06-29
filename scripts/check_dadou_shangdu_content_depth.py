from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "projects" / "dadou-shangdu"
PUBLIC = PROJECT / "public"
WEB_PUBLIC = ROOT / "web" / "public" / "projects" / "dadou-shangdu"
REPORT = PROJECT / "reports" / "content_depth_report.md"

REQUIRED_PLACES = {
    "旧县村",
    "八达岭关城",
    "居庸关云台",
    "不堡子村",
    "塘子庙",
    "馒头山村",
    "石柱村",
    "水泉淖尔",
    "圆图淖尔",
    "河北内蒙古分界线",
    "滦河东岸沙丘",
}

REQUIRED_THEMES = {
    "大都到上都的路线结构",
    "关口与边界",
    "水源与湖淖",
    "村镇与补给",
    "徒步、乘车与断点",
    "历史地名与现代定位",
}

QUOTE_LIMIT = 120
MAX_PUBLIC_TEXT_VALUE = 900
MAX_JSON_BYTES = 250_000
ROUTE_FILES = [
    "projects/dadou-shangdu/public/route_segments.json",
    "projects/dadou-shangdu/public/route.geojson",
    "projects/dadou-shangdu/public/route.gpx",
    "web/public/projects/dadou-shangdu/route_segments.json",
    "web/public/projects/dadou-shangdu/route.geojson",
    "web/public/projects/dadou-shangdu/route.gpx",
    "data/route_segments.json",
    "data/route.geojson",
    "data/route.gpx",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def walk_strings(value: Any, path: str = "$") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, str):
        found.append((path, value))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(walk_strings(item, f"{path}[{index}]"))
    elif isinstance(value, dict):
        for key, item in value.items():
            found.extend(walk_strings(item, f"{path}.{key}"))
    return found


def walk_refs(value: Any) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if {"page", "quote", "note"}.issubset(value.keys()):
            refs.append(value)
        for child in value.values():
            refs.extend(walk_refs(child))
    elif isinstance(value, list):
        for item in value:
            refs.extend(walk_refs(item))
    return refs


def git_has_diff(paths: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--", *paths],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError:
        return False, "git not found; route data diff check skipped"
    changed = [line for line in result.stdout.splitlines() if line.strip()]
    return bool(changed), "\n".join(changed)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    details: list[str] = []

    files = {
        "book_overview": PUBLIC / "book_overview.json",
        "segment_cards": PUBLIC / "segment_reading_cards.json",
        "place_index": PUBLIC / "place_index.json",
        "book_themes": PUBLIC / "book_themes.json",
    }

    data: dict[str, Any] = {}
    for key, path in files.items():
        if not path.exists():
            errors.append(f"Missing {path.as_posix()}")
            continue
        if path.stat().st_size > MAX_JSON_BYTES:
            errors.append(f"{path.as_posix()} is unexpectedly large ({path.stat().st_size} bytes)")
        try:
            data[key] = read_json(path)
        except Exception as exc:
            errors.append(f"Cannot read {path.as_posix()}: {exc}")

        web_copy = WEB_PUBLIC / path.name
        if not web_copy.exists():
            errors.append(f"Missing synced web copy: {web_copy.as_posix()}")
        elif path.read_bytes() != web_copy.read_bytes():
            errors.append(f"Web copy is not synced: {web_copy.as_posix()}")

    cards = data.get("segment_cards")
    if isinstance(cards, list):
        if len(cards) != 15:
            errors.append(f"segment_reading_cards.json must contain 15 cards, found {len(cards)}")
        for card in cards:
            segment_id = card.get("segment_id", "unknown") if isinstance(card, dict) else "unknown"
            refs = card.get("evidence_refs", []) if isinstance(card, dict) else []
            if not isinstance(refs, list) or len(refs) < 3:
                errors.append(f"{segment_id} has fewer than 3 evidence_refs")
            for index, ref in enumerate(refs):
                if not isinstance(ref, dict):
                    errors.append(f"{segment_id} evidence_refs[{index}] is not an object")
                    continue
                for field in ["page", "quote", "note"]:
                    if ref.get(field) in (None, ""):
                        errors.append(f"{segment_id} evidence_refs[{index}] missing {field}")
                quote = str(ref.get("quote") or "")
                if len(quote) > QUOTE_LIMIT:
                    errors.append(f"{segment_id} evidence_refs[{index}] quote length {len(quote)} > {QUOTE_LIMIT}")
            details.append(f"- {segment_id}: {len(refs) if isinstance(refs, list) else 0} evidence_refs")
    elif "segment_cards" in data:
        errors.append("segment_reading_cards.json must be a list")

    places = data.get("place_index")
    if isinstance(places, list):
        place_names = {str(item.get("name")) for item in places if isinstance(item, dict)}
        missing = sorted(REQUIRED_PLACES - place_names)
        if missing:
            errors.append("place_index.json missing required places: " + ", ".join(missing))
        if len(places) < len(REQUIRED_PLACES):
            errors.append(f"place_index.json must contain at least {len(REQUIRED_PLACES)} places, found {len(places)}")
    elif "place_index" in data:
        errors.append("place_index.json must be a list")

    themes = data.get("book_themes")
    if isinstance(themes, list):
        theme_names = {str(item.get("theme")) for item in themes if isinstance(item, dict)}
        missing = sorted(REQUIRED_THEMES - theme_names)
        if missing:
            errors.append("book_themes.json missing required themes: " + ", ".join(missing))
        if len(themes) < len(REQUIRED_THEMES):
            errors.append(f"book_themes.json must contain at least {len(REQUIRED_THEMES)} themes, found {len(themes)}")
    elif "book_themes" in data:
        errors.append("book_themes.json must be a list")

    for key, value in data.items():
        for ref in walk_refs(value):
            quote = str(ref.get("quote") or "")
            if len(quote) > QUOTE_LIMIT:
                errors.append(f"{key} has quote over {QUOTE_LIMIT} chars: {quote[:40]}")
        for json_path, text in walk_strings(value):
            if len(text) > MAX_PUBLIC_TEXT_VALUE:
                errors.append(f"{key} contains a long text value at {json_path} ({len(text)} chars)")

    changed, diff_text = git_has_diff(ROUTE_FILES)
    if changed:
        errors.append("Route data files have uncommitted diffs:\n" + diff_text)
    elif diff_text:
        warnings.append(diff_text)

    status = "PASS" if not errors else "FAIL"
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    error_lines = [f"- {item}" for item in errors] if errors else ["- None"]
    warning_lines = [f"- {item}" for item in warnings] if warnings else ["- None"]

    lines = [
        "# Dadou-Shangdu Content Depth Report",
        "",
        f"Status: **{status}**",
        "",
        "## Summary",
        "",
        f"- segment_reading_cards: {len(cards) if isinstance(cards, list) else 'unreadable'}",
        f"- place_index: {len(places) if isinstance(places, list) else 'unreadable'}",
        f"- book_themes: {len(themes) if isinstance(themes, list) else 'unreadable'}",
        f"- quote limit: {QUOTE_LIMIT}",
        f"- route data modified: {'yes' if changed else 'no'}",
        "",
        "## Segment Evidence Counts",
        "",
        *(details or ["- Unavailable"]),
        "",
        "## Errors",
        "",
        *error_lines,
        "",
        "## Warnings",
        "",
        *warning_lines,
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"Content depth check: {status}")
    print(f"Report: {REPORT}")
    if errors:
        print(f"Errors: {len(errors)}")
        return 1
    print("Errors: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
