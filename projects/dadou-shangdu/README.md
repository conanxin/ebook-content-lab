# dadou-shangdu

《从大都到上都》徒步路线图解项目。

- slug: `dadou-shangdu`
- project type: `route-map`
- source type: `scanned_pdf`
- status: `v0.4-local-accepted-needs-manual-review`

## 目录

```text
private/      本地私有材料：原书 PDF、OCR PDF、OCR 文本和分块
working/      抽取、证据审计、清理过程中的中间产物
public/       可发布数据：路线 JSON、GeoJSON、GPX、复走说明书
reports/      OCR、证据审计、GPX、验收和专项审查报告
review_pack/  人工复核 HTML 入口和 checklist
```

## 公开数据

公开发布数据位于 `public/`，并同步到：

```text
web/public/projects/dadou-shangdu/
```

包含：

- `project.json`
- `route_segments.json`
- `route.geojson`
- `route_places.geojson`
- `route.gpx`
- `route_walkable_blocks.json`
- `field_guide.md`

## 私有材料

`private/` 中包含原书 PDF、OCR PDF 和整书 OCR 文本。它们只用于本地复核与再处理，不应发布到 `web/public`，也不建议提交到公开仓库。

## 验收状态

详见：

- `reports/final_acceptance_report.md`
- `reports/seg009_consistency_review.md`
- `reports/review_notes.md`

当前数据已通过本地证据审计和前端构建，但仍需人工核对 OCR 地名、路线断点、补走/乘车上下文和现代路况。

