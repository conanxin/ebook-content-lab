# Data Policy

本仓库把“可公开代码和结构化数据”与“本地电子书源材料”分开管理。

## 可以公开的内容

通常可以公开：

- 平台代码和文档。
- `projects/<slug>/project.json`。
- `projects/<slug>/public/` 中经过整理的结构化数据。
- `web/public/projects/<slug>/` 中页面运行所需的数据。
- 短证据摘录、GeoJSON、GPX、公开说明书和项目索引。
- 不包含扫描图、OCR 全文或长篇原文摘录的复核清单。

公开内容应服务于页面阅读、证据追溯和数据复用，不应复制原书正文。

## 只保留本地的内容

不要提交或发布：

- 原始 PDF。
- OCR PDF。
- OCR 全文 Markdown。
- OCR 逐页 JSONL。
- OCR 分块 JSONL。
- 扫描页图片。
- `review_pack/pages/*.png`。
- 包含大段原文的临时文件。

这些文件可以存在于本地工作区，用于 OCR、证据审计和人工复核，但不进入公开仓库。

## 子项目目录职责

每个子项目使用：

- `private/`：本地源文件、OCR PDF、OCR 全文和其他私有材料。
- `working/`：抽取草稿、审计中间文件、待清理数据。
- `public/`：可以公开的结构化数据和读者说明。
- `reports/`：OCR、审计、校验、复核和验收报告。
- `review_pack/`：人工复核入口和 checklist；扫描页图片不公开。

## 发布到 web/public 的规则

`web/public/projects/<slug>/` 只放页面运行需要的公开数据，例如：

- `project.json`
- `route_segments.json`
- `route.geojson`
- `route_places.geojson`
- `route.gpx`
- `route_walkable_blocks.json`
- `field_guide.md`
- `review_index.md`，前提是不含扫描图或长篇原文摘录

不要把 `private/`、OCR 全文、扫描图或本地复核图片复制到 `web/public/`。

## 新增公开数据流程

1. 先将整理后的公开文件放入 `projects/<slug>/public/`。
2. 在 `projects/<slug>/project.json` 的 `public_files` 中登记。
3. 同步到 `web/public/projects/<slug>/`。
4. 确认证据摘录简短，且没有原书长篇内容。
5. 运行公开发布检查。

## 发布检查

运行：

```powershell
python scripts\check_public_release.py
```

报告输出：

```text
data/public_release_report.md
```

检查内容包括：

- 私有源文件是否误入公开目录。
- `projects/*/private/` 是否被 `.gitignore` 排除。
- `web/public/projects/index.json` 是否可读取。
- 每个项目的 `project.json` 是否存在。
- `public_files` 指向的文件是否存在。
- 路线证据 quote 是否过长。
- 页面文案是否包含高风险表述。
- 是否出现内部标记。
