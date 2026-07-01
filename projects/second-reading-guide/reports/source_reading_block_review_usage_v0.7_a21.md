# Source Reading Block Review Usage v0.7-A21

## Open The Workbench

Start with `source_reading_block_workbench_v0.7_a21.md`. It groups the current public reading blocks by the 25 letters.

## Fill The Decisions Template

Use `source_reading_block_decisions_template_v0.7_a21.csv` as the manual working file. Do not edit the generated task CSV unless regenerating A21.

## Review Result Values

- `keep`: the block can remain as is.
- `replace`: choose a better block later.
- `shorten`: keep the idea but reduce length.
- `expand`: add context around the block later.
- `move_to_extra`: move a core block into the folded area.
- `move_to_core`: promote an extra block into the default view.
- `needs_context`: keep or replace only after more context is reviewed.
- `rewrite_note`: keep the block but improve the guide note.
- `remove`: remove the block from public display in a later apply phase.
- `defer`: postpone the decision.

## Replacement Strategy Values

`use_adjacent_paragraph`, `use_more_specific_scene`, `use_route_movement`, `use_place_description`, `use_reflection`, `manual_pick`, `not_needed`.

## Notes Required

Write `review_notes` for `replace`, `shorten`, `expand`, `move_to_extra`, `move_to_core`, `needs_context`, `rewrite_note`, `remove`, or `defer`.

## Why Not Auto-Keep Everything

A20 generated useful longer blocks, but only human reading can decide whether each block is representative, complete, and placed correctly.

## After Filling Decisions

A22 should add a dry-run importer that checks the completed decisions file, reports would-change counts, and only applies updates with an explicit confirmation phrase.
