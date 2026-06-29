# Reading Guide Validation Report

Project: `projects/second-reading-guide`
Status: **pass**
Project status: `draft`

## Required Public Files

- `book_overview.json`: ok, data status `draft`
- `chapter_reading_cards.json`: ok, data status `draft`
- `key_concepts.json`: ok, data status `draft`
- `quote_index.json`: ok, data status `draft`
- `reading_questions.json`: ok, data status `draft`

## Summary

- Errors: 0
- Warnings: 0

## Errors

- None

## Warnings

- None

## Rules

- `project.json` must exist and declare `project_type: reading-guide`.
- Draft projects may keep content arrays empty.
- Non-draft projects must include chapter cards with evidence references.
- Evidence quotes should be short and no longer than 120 characters.
