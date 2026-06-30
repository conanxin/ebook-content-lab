# Manual Review Completion Usage v0.7-A6

## Purpose

Use `scripts/update_manual_review_result.py` to record human review results for one task at a time.

The script is conservative by default: without `--apply`, it performs a dry-run and does not change the CSV.

## Dry-Run One Task

```bash
python scripts/update_manual_review_result.py \
  --project projects/second-reading-guide \
  --task-id p0-public-boundary-001 \
  --result pass \
  --notes "Dry-run only; no CSV change." \
  --reviewer "your-name" \
  --dry-run
```

## Apply One Task

```bash
python scripts/update_manual_review_result.py \
  --project projects/second-reading-guide \
  --task-id p0-public-boundary-001 \
  --result pass \
  --notes "Reviewed against public boundary rules." \
  --reviewer "your-name" \
  --apply \
  --confirm-update "UPDATE MANUAL REVIEW TASK p0-public-boundary-001"
```

## Legal Result Values

- `pass`
- `needs_fix`
- `blocked`
- `deferred`

`deferred`, `needs_fix`, and `blocked` require notes.

## Why No Batch Auto-Pass

Manual review is a human judgment step. The helper is intentionally task-based so every result remains auditable.

Do not batch-fill all results as `pass`.

## Checks After Updating

After any real update, run:

```bash
python scripts/check_manual_review_progress.py --project projects/second-reading-guide --version v0.7-A6
python scripts/check_manual_review_tasks.py --project projects/second-reading-guide --version v0.7-A4
python scripts/promote_status.py --project projects/second-reading-guide --version v0.7-A5 --target-status reviewed-draft --dry-run
python scripts/check_promote_status.py --project projects/second-reading-guide --version v0.7-A5
```

Only rerun promotion with apply mode after all required manual review tasks are complete and the preflight reports readiness.
