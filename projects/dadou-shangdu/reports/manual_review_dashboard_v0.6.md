# v0.6 人工复核总控面板

本面板用于组织《从大都到上都》路线数据的人工复核。本轮只生成报告和清单，不修改路线数据、坐标、书中出处或线上 URL。

## 任务统计

| priority | count |
| --- | ---: |
| P0 | 31 |
| P1 | 45 |
| P2 | 1 |

| category | count |
| --- | ---: |
| OCR 地名复核 | 8 |
| 路线连续性复核 | 8 |
| GPX 连接规则复核 | 9 |
| 坐标复核 | 15 |
| 书中证据复核 | 33 |
| 页面表述复核 | 4 |

## 最优先人工复核的 10 条

1. **P0 OCR 地名复核** - seg-002 p54 `旧县村`: 请回看 PDF 原书扫描页，确认该地名的正确写法、上下文和是否属于路线事实。
2. **P0 OCR 地名复核** - seg-003 p76;88 `八达岭 / 居庸关`: 请回看 PDF 原书扫描页，确认该地名的正确写法、上下文和是否属于路线事实。
3. **P0 OCR 地名复核** - seg-006 p148;150 `不堡子村`: 请回看 PDF 原书扫描页，确认该地名的正确写法、上下文和是否属于路线事实。
4. **P0 OCR 地名复核** - seg-007 p172;174;191 `塘子庙`: 请回看 PDF 原书扫描页，确认该地名的正确写法、上下文和是否属于路线事实。
5. **P0 OCR 地名复核** - seg-010 p240;242;251 `馒头山村 / 石柱村`: 请回看 PDF 原书扫描页，确认该地名的正确写法、上下文和是否属于路线事实。
6. **P0 OCR 地名复核** - seg-012 p280;286 `水泉淖尔 / 圆图淖尔`: 请回看 PDF 原书扫描页，确认该地名的正确写法、上下文和是否属于路线事实。
7. **P0 OCR 地名复核** - seg-013 p302;313 `河北内蒙古分界线`: 请回看 PDF 原书扫描页，确认该地名的正确写法、上下文和是否属于路线事实。
8. **P0 OCR 地名复核** - seg-014 p322;324 `滦河东岸沙丘`: 请回看 PDF 原书扫描页，确认该地名的正确写法、上下文和是否属于路线事实。
9. **P0 路线连续性复核** - seg-003 p76;88;96;98 `movement_type / continuity_status / gap_notes`: 请核对 book_refs 和原图，确认当前 movement_type / continuity_status / gap_notes 判断是否被书中文字支持。
10. **P0 路线连续性复核** - seg-008 p192;194;205;207 `movement_type / continuity_status / gap_notes`: 请核对 book_refs 和原图，确认当前 movement_type / continuity_status / gap_notes 判断是否被书中文字支持。

## 六类复核任务

- **OCR 地名复核**: 8
- **路线连续性复核**: 8
- **GPX 连接规则复核**: 9
- **坐标复核**: 15
- **书中证据复核**: 33
- **页面表述复核**: 4

## 路线状态上下文

- 路线段数: 15
- 连续徒步块: 8
- do_not_connect_in_gpx=true: seg-003, seg-008, seg-010, seg-011, seg-013, seg-014, seg-015
- waypoint-only: seg-003, seg-008, seg-010, seg-011, seg-013, seg-014, seg-015
- GPX track segments: seg-001, seg-002, seg-004, seg-005, seg-006, seg-007, seg-009, seg-012
- needs_field_check: seg-003, seg-008, seg-010, seg-011, seg-013, seg-014, seg-015
- 旧复核包 checklist 行数: 380
- data/manual_review_tasks_v0.5.csv: 未找到

## 使用方式

1. 打开 `manual_review_tasks_v0.6.csv`，按 P0 -> P1 -> P2 顺序复核。
2. 在 `manual_result` 填写人工结论，在 `notes` 补充页码、原文短摘或判断依据。
3. 复核本身不直接修改路线数据；需改数据时，另起修正任务并保留书中证据。
4. 不要用现代地图反推书中路线；坐标只能作为辅助定位。

## 输出文件

- `projects/dadou-shangdu/reports/manual_review_tasks_v0.6.csv`
- `projects/dadou-shangdu/reports/manual_review_summary_v0.6.json`
- `projects/dadou-shangdu/reports/manual_review_dashboard_v0.6.md`
