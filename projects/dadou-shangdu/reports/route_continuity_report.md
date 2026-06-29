# 路线连续性标注报告

- Generated at: 2026-06-29T09:28:41
- Input: `data\route_segments.json`
- GPX report: `data\gpx_export_report.md`
- 说明: 本次只补充复走、断点和 GPX 连接规则字段，不改路线顺序、坐标、book_refs 或 chapter_refs。

## 字段检查

- seg-001: 缺失 movement_type, continuity_status, walkability_status, modern_followability, gap_notes, do_not_connect_in_gpx
- seg-002: 缺失 movement_type, continuity_status, walkability_status, modern_followability, gap_notes, do_not_connect_in_gpx
- seg-003: 缺失 movement_type, continuity_status, walkability_status, modern_followability, gap_notes, do_not_connect_in_gpx
- seg-004: 缺失 movement_type, continuity_status, walkability_status, modern_followability, gap_notes, do_not_connect_in_gpx
- seg-005: 缺失 movement_type, continuity_status, walkability_status, modern_followability, gap_notes, do_not_connect_in_gpx
- seg-006: 缺失 movement_type, continuity_status, walkability_status, modern_followability, gap_notes, do_not_connect_in_gpx
- seg-007: 缺失 movement_type, continuity_status, walkability_status, modern_followability, gap_notes, do_not_connect_in_gpx
- seg-008: 缺失 movement_type, continuity_status, walkability_status, modern_followability, gap_notes, do_not_connect_in_gpx
- seg-009: 缺失 movement_type, continuity_status, walkability_status, modern_followability, gap_notes, do_not_connect_in_gpx
- seg-010: 缺失 movement_type, continuity_status, walkability_status, modern_followability, gap_notes, do_not_connect_in_gpx
- seg-011: 缺失 movement_type, continuity_status, walkability_status, modern_followability, gap_notes, do_not_connect_in_gpx
- seg-012: 缺失 movement_type, continuity_status, walkability_status, modern_followability, gap_notes, do_not_connect_in_gpx
- seg-013: 缺失 movement_type, continuity_status, walkability_status, modern_followability, gap_notes, do_not_connect_in_gpx
- seg-014: 缺失 movement_type, continuity_status, walkability_status, modern_followability, gap_notes, do_not_connect_in_gpx
- seg-015: 缺失 movement_type, continuity_status, walkability_status, modern_followability, gap_notes, do_not_connect_in_gpx

## 标注统计

### movement_type

- walked: 7
- vehicle: 0
- mixed: 8
- inferred: 0
- unclear: 0

### continuity_status

- continuous: 6
- gap_before: 4
- gap_after: 4
- isolated: 1
- unclear: 0

### walkability_status

- book_walkable: 8
- partially_walkable: 7
- not_walkable_as_written: 0
- needs_review: 0

### modern_followability

- likely_followable: 0
- approximate_only: 8
- not_enough_information: 0
- needs_field_check: 7

## GPX 连接规则

- do_not_connect_in_gpx=true: seg-003, seg-008, seg-010, seg-011, seg-013, seg-014, seg-015
- walkable blocks: 8
- 与当前 GPX 连续 track 数量对齐: yes

## 与现有 GPX 报告交叉检查

- seg-003: 已出现在 GPX 断点报告中
- seg-008: 已出现在 GPX 断点报告中
- seg-010: 已出现在 GPX 断点报告中
- seg-011: 已出现在 GPX 断点报告中
- seg-013: 已出现在 GPX 断点报告中
- seg-014: 已出现在 GPX 断点报告中
- seg-015: 已出现在 GPX 断点报告中

## 分段修改

### seg-001 健德门到皂甲屯

