# Source Reading Block Decisions Import Usage v0.7-A22

## Copy The Template

Copy the A21 decisions template to a new working file before manual editing. Keep the generated template unchanged as the blank baseline.

## Fill Review Results

Use one of: `keep`, `replace`, `shorten`, `expand`, `move_to_extra`, `move_to_core`, `needs_context`, `rewrite_note`, `remove`, `defer`.

## Fill Replacement Strategy

Use blank or one of: `use_adjacent_paragraph`, `use_more_specific_scene`, `use_route_movement`, `use_place_description`, `use_reflection`, `manual_pick`, `not_needed`.

## Notes Required

`replace`, `shorten`, `expand`, `needs_context`, `rewrite_note`, `remove`, and `defer` must include `review_notes`. For `replace`, choose a replacement strategy other than `not_needed`.

## Why Empty Is Not Keep

A blank decision means not reviewed. The importer never treats blank cells as approval.

## Dry-Run Import

`python scripts/import_source_reading_block_decisions.py --project projects/second-reading-guide --version v0.7-A22 --decisions-csv <filled-decisions.csv> --dry-run`

## Apply Import

Apply mode is for a later phase. It requires `--apply` plus `--confirm-import "IMPORT SOURCE READING BLOCK DECISIONS INTO second-reading-guide"`.

## Checks After Import

Run the A22 checker, the A21 workbench checker, source reading block checks, public reading-guide checks, promotion dry-run, and web build.

## Next Phase

A23 can turn validated decisions into a controlled apply or rewrite workflow.
