# Manual Review Dashboard v0.7-A4

- Project: `second-reading-guide`
- Status: `draft`
- Total tasks: `95`

## Priority Counts

| priority | count |
|---|---:|
| `P0` | 10 |
| `P1` | 81 |
| `P2` | 4 |

## Category Counts

| category | count |
|---|---:|
| `book_overview` | 1 |
| `chapter_card` | 25 |
| `chapter_card_sample` | 5 |
| `concept_grouping_refinement` | 1 |
| `future_quote_replacement` | 1 |
| `key_concept` | 5 |
| `public_boundary` | 1 |
| `question_quality_enhancement` | 1 |
| `quote_policy` | 1 |
| `quote_structural_entry` | 25 |
| `reading_question` | 26 |
| `schema_status` | 1 |
| `web_mirror` | 1 |
| `wording_polish` | 1 |

## P0 Tasks

| task_id | category | target | question |
|---|---|---|---|
| `p0-public-boundary-001` | `public_boundary` | Public reading-guide files | Confirm public files contain no private paths, no source text, and no long excerpts. |
| `p0-book-overview-001` | `book_overview` | Book overview | Confirm the overview accurately describes the draft as structural and conservative. |
| `p0-quote-policy-001` | `quote_policy` | Quote index policy | Confirm quote entries use structural_no_quote and do not publish source quotations. |
| `p0-schema-status-001` | `schema_status` | Schema and status | Confirm schema_version is reading-guide.v0.2 and status remains draft. |
| `p0-web-mirror-001` | `web_mirror` | Web public mirror | Confirm web mirror JSON files match project public JSON files. |
| `p0-chapter-sample-001` | `chapter_card_sample` | 第1封 3月17日~18日 娘子关→骊山→西安 | Spot-check that this chapter card is derived only from structural metadata. |
| `p0-chapter-sample-007` | `chapter_card_sample` | 第7封 4月2日~3日 贵阳流山→桂林伏波山/七星山/象鼻山/漓江 | Spot-check that this chapter card is derived only from structural metadata. |
| `p0-chapter-sample-013` | `chapter_card_sample` | 第13封 4月13日~14日 汕头看海 | Spot-check that this chapter card is derived only from structural metadata. |
| `p0-chapter-sample-019` | `chapter_card_sample` | 第19封 4月28日~5月2日 千古如斯的余杭 | Spot-check that this chapter card is derived only from structural metadata. |
| `p0-chapter-sample-025` | `chapter_card_sample` | 第25封 5月18日~23日 沪青海航→青岛崂山→返京 | Spot-check that this chapter card is derived only from structural metadata. |

## Notes

- The CSV file is the single source of truth for manual review.
- `manual_result` is intentionally blank for all generated tasks.
- A4 creates review tasks only and does not promote project status.
