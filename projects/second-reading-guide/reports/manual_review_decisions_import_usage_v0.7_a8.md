# Manual Review Decisions Import Usage v0.7-A8

## Prepare A Human-Filled File

Copy the A7 template before editing:

```bash
cp projects/second-reading-guide/reports/manual_review_decisions_template_v0.7_a7.csv \
  projects/second-reading-guide/reports/manual_review_decisions_human.csv
```

Fill only the human decision columns:

- `manual_result`
- `notes`
- `reviewer`
- `reviewed_at`

Do not edit `task_id`.

## Legal Results

Allowed values:

- `pass`
- `needs_fix`
- `blocked`
- `deferred`

Blank values are not pass. They are treated as not reviewed.

`needs_fix`, `blocked`, and `deferred` must include notes.

## Dry-Run Import

```bash
python scripts/import_manual_review_decisions.py \
  --project projects/second-reading-guide \
  --version v0.7-A8 \
  --decisions-csv projects/second-reading-guide/reports/manual_review_decisions_human.csv \
  --dry-run
```

Review the generated dry-run report before applying.

## Apply Import

```bash
python scripts/import_manual_review_decisions.py \
  --project projects/second-reading-guide \
  --version v0.7-A8 \
  --decisions-csv projects/second-reading-guide/reports/manual_review_decisions_human.csv \
  --apply \
  --confirm-import "IMPORT MANUAL REVIEW DECISIONS INTO second-reading-guide"
```

## Checks After Import

Run:

```bash
python scripts/check_manual_review_decisions_import.py --project projects/second-reading-guide --version v0.7-A8
python scripts/check_manual_review_progress.py --project projects/second-reading-guide --version v0.7-A6
python scripts/promote_status.py --project projects/second-reading-guide --version v0.7-A5 --target-status reviewed-draft --dry-run
python scripts/check_promote_status.py --project projects/second-reading-guide --version v0.7-A5
```

Promotion preflight should be rerun only after the import passes and the review status is complete.
