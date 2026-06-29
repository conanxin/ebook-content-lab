# seg-009 状态一致性专项审查

- 审查对象：`seg-009 老掌沟到小厂镇`
- 审查范围：只读取现有路线数据和报告，不修改数据、不重新生成 GPX、不改页面
- 结论：seg-009 当前状态基本自洽；不建议把 `do_not_connect_in_gpx` 改为 `true`

## 1. 当前字段

| 字段 | 当前值 | 审查说明 |
|---|---|---|
| `movement_type` | `mixed` | 准确。书中和当前数据都显示本段包含“下车 / 补走前一日未完成路段”的上下文。 |
| `continuity_status` | `gap_before` | 准确。断点发生在本段之前：前一日未走完，次日回到相关位置补走。 |
| `walkability_status` | `book_walkable` | 可解释。虽然本段不是纯粹连续的 walked 段，但当前 GPX 表达的是书中可支持的补走和随后步行部分，因此这部分可以按书中徒步描述理解。 |
| `modern_followability` | `approximate_only` | 合理。该段坐标用于大致定位，不代表现代路况已核验。 |
| `do_not_connect_in_gpx` | `false` | 合理。它不表示“完全没有补走/断点”，而是表示当前导出的这段 GPX track 不包含接送车路线，且可表达为一个独立连续步行参考段。 |
| `gap_notes` | “本段包含补走前一日未完成路段；接送车路线不得计入步行路线。”；“本段 GPX 只表达书中可支持的补走和随后步行部分。” | 说明已经把补走和 GPX 边界说清楚。 |

## 2. 证据与出处

### book_refs

seg-009 有 10 条 `book_refs`，包括：

- 第218页：“首先要补上昨天没有走完的一段”
- 第220页：“我们开始补走这一段到处都是牛群的风景区”
- 第220页：“本来只有五公里长的沟谷，我们实际走了差不多十公里”
- 第221页：“从沟门往北走十多分钟，就到了燕山山脉北支的分水岭”
- 第224页：“X404的路东先后是前坝村和后坝村”
- 第228页：“下午四点一刻，我们走到X404与S245交叉的地方，终于到小厂镇了”

这些引用能支持两件事：

- 本段包含补走上下文。
- 补走开始后到小厂镇这一部分，有书中步行方向和到达证据。

### chapter_refs

- 第216页：“从老掌沟到小厂镇”

该引用只是章节或段落标题来源，不应当作路线事实证据。

## 3. route_walkable_blocks / GPX 状态

- seg-009 属于 `route_walkable_blocks`：`walk-block-007`
- `walk-block-007` 起点：老掌沟
- `walk-block-007` 终点：小厂镇
- block 状态：`partial`
- seg-009 进入 GPX track：是
- seg-009 只导出 waypoint：否
- `gpx_export_report.md` 的“因路线断点未导出连续 track”列表不包含 seg-009

这说明当前项目把 seg-009 处理为：

> 有补走/断点背景，但当前可导出的 GPX track 只表达书中可支持的补走和随后步行部分，不把接送车路线画进去。

## 4. 是否存在断点、补走、乘车或路线不连续

seg-009 存在“补走”和“gap_before”。

但这里的断点性质与 `do_not_connect_in_gpx=true` 的 7 段不同：

- `seg-003`、`seg-008`、`seg-010`、`seg-011`、`seg-013`、`seg-014`、`seg-015` 是段内或段落连接处存在乘车、接应、补走起点回送、或不能完整画成连续步行线的问题，因此只导出 waypoint。
- `seg-009` 的问题是本段开始前存在补走上下文；当前数据已经把接送车路线排除，只把书中支持的补走和随后步行部分作为一个独立 track。因此它可以是 `movement_type=mixed`，同时 `do_not_connect_in_gpx=false`。

## 5. 最终验收报告中的表述是否准确

`final_acceptance_report.md` 中“断点/补走/乘车”列表把 seg-009 放入“最需要人工复核的段落”，从“需要复核补走上下文”的角度是准确的。

但如果读者把这个标题理解为“这些段都应当 `do_not_connect_in_gpx=true` 或只导出 waypoint”，则会产生歧义。

因此，不建议修改路线数据；建议修改报告措辞。

## 6. 建议修正方案

### 不建议修改

- 不建议修改 `data/route_segments.json`
- 不建议修改 `do_not_connect_in_gpx`
- 不建议重新生成 `route.gpx`
- 不建议修改 `gpx_export_report.md`
- 不建议修改 `route_continuity_report.md`
- 不建议修改页面逻辑

理由：当前数据模型已经表达了 seg-009 的特殊性：

- `movement_type=mixed`
- `continuity_status=gap_before`
- `walkability_status=book_walkable`
- `do_not_connect_in_gpx=false`
- `gap_notes` 明确说明接送车路线不得计入，GPX 只表达书中支持的补走和随后步行部分
- route_status_matrix 和 field_guide 已对这个差异作出解释

### 建议修改

建议只修改 `data/final_acceptance_report.md` 的措辞，把“断点/补走/乘车”分成两类：

1. **不应连接 GPX / 只导出 waypoint 的段落**
   - `seg-003`
   - `seg-008`
   - `seg-010`
   - `seg-011`
   - `seg-013`
   - `seg-014`
   - `seg-015`

2. **存在补走上下文但仍进入独立 GPX track 的段落**
   - `seg-009`
   - 说明：该段是 `mixed`、`gap_before`，但 `do_not_connect_in_gpx=false`；当前 GPX 只表达书中可支持的补走和随后步行部分，不连接接送车路线。

如需进一步消除歧义，也可以在页面文案中保留现状，不必改逻辑；页面已经显示 `movement_type=mixed`、`gap_before`、`gap_notes`、以及是否进入 GPX track。

## 7. 最终判断

- seg-009 当前状态自洽：是
- 是否需要修改 `do_not_connect_in_gpx`：否
- 是否需要修改报告中的“断点/补走/乘车段”表述：建议修改，尤其是 `final_acceptance_report.md` 的分组标题和说明

