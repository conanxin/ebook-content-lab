# 第二本电子书阅读导读

Book: `待定书名`

Project type: `reading-guide`

Status: `draft`

This project was created from `templates/project-template/`.

## Directories

- `private/source/`: source ebook files, such as `book.pdf`. Do not publish this directory.
- `private/ocr/`: OCR PDF and OCR engine intermediates. Do not publish this directory.
- `working/`: draft extraction, audit intermediates, and temporary structured data.
- `public/`: public artifacts that can be copied to `web/public/projects/second-reading-guide/`.
- `reports/`: OCR, audit, validation, review, and acceptance reports.
- `review_pack/`: local manual review entrypoints and checklists.

## Next Steps

1. Put the source ebook at `projects/second-reading-guide/private/source/book.pdf`.
2. Run OCR and text extraction.
3. Clean and chunk the OCR text.
4. Extract structured content for `reading-guide`.
5. Audit every claim against book evidence.
6. Generate public artifacts under `projects/second-reading-guide/public/`.
7. Sync safe public files to `web/public/projects/second-reading-guide/`.
8. Keep source PDFs, OCR PDFs, scan images, and private review material out of `web/public`.
