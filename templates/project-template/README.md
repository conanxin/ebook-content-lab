# __TITLE__

Book: `__BOOK_TITLE__`

Project type: `__PROJECT_TYPE__`

Status: `draft`

This project follows the `ebook-content-lab` layout.

## Directories

- `private/source/`: source ebook files, such as `book.pdf`. Do not publish this directory.
- `private/ocr/`: OCR PDF and OCR engine intermediates. Do not publish this directory.
- `working/`: draft extraction, audit intermediates, and temporary structured data.
- `public/`: public artifacts that can be copied to `web/public/projects/__SLUG__/`.
- `reports/`: OCR, audit, validation, review, and acceptance reports.
- `review_pack/`: local manual review entrypoints and checklists.

## Suggested Flow

1. Put the source ebook at `private/source/book.pdf`.
2. Run OCR and text extraction into `private/` or compatibility `data/` paths.
3. Clean and chunk the OCR text.
4. Extract structured content for this project type.
5. Audit every claim against book evidence.
6. Generate public data into `public/`.
7. Sync safe public files to `web/public/projects/__SLUG__/`.
8. Keep source PDFs, OCR PDFs, scan images, and private review material out of `web/public`.
