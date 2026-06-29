# 最终本地验收报告

- 验收时间：2026-06-29 10:04 本地重跑
- 项目路径：`D:\WSL\Codex`
- 状态结论：v0.4 可交付，但仍保留人工复核事项

## 1. 核心文件完整性

必需核心文件全部存在，包括：

- 原始 PDF、OCR PDF、OCR 文本与分块数据
- 正式路线 JSON、GeoJSON、GPX、连续徒步块
- 证据审计、证据清理、连续性、状态矩阵、校验、GPX 导出报告
- 复走说明书与人工复核包
- 前端 `web/public/data` 数据与 `web/src/App.tsx`

检查结果：通过，缺失文件数 0。

## 2. OCR 页数和质量摘要

- 总页数：360
- OCR 成功页数：332
- 空文本页数：28
- 字符数过少页：31
- 疑似识别错误页：59
- 平均每页字符数：530.4
- 清洗后总字符数：187,923
- 清洗后需复核页数：59

质量结论：OCR 已足以支撑路线抽取和证据审计，但标题页、插图页、低字符页和疑似识别错误页仍必须人工抽查。路线项目已把这些风险写入复核说明和复核包。

## 3. 路线数据与证据审计

- 路线段数：15
- 每段均有 `book_refs`
- `chapter_refs` 已与路线事实证据分开
- 证据审计结果：pass 15，warning 0，fail 0
- 证据不足字段数：0
- 路线校验结果：Errors 0，Warnings 0

证据结论：当前正式路线数据已通过本地证据审计；仍需人工回看 PDF 核对 OCR 地名、标题页、断点和乘车/补走上下文。

## 4. 复走状态统计

### movement_type

- walked：7
- mixed：8
- vehicle：0
- inferred：0
- unclear：0

### continuity_status

- continuous：6
- gap_before：4
- gap_after：4
- isolated：1
- unclear：0

### walkability_status

- book_walkable：8
- partially_walkable：7
- not_walkable_as_written：0
- needs_review：0

### modern_followability

- likely_followable：0
- approximate_only：8
- not_enough_information：0
- needs_field_check：7

## 5. GPX 导出结果

- Waypoints：99
- 连续 track：8
- 缺坐标未导出项：无
- 只导出 waypoint / 不应连接 GPX 的段落：7

不应连接 GPX 的 segment：

- `seg-003` 居庸关到延庆
- `seg-008` 白草镇到老掌沟
- `seg-010` 小厂镇到五花草甸
- `seg-011` 五花草甸到沽源
- `seg-013` 塞北管理区到黑城子
- `seg-014` 黑城子到四郎城
- `seg-015` 四郎城到上都遗址

GPX 结论：GPX 没有把断点、补走、乘车或需复核段强连成连续 track。只导出 waypoint 的段落已在报告和页面中标明。

## 6. 前端与 public 数据

重跑命令：

```powershell
python scripts\validate_route.py data\route_segments.json
python scripts\export_gpx.py data\route_segments.json --output data\route.gpx
cd web
npm run build
```

结果：

- `validate_route.py`：通过
- `export_gpx.py`：通过，99 waypoint，8 track，7 skipped
- `npm run build`：通过
- `web/public/data` 与 `data` 对应文件同步：通过

同步核对通过的文件：

- `route_segments.json`
- `route.geojson`
- `route_places.geojson`
- `route.gpx`
- `route_walkable_blocks.json`
- `field_guide.md`

## 7. 页面文案与边界

页面禁用表述扫描：无命中。

页面已明确显示：

- 页面不是未经核验的户外导航路线
- 坐标为现代地图辅助定位
- `book_refs` 是路线证据
- `chapter_refs` 是章节出处
- 断点、补走、乘车段不应强连 GPX

## 8. 内部标记扫描

对 `README.md`、`data`、`scripts`、`web`、`prompts`、`source` 做了内部标记扫描。

结果：无命中。

## 9. 复核包与说明书

- 人工复核包入口：`data/review_pack/index.html`
- 人工复核 checklist：`data/review_pack/manual_review_checklist.csv`
- 复走说明书：`data/field_guide.md`
- 前端同步说明书：`web/public/data/field_guide.md`

复核包状态：已生成，可本地浏览器直接打开。

## 10. 必须人工复核的问题

### 重点回看页码

30, 54, 76, 98, 100, 122, 148, 172, 192, 207, 216, 220, 240, 260, 262, 265, 280, 302, 318, 322, 324, 342, 344, 353

### 地名和 OCR

- 第54页“哈旧县”疑为 OCR 噪声，需核对旧县村。
- 第76页“达岭关城”“居肃关云台”需核对八达岭关城、居庸关云台。
- 第148页“不堡子村”需回看标题页。
- 第172页“特子庙”需核对塘子庙。
- 第240页“慢头山村”“俗石柱村”需核对馒头山村、石柱村。
- 第280页“水泉津尔”“圆图漳尔”需核对水泉淖尔、圆图淖尔。
- 第302页“河北内装专分累线”需核对河北内蒙古分界线。
- 第322页“梁河东岸沙丘”需核对滦河东岸沙丘。

### 断点、补走、乘车

最需要人工复核的段落：

- `seg-003` 居庸关到延庆
- `seg-008` 白草镇到老掌沟
- `seg-009` 老掌沟到小厂镇
- `seg-010` 小厂镇到五花草甸
- `seg-011` 五花草甸到沽源
- `seg-013` 塞北管理区到黑城子
- `seg-014` 黑城子到四郎城
- `seg-015` 四郎城到上都遗址

这些段涉及乘车、补走、断点、或现代路况核验。当前页面和 GPX 已避免把它们强连成普通连续徒步线。

## 11. 本地启动命令

开发预览：

```powershell
cd D:\WSL\Codex\web
npm run dev -- --host 127.0.0.1 --port 4287 --strictPort
```

生产构建预览：

```powershell
cd D:\WSL\Codex\web
npm run build
npm run preview -- --host 127.0.0.1 --port 4288 --strictPort
```

复核包直接打开：

```powershell
start D:\WSL\Codex\data\review_pack\index.html
```

## 12. 交付结论

当前项目达到 v0.4 本地可交付状态：

- OCR、路线抽取、证据审计、证据清理、坐标辅助、GeoJSON、GPX、复走状态、复核包、复走说明书、前端页面均已形成闭环。
- 所有核心文件存在。
- 路线数据校验通过。
- GPX 导出规则与断点状态一致。
- 前端构建通过。
- 页面已明确边界，不把项目包装成未核验的户外导航。

保留限制：人工复核尚未完成。正式对外发布前，应至少完成重点页码、地名 OCR、断点/补走/乘车上下文、以及现代路况的人工核验。
