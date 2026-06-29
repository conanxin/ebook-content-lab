# Public Release Report

Status: **pass**

## Summary

- Projects in web/public/projects/index.json: 2
- Errors: 0
- Warnings: 0

## Errors

- None

## Warnings

- None

## Checks

- Private source and OCR filenames are absent from public directories.
- Project private directories are expected to be ignored by `.gitignore`.
- `web/public/projects/index.json` is readable.
- Public project `project.json` files exist.
- `public_files` entries resolve in `web/public/projects/<slug>/`.
- Route evidence quotes are checked for length warnings.
- Public-facing text is checked for internal markers and high-risk navigation claims.
