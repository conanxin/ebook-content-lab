# Manual Review P0 Packet v0.7-A7

- Project: `second-reading-guide`
- P0 tasks: `10`
- This packet contains priority tasks only.
- It does not contain source text or private paths.

### p0-public-boundary-001

- priority: `P0`
- category: `public_boundary`
- target_id: `public-layer`
- target_title: `Public reading-guide files`
- source_file: `projects/second-reading-guide/public/*.json`
- current manual_result: `blank`
- review question: Confirm public files contain no private paths, no source text, and no long excerpts.

Structured context:

- structural context: `see source_file`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

Apply command template:

```bash
python scripts/update_manual_review_result.py --project projects/second-reading-guide --task-id p0-public-boundary-001 --result pass --notes "Reviewed manually." --reviewer "your-name" --apply --confirm-update "UPDATE MANUAL REVIEW TASK p0-public-boundary-001"
```

### p0-book-overview-001

- priority: `P0`
- category: `book_overview`
- target_id: `book_overview`
- target_title: `Book overview`
- source_file: `projects/second-reading-guide/public/book_overview.json`
- current manual_result: `blank`
- review question: Confirm the overview accurately describes the draft as structural and conservative.

Structured context:

- schema_version: `reading-guide.v0.2`
- status: `draft`
- body_letter_count: `25`
- source_mode: `metadata_and_letters_brief`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

Apply command template:

```bash
python scripts/update_manual_review_result.py --project projects/second-reading-guide --task-id p0-book-overview-001 --result pass --notes "Reviewed manually." --reviewer "your-name" --apply --confirm-update "UPDATE MANUAL REVIEW TASK p0-book-overview-001"
```

### p0-quote-policy-001

- priority: `P0`
- category: `quote_policy`
- target_id: `quote_index`
- target_title: `Quote index policy`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm quote entries use structural_no_quote and do not publish source quotations.

Structured context:

- quote_mode: `structural_no_quote`
- entries: `25`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

Apply command template:

```bash
python scripts/update_manual_review_result.py --project projects/second-reading-guide --task-id p0-quote-policy-001 --result pass --notes "Reviewed manually." --reviewer "your-name" --apply --confirm-update "UPDATE MANUAL REVIEW TASK p0-quote-policy-001"
```

### p0-schema-status-001

- priority: `P0`
- category: `schema_status`
- target_id: `reading-guide.v0.2`
- target_title: `Schema and status`
- source_file: `projects/second-reading-guide/public/*.json`
- current manual_result: `blank`
- review question: Confirm schema_version is reading-guide.v0.2 and status remains draft.

Structured context:

- schemas: `reading-guide.v0.2`
- statuses: `draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

Apply command template:

```bash
python scripts/update_manual_review_result.py --project projects/second-reading-guide --task-id p0-schema-status-001 --result pass --notes "Reviewed manually." --reviewer "your-name" --apply --confirm-update "UPDATE MANUAL REVIEW TASK p0-schema-status-001"
```

### p0-web-mirror-001

- priority: `P0`
- category: `web_mirror`
- target_id: `web-public-mirror`
- target_title: `Web public mirror`
- source_file: `web/public/projects/second-reading-guide/*.json`
- current manual_result: `blank`
- review question: Confirm web mirror JSON files match project public JSON files.

Structured context:

- structural context: `see source_file`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

Apply command template:

```bash
python scripts/update_manual_review_result.py --project projects/second-reading-guide --task-id p0-web-mirror-001 --result pass --notes "Reviewed manually." --reviewer "your-name" --apply --confirm-update "UPDATE MANUAL REVIEW TASK p0-web-mirror-001"
```

### p0-chapter-sample-001

- priority: `P0`
- category: `chapter_card_sample`
- target_id: `chapter-001`
- target_title: `第1封 3月17日~18日 娘子关→骊山→西安`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Spot-check that this chapter card is derived only from structural metadata.

Structured context:

- section_id: `sec-006`
- order: `1`
- places: `娘子关, 骊山, 西安`
- themes: `旅行书信, 山水行旅, 城市与旅途`
- chunk_count: `2`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

Apply command template:

```bash
python scripts/update_manual_review_result.py --project projects/second-reading-guide --task-id p0-chapter-sample-001 --result pass --notes "Reviewed manually." --reviewer "your-name" --apply --confirm-update "UPDATE MANUAL REVIEW TASK p0-chapter-sample-001"
```

### p0-chapter-sample-007

- priority: `P0`
- category: `chapter_card_sample`
- target_id: `chapter-007`
- target_title: `第7封 4月2日~3日 贵阳流山→桂林伏波山/七星山/象鼻山/漓江`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Spot-check that this chapter card is derived only from structural metadata.

Structured context:

- section_id: `sec-012`
- order: `7`
- places: `贵阳流山, 桂林伏波山, 七星山, 象鼻山, 漓江`
- themes: `旅行书信, 山水行旅`
- chunk_count: `3`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

Apply command template:

```bash
python scripts/update_manual_review_result.py --project projects/second-reading-guide --task-id p0-chapter-sample-007 --result pass --notes "Reviewed manually." --reviewer "your-name" --apply --confirm-update "UPDATE MANUAL REVIEW TASK p0-chapter-sample-007"
```

### p0-chapter-sample-013

- priority: `P0`
- category: `chapter_card_sample`
- target_id: `chapter-013`
- target_title: `第13封 4月13日~14日 汕头看海`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Spot-check that this chapter card is derived only from structural metadata.

Structured context:

- section_id: `sec-018`
- order: `13`
- places: `汕头看海`
- themes: `旅行书信`
- chunk_count: `4`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

Apply command template:

```bash
python scripts/update_manual_review_result.py --project projects/second-reading-guide --task-id p0-chapter-sample-013 --result pass --notes "Reviewed manually." --reviewer "your-name" --apply --confirm-update "UPDATE MANUAL REVIEW TASK p0-chapter-sample-013"
```

### p0-chapter-sample-019

- priority: `P0`
- category: `chapter_card_sample`
- target_id: `chapter-019`
- target_title: `第19封 4月28日~5月2日 千古如斯的余杭`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Spot-check that this chapter card is derived only from structural metadata.

Structured context:

- section_id: `sec-024`
- order: `19`
- places: `千古如斯的余杭`
- themes: `旅行书信, 长篇行旅记录, 多段叙述`
- chunk_count: `5`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

Apply command template:

```bash
python scripts/update_manual_review_result.py --project projects/second-reading-guide --task-id p0-chapter-sample-019 --result pass --notes "Reviewed manually." --reviewer "your-name" --apply --confirm-update "UPDATE MANUAL REVIEW TASK p0-chapter-sample-019"
```

### p0-chapter-sample-025

- priority: `P0`
- category: `chapter_card_sample`
- target_id: `chapter-025`
- target_title: `第25封 5月18日~23日 沪青海航→青岛崂山→返京`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Spot-check that this chapter card is derived only from structural metadata.

Structured context:

- section_id: `sec-030`
- order: `25`
- places: `沪青海航, 青岛崂山, 返京`
- themes: `旅行书信, 长篇行旅记录, 多段叙述, 山水行旅, 城市与旅途`
- chunk_count: `6`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

Apply command template:

```bash
python scripts/update_manual_review_result.py --project projects/second-reading-guide --task-id p0-chapter-sample-025 --result pass --notes "Reviewed manually." --reviewer "your-name" --apply --confirm-update "UPDATE MANUAL REVIEW TASK p0-chapter-sample-025"
```
