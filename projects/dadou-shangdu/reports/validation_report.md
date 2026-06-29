# 路线校验报告

- Generated at: 2026-06-29T10:42:56
- Input: `data\route_segments.json`
- Segments: 15
- Errors: 0
- Warnings: 0
- Info: 15

## Errors

- None

## Warnings

- None

## Info

- seg-003: movement_type=mixed，GPX 应避免把非连续/乘车/补走信息强连。
- seg-003: do_not_connect_in_gpx=true，export_gpx.py 应只导出 waypoint，不导出连续 track。
- seg-008: movement_type=mixed，GPX 应避免把非连续/乘车/补走信息强连。
- seg-008: do_not_connect_in_gpx=true，export_gpx.py 应只导出 waypoint，不导出连续 track。
- seg-009: movement_type=mixed，GPX 应避免把非连续/乘车/补走信息强连。
- seg-010: movement_type=mixed，GPX 应避免把非连续/乘车/补走信息强连。
- seg-010: do_not_connect_in_gpx=true，export_gpx.py 应只导出 waypoint，不导出连续 track。
- seg-011: movement_type=mixed，GPX 应避免把非连续/乘车/补走信息强连。
- seg-011: do_not_connect_in_gpx=true，export_gpx.py 应只导出 waypoint，不导出连续 track。
- seg-013: movement_type=mixed，GPX 应避免把非连续/乘车/补走信息强连。
- seg-013: do_not_connect_in_gpx=true，export_gpx.py 应只导出 waypoint，不导出连续 track。
- seg-014: movement_type=mixed，GPX 应避免把非连续/乘车/补走信息强连。
- seg-014: do_not_connect_in_gpx=true，export_gpx.py 应只导出 waypoint，不导出连续 track。
- seg-015: movement_type=mixed，GPX 应避免把非连续/乘车/补走信息强连。
- seg-015: do_not_connect_in_gpx=true，export_gpx.py 应只导出 waypoint，不导出连续 track。

## Continuity Field Counts

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

## GPX Connection Rules

- do_not_connect_in_gpx=true segments: seg-003, seg-008, seg-010, seg-011, seg-013, seg-014, seg-015
- Validation expectation: export_gpx.py must not emit continuous track segments for these IDs.
