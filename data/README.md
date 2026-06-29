# 路线数据字段说明

`route_segments.json` 是最终路线数据，每个对象代表书中可追溯的一段路线。

主要字段：

- `id`：段落 ID，例如 `seg-001`。
- `order`：路线顺序，必须连续。
- `chapter`：章节或书中上下文；未知为 `null`。
- `title`：段落标题。
- `start` / `end`：起终点对象，包含 `name`、`lat`、`lng`、`coordinate_source`、`coordinate_confidence`。
- `via`：途经点数组，结构同地点对象。
- `distance_km_book`：书中明示里程；未明示为 `null`。
- `distance_km_computed`：按已补坐标粗略计算的直线或折线距离；缺坐标为 `null`。
- `route_summary`：只依据书中内容的路线概括。
- `walking_directions`：书中可抽取的方向或行走说明。
- `terrain`、`roads_or_paths`、`water_sources`、`resupply`、`lodging`、`risks_or_notes`：书中明示信息；未明示填 `null` 或 `书中未明示`。
- `book_refs`：书中出处数组。每项必须包含 `page`、`quote`、`note`。`quote` 只放短摘。
- `confidence`：路线抽取置信度，可用 `verified`、`approximate`、`needs_review`。
- `review_notes`：需要人工复核的问题。

坐标置信度：

- `verified`：位置较明确，坐标只作现代辅助定位。
- `approximate`：只能定位到大致区域或存在历史/现代地名差异。
- `missing`：无法可靠补坐标。

重要边界：坐标不能改变书中路线顺序，也不能替代书中证据。