- changes: movement_type: added; continuity_status: added; walkability_status: added; modern_followability: added; gap_notes: added; do_not_connect_in_gpx: added
- movement_type: walked
- continuity_status: continuous
- walkability_status: book_walkable
- modern_followability: approximate_only
- do_not_connect_in_gpx: False
- gap_notes:
  - 书中显示第一日行走结束后另有乘车南返；本段 GPX 只表达健德门至皂甲屯的步行段，不连接乘车路线。

### seg-002 昌平到居庸关

- changes: movement_type: added; continuity_status: added; walkability_status: added; modern_followability: added; gap_notes: added; do_not_connect_in_gpx: added
- movement_type: walked
- continuity_status: continuous
- walkability_status: book_walkable
- modern_followability: approximate_only
- do_not_connect_in_gpx: False
- gap_notes:
  - 无

### seg-003 居庸关到延庆

- changes: movement_type: added; continuity_status: added; walkability_status: added; modern_followability: added; gap_notes: added; do_not_connect_in_gpx: added
- movement_type: mixed
- continuity_status: gap_after
- walkability_status: partially_walkable
- modern_followability: needs_field_check
- do_not_connect_in_gpx: True
- gap_notes:
  - 第98页及复核备注显示当天行走未连续到延庆旧县镇，后续存在乘车返回/休整信息。
  - 书中存在乘车/断点复核说明，不应与前后段强行连成连续徒步轨迹。
  - 该段只导出 waypoint，不作为连续 GPX track。

### seg-004 延庆旧县镇到白河堡水库

- changes: movement_type: added; continuity_status: added; walkability_status: added; modern_followability: added; gap_notes: added; do_not_connect_in_gpx: added
- movement_type: walked
- continuity_status: gap_before
- walkability_status: book_walkable
- modern_followability: approximate_only
- do_not_connect_in_gpx: False
- gap_notes:
  - 本段从旧县镇开始步行；与上一段之间存在已在 seg-003 标记的断点。

### seg-005 白河堡水库到长伸地村

- changes: movement_type: added; continuity_status: added; walkability_status: added; modern_followability: added; gap_notes: added; do_not_connect_in_gpx: added
- movement_type: walked
- continuity_status: continuous
- walkability_status: book_walkable
- modern_followability: approximate_only
- do_not_connect_in_gpx: False
- gap_notes:
  - 部分中途地名曾因 OCR 和标题页证据不足被移入复核说明；GPX 仅按已保留正文证据和坐标生成参考线。

### seg-006 长伸地村到龙门所镇

- changes: movement_type: added; continuity_status: added; walkability_status: added; modern_followability: added; gap_notes: added; do_not_connect_in_gpx: added
- movement_type: walked
- continuity_status: continuous
- walkability_status: book_walkable
- modern_followability: approximate_only
- do_not_connect_in_gpx: False
- gap_notes:
  - 无

### seg-007 龙门所到白草镇

- changes: movement_type: added; continuity_status: added; walkability_status: added; modern_followability: added; gap_notes: added; do_not_connect_in_gpx: added
- movement_type: walked
- continuity_status: continuous
- walkability_status: book_walkable
- modern_followability: approximate_only
- do_not_connect_in_gpx: False
- gap_notes:
  - 无

### seg-008 白草镇到老掌沟

- changes: movement_type: added; continuity_status: added; walkability_status: added; modern_followability: added; gap_notes: added; do_not_connect_in_gpx: added
- movement_type: mixed
- continuity_status: gap_after
- walkability_status: partially_walkable
- modern_followability: needs_field_check
- do_not_connect_in_gpx: True
- gap_notes:
  - 第207页及复核备注显示进入老掌沟后联系车辆接应，步行终点与住宿点之间存在非步行接续。
  - 书中存在乘车/补走信息，不应与前后段强行连成连续徒步轨迹。
  - 该段只导出 waypoint，不作为连续 GPX track。

### seg-009 老掌沟到小厂镇

