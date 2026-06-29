# ebook-content-lab

从电子书识别、证据抽取到可视化创作的开源项目集。

当前状态：`v0.5-online`

## Links

- GitHub 仓库：[https://github.com/conanxin/ebook-content-lab](https://github.com/conanxin/ebook-content-lab)
- 线上首页：[https://conanxin.github.io/ebook-content-lab/](https://conanxin.github.io/ebook-content-lab/)
- 《从大都到上都》子项目页面：[https://conanxin.github.io/ebook-content-lab/#/projects/dadou-shangdu](https://conanxin.github.io/ebook-content-lab/#/projects/dadou-shangdu)

## 当前子项目

- `projects/dadou-shangdu/`：《从大都到上都》徒步路线图解
- project type: `route-map`
- Web route: `#/projects/dadou-shangdu`

这个子项目把《从大都到上都》整理成按书中线索组织的路线地图页面。页面展示路线段、书中路线证据、章节出处、复走状态、断点、GPX 连接规则和复核提示。

重要说明：本页面不是未经核验的户外导航路线。坐标只是现代地图辅助定位；历史地名、乘车/补走、路线断点和现代路况仍需要复核。

## Online Deployment

本项目通过 GitHub Pages 部署，使用 GitHub Actions 自动构建 `web/dist`。

- Workflow: `.github/workflows/pages.yml`
- Publishing docs: `docs/publishing.md`
- Site base: `/ebook-content-lab/`
- Hash route example: `#/projects/dadou-shangdu`

## Local Development

Install dependencies:

```powershell
cd web
npm install
```

Run dev server:

```powershell
cd web
npm run dev -- --host 127.0.0.1
```

Build:

```powershell
cd web
npm run build
```

Public release check:

```powershell
python scripts\check_public_release.py
```

## Add a New Ebook Project

Create a scaffold:

```powershell
python scripts\create_project.py --slug another-book --title "《某书》时间线解读" --book-title "某书" --project-type timeline
```

Supported `project_type` values:

- `route-map`
- `timeline`
- `character-map`
- `place-index`
- `reading-guide`
- `quote-atlas`
- `knowledge-map`
- `field-guide`

Project workflow docs:

- `docs/add-new-book-project.md`
- `docs/project-lifecycle.md`
- `docs/architecture.md`

## Data Policy

The repository separates local source materials from public data:

- `projects/<slug>/private/`: source ebook files, OCR PDFs, OCR full text, and other local-only materials.
- `projects/<slug>/working/`: extraction and audit intermediates.
- `projects/<slug>/public/`: curated public structured data.
- `web/public/projects/<slug>/`: public data loaded by the web app.

Do not publish source PDFs, OCR full text, scan page images, or review packs containing original scan pages. Public data should contain only the structured data, short evidence snippets, GeoJSON, GPX, and public guide files needed by the site.

See `docs/data-policy.md`.

## License

- Code: MIT License, see `LICENSE`.
- Original documentation, structured data, and human-curated explanatory content: CC BY 4.0, see `LICENSE-CONTENT.md`.
- Files under `private/`, source ebooks, OCR full text, and scan page images are not part of the public release content and are not licensed by this repository.
