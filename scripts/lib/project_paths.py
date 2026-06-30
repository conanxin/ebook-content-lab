from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    """Find the repository root by walking upward from a project path.

    The repo root is defined conservatively as a directory that contains both
    `scripts/` and `web/`. This avoids depending on git metadata and works in
    both Windows and WSL path layouts.
    """
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "scripts").is_dir() and (candidate / "web").is_dir():
            return candidate
    raise FileNotFoundError(f"Cannot find repo root above {start}")


@dataclass(frozen=True)
class ProjectPaths:
    repo_root: Path
    project_dir: Path
    slug: str
    project_json: Path
    private_dir: Path
    source_dir: Path
    epub_path: Path
    working_dir: Path
    reports_dir: Path
    public_dir: Path
    web_public_dir: Path
    web_project_dir: Path
    web_index_json: Path
    book_identity_json: Path
    book_identity_source_json: Path
    epub_extraction_report: Path
    book_identity_report: Path
    book_overview_json: Path
    chapter_reading_cards_json: Path
    key_concepts_json: Path
    quote_index_json: Path
    reading_questions_json: Path
    web_book_overview_json: Path
    web_chapter_reading_cards_json: Path
    web_key_concepts_json: Path
    web_quote_index_json: Path
    web_reading_questions_json: Path

    @classmethod
    def from_project(cls, project_path: str | Path) -> "ProjectPaths":
        project_dir = Path(project_path).resolve()
        repo_root = find_repo_root(project_dir)
        slug = project_dir.name

        private_dir = project_dir / "private"
        source_dir = private_dir / "source"
        working_dir = project_dir / "working"
        reports_dir = project_dir / "reports"
        public_dir = project_dir / "public"
        web_public_dir = repo_root / "web" / "public"
        web_project_dir = web_public_dir / "projects" / slug

        return cls(
            repo_root=repo_root,
            project_dir=project_dir,
            slug=slug,
            project_json=project_dir / "project.json",
            private_dir=private_dir,
            source_dir=source_dir,
            epub_path=source_dir / "book.epub",
            working_dir=working_dir,
            reports_dir=reports_dir,
            public_dir=public_dir,
            web_public_dir=web_public_dir,
            web_project_dir=web_project_dir,
            web_index_json=web_public_dir / "projects" / "index.json",
            book_identity_json=working_dir / "book_identity.json",
            book_identity_source_json=working_dir / "book_identity_source.json",
            epub_extraction_report=reports_dir / "epub_extraction_report.md",
            book_identity_report=reports_dir / "book_identity_report.md",
            book_overview_json=public_dir / "book_overview.json",
            chapter_reading_cards_json=public_dir / "chapter_reading_cards.json",
            key_concepts_json=public_dir / "key_concepts.json",
            quote_index_json=public_dir / "quote_index.json",
            reading_questions_json=public_dir / "reading_questions.json",
            web_book_overview_json=web_project_dir / "book_overview.json",
            web_chapter_reading_cards_json=web_project_dir / "chapter_reading_cards.json",
            web_key_concepts_json=web_project_dir / "key_concepts.json",
            web_quote_index_json=web_project_dir / "quote_index.json",
            web_reading_questions_json=web_project_dir / "reading_questions.json",
        )

    def report_path(self, name: str) -> Path:
        return self.reports_dir / name

    def working_path(self, name: str) -> Path:
        return self.working_dir / name

    def public_path(self, name: str) -> Path:
        return self.public_dir / name

    def web_project_path(self, name: str) -> Path:
        return self.web_project_dir / name

    def pipeline_check_report(self, version: str) -> Path:
        normalized = version.lower().replace("-", "_")
        return self.report_path(f"{normalized}_pipeline_check.md")


def from_project(project_path: str | Path) -> ProjectPaths:
    return ProjectPaths.from_project(project_path)