- changes: movement_type: added; continuity_status: added; walkability_status: added; modern_followability: added; gap_notes: added; do_not_connect_in_gpx: added
- movement_type: mixed
- continuity_status: gap_before
- walkability_status: book_walkable
- modern_followability: approximate_only
- do_not_connect_in_gpx: False
- gap_notes:
  - 本段包含补走前一日未完成路段；接送车路线不得计入步行路线。
  - 本段 GPX 只表达书中可支持的补走和随后步行部分。

### seg-010 小厂镇到五花草甸

- changes: movement_type: added; continuity_status: added; walkability_status: added; modern_followability: added; gap_notes: added; do_not_connect_in_gpx: added
- movement_type: mixed
- continuity_status: gap_after
- walkability_status: partially_walkable
- modern_followability: needs_field_check
- do_not_connect_in_gpx: True
- gap_notes:
  - 第260页及复核备注显示近五花草甸后搭车离开，不能画成完整步行到沽源。
  - 书中存在乘车/断点信息，不应与前后段强行连成连续徒步轨迹。
  - 该段只导出 waypoint，不作为连续 GPX track。

### seg-011 五花草甸到沽源

- changes: movement_type: added; continuity_status: added; walkability_status: added; modern_followability: added; gap_notes: added; do_not_connect_in_gpx: added
- movement_type: mixed
- continuity_status: gap_before
- walkability_status: partially_walkable
- modern_followability: needs_field_check
- do_not_connect_in_gpx: True
- gap_notes:
  - 第265页及复核备注显示本段先乘出租车到梳妆楼和五花草甸，再补走五花草甸至沽源。
  - 书中存在乘车/补走信息，不应与前后段强行连成连续徒步轨迹。
  - 该段只导出 waypoint，不作为连续 GPX track。

### seg-012 沽源到塞北管理区

- changes: movement_type: added; continuity_status: added; walkability_status: added; modern_followability: added; gap_notes: added; do_not_connect_in_gpx: added
- movement_type: walked
- continuity_status: continuous
- walkability_status: book_walkable
- modern_followability: approximate_only
- do_not_connect_in_gpx: False
- gap_notes:
  - 无

### seg-013 塞北管理区到黑城子

- changes: movement_type: added; continuity_status: added; walkability_status: added; modern_followability: added; gap_notes: added; do_not_connect_in_gpx: added
- movement_type: mixed
- continuity_status: gap_after
- walkability_status: partially_walkable
- modern_followability: needs_field_check
- do_not_connect_in_gpx: True
- gap_notes:
  - 第318页及复核备注显示黑城子到正蓝旗存在车辆接续，需避免画成步行路线。
  - 书中存在乘车/断点信息，不应与前后段强行连成连续徒步轨迹。
  - 该段只导出 waypoint，不作为连续 GPX track。

### seg-014 黑城子到四郎城

- changes: movement_type: added; continuity_status: added; walkability_status: added; modern_followability: added; gap_notes: added; do_not_connect_in_gpx: added
- movement_type: mixed
- continuity_status: isolated
- walkability_status: partially_walkable
- modern_followability: needs_field_check
- do_not_connect_in_gpx: True
- gap_notes:
  - 第324页及复核备注显示本段先坐出租车到补走点，路线连续性需人工确认。
  - 书中存在乘车/补走信息，不应与前后段强行连成连续徒步轨迹。
  - 该段只导出 waypoint，不作为连续 GPX track。

### seg-015 四郎城到上都遗址

- changes: movement_type: added; continuity_status: added; walkability_status: added; modern_followability: added; gap_notes: added; do_not_connect_in_gpx: added
- movement_type: mixed
- continuity_status: gap_before
- walkability_status: partially_walkable
- modern_followability: needs_field_check
- do_not_connect_in_gpx: True
- gap_notes:
  - 第344页及复核备注显示坐车过上都音高勒大桥后，从桥北开始最后一日步行。
  - 书中存在乘车/断点信息，不应与前后段强行连成连续徒步轨迹。
  - 该段只导出 waypoint，不作为连续 GPX track。

