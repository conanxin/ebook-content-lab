# Project Lifecycle

一个电子书内容子项目建议按以下阶段推进。每一步都应保留证据边界：书中事实、模型整理、现代辅助资料和人工复核意见要分开记录。

## 01 电子书输入

1. 创建子项目：

   ```powershell
   python scripts\create_project.py --slug <slug> --title "<项目标题>" --book-title "<书名>" --project-type <type>
   ```

2. 将电子书源文件放入：

   ```text
   projects/<slug>/private/source/book.pdf
   ```

3. 原始 PDF、扫描图和授权不明的源文件只保留在 `private/`，不要复制到 `web/public/`。

## 02 OCR

扫描版 PDF 需要先 OCR。当前历史脚本仍兼容旧路径：

```powershell
python scripts\ocr_pdf.py source\book.pdf --out-dir data\ocr --lang chi_sim+eng
```

新项目应把持久化 OCR 产物整理回：

```text
projects/<slug>/private/ocr/
projects/<slug>/private/
```

常见产物包括 OCR PDF、逐页 JSONL、清洗后 JSONL、分块 JSONL 和 `book.md`。这些属于本地材料，不进入公开发布目录。

## 03 电子书识别

运行本地识别：

```powershell
python scripts\identify_book.py --project projects\<slug> --output projects\<slug>\reports\book_identity_report.md
```

识别内容包括书名、作者、出版信息、目录页范围、章节结构、总页数、语言、扫描版状态、OCR 状态、内容类型建议和项目类型建议。

未知字段保持 `unknown` 或 `null`，不使用外部网络搜索补写。

## 04 内容抽取

根据 `project_type` 选择结构化抽取方式：

- `route-map`：路线段、地点、书中证据、GeoJSON、GPX、复走说明。
- `timeline`：时间、事件、人物、地点、页码证据。
- `character-map`：人物、关系、章节证据。
- `place-index`：地点、别名、上下文、页码证据。
- `reading-guide`：章节说明、主题、问题、短证据。
- `quote-atlas`：短引文、主题、页码、说明。
- `knowledge-map`：概念、关系、来源。
- `field-guide`：保守的实地复核说明。

抽取草稿放在：

```text
projects/<slug>/working/
```

## 05 证据审计

每条结构化事实都应能追溯到书中页码和短摘。审计重点：

- 引文是否能在对应 OCR 页找到。
- 章节出处是否和路线或内容事实分开。
- 模型推断是否被误写成书中事实。
- 现代资料是否只用于辅助定位或复核，不用于改写书中顺序。
- 字段为空时是否明确写 `null`、`unknown` 或“书中未明示”。

审计报告放在：

```text
projects/<slug>/reports/
```

## 06 人工复核

人工复核用于检查 OCR、地名、页码证据和不确定字段。复核材料放在：

```text
projects/<slug>/review_pack/
```

如果包含扫描页图片，只能本地使用，不发布到 `web/public/`。

## 07 公开数据生成

公开数据放在：

```text
projects/<slug>/public/
```

可公开内容通常包括：

- `project.json`
- 结构化 JSON
- GeoJSON 或其他可视化数据
- GPX 或其他导出文件
- 面向读者的 Markdown 说明

公开数据不应包含原始 PDF、OCR 全文、扫描图或长篇原文摘录。

## 08 页面发布

同步公开数据到：

```text
web/public/projects/<slug>/
```

更新：

```text
web/public/projects/index.json
```

发布前运行：

```powershell
python scripts\check_public_release.py
cd web
npm run build
```

GitHub Pages 发布见 `docs/publishing.md`。
