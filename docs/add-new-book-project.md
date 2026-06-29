# Add a New Ebook Project

本指南说明如何为 `ebook-content-lab` 新增一本电子书子项目。

## 1. 创建项目骨架

运行：

```powershell
python scripts\create_project.py --slug another-book --title "《某书》时间线解读" --book-title "某书" --project-type timeline
```

`slug` 只能使用小写字母、数字和短横线。脚本不会覆盖已有的 `projects/<slug>` 或 `web/public/projects/<slug>`。

支持的 `project_type`：

- `route-map`
- `timeline`
- `character-map`
- `place-index`
- `reading-guide`
- `quote-atlas`
- `knowledge-map`
- `field-guide`

新项目默认 `status: draft`，`public_files` 为空，质量字段为 `unknown`。

## 2. 放入电子书源文件

将电子书放在：

```text
projects/<slug>/private/source/book.pdf
```

不要把源 PDF、OCR PDF、扫描页图片或私有复核材料复制到 `web/public/`。

## 3. 运行 OCR

当前 OCR 脚本仍支持旧的兼容路径：

```powershell
python scripts\ocr_pdf.py source\book.pdf --out-dir data\ocr --lang chi_sim+eng
```

新项目完成 OCR 后，应把持久化结果整理到：

```text
projects/<slug>/private/ocr/
projects/<slug>/private/
```

常见本地 OCR 产物：

- `private/ocr/book_ocr.pdf`
- `private/book.md`
- `private/book_pages.jsonl`
- `private/book_pages.cleaned.jsonl`
- `private/book_chunks.jsonl`

这些文件不属于公开发布内容。

## 4. 运行电子书识别

```powershell
python scripts\identify_book.py --project projects\<slug> --output projects\<slug>\reports\book_identity_report.md
```

输出：

```text
projects/<slug>/reports/book_identity_report.md
projects/<slug>/working/book_identity.json
```

脚本会更新 `projects/<slug>/project.json` 中的 `book`、`suggested_content_types`、`suggested_project_types` 和 `identity_status`。识别只使用本地文件，不使用外部网络搜索。

## 5. 清洗和分块

如果使用兼容路径，可运行：

```powershell
python scripts\clean_ocr_text.py --input data\book_pages.jsonl --output data\book_pages.cleaned.jsonl
python scripts\chunk_book.py --input data\book_pages.cleaned.jsonl --output data\book_chunks.jsonl --max-chars 3500
```

完成后把本项目的持久化文本产物整理到 `projects/<slug>/private/`。

## 6. 做结构化抽取

按项目类型选择抽取目标：

- `route-map`：路线段、地点、方向、证据、GeoJSON、GPX、复走说明。
- `timeline`：日期、事件、人物、地点、证据。
- `character-map`：人物、关系、章节证据。
- `place-index`：地名、别名、上下文、证据。
- `reading-guide`：章节概括、主题、问题、短证据。
- `quote-atlas`：短引文、主题、页码、说明。
- `knowledge-map`：概念、关系、来源。
- `field-guide`：保守的复核说明和实践提示。

中间稿放入：

```text
projects/<slug>/working/
```

## 7. 做证据审计

审计要求：

- 每条事实尽量有页码和短摘。
- 短摘只保留必要证据，不复制长篇原文。
- 章节出处和事实证据分开。
- 不确定字段显式标记。
- 不用现代资料改写书中事实。

报告放入：

```text
projects/<slug>/reports/
```

## 8. 生成人工复核材料

人工复核包放入：

```text
projects/<slug>/review_pack/
```

如果包含扫描页图片，只能本地使用。不要把 `review_pack/pages/` 发布到 `web/public/`。

## 9. 生成公开数据

公开数据放入：

```text
projects/<slug>/public/
```

并同步到：

```text
web/public/projects/<slug>/
```

同步后更新 `projects/<slug>/project.json` 的 `public_files`，并确保 `web/public/projects/index.json` 包含该项目。

## 10. 发布前检查

运行：

```powershell
python scripts\check_public_release.py
cd web
npm run build
```

检查报告：

```text
data/public_release_report.md
```

## 11. 模板脚本测试

可用以下命令测试项目创建：

```powershell
python scripts\create_project.py --slug example-project --title "示例电子书项目" --book-title "示例书名" --project-type reading-guide
```

预期结果：

- `projects/example-project/` 被创建。
- `projects/example-project/project.json` 状态为 `draft`。
- `web/public/projects/example-project/project.json` 被创建。
- `web/public/projects/index.json` 增加 `example-project`。

测试后清理：

```powershell
Remove-Item -Recurse -Force projects\example-project
Remove-Item -Recurse -Force web\public\projects\example-project
```

然后从 `web/public/projects/index.json` 移除 `example-project`。
