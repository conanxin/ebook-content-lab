# Public Preview Feedback Fix Report v0.7-A10

## Summary

- Project: `second-reading-guide`
- Page URL: `https://conanxin.github.io/ebook-content-lab/#/projects/second-reading-guide`
- New page title: `《旅行人信札》阅读导览`
- Subtitle: `25 封旅行书信的路线、地点与主题导读`
- Public status: `draft`
- Release phase: `public-preview`
- Review status: `manual-review-pending`

## Changes

### Page and UI

- Reworked the reading-guide page from a technical module view into a reader-facing public preview.
- Added a correspondence / envelope card layout for the 25 chapter cards.
- Added date stamps, route labels, envelope flaps, expandable reading clues, and answer blocks.
- Moved technical version information into a bottom details section.

### Public Data

- Updated project metadata and project index display name.
- Updated 5 public JSON files and matching web mirror files.
- Added guide fields to all 25 chapter cards:
  - `letter_summary`
  - `route_note`
  - `reading_focus`
  - `theme_note`
  - `review_notice`
- Added `answer_hint` to all 26 reading questions.
- Reworded quote-index presentation as “暂不公开原文摘录”.

## Coverage

- Chapter cards: 25
- Chapter cards with guide fields: 25
- Reading questions: 26
- Reading questions with answer hints: 26
- Key concepts: 5

## Boundary

- No manual review result was filled.
- No status promotion was applied.
- No source-layer files or long excerpts were published.
- `dadou-shangdu` was not changed.

## Validation

- A10 feedback-fix validation: pass
- A9 public-preview validation: pass
- Reading-guide public validation: pass
- Manual review progress validation: pass
- Promotion preflight: blocked as expected
- Public release check: pass
- Local web build: pass

Validation details are recorded in `public_preview_feedback_fix_validation_v0.7_a10.md`.
