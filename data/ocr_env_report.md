# OCR 环境检测报告

- Generated at: 2026-06-29T07:35:57
- System: Windows 10
- Machine: AMD64

## Command Checks

| Item | Available | Path | Version |
| --- | --- | --- | --- |
| python | True | `C:\Users\haili\AppData\Local\Programs\Python\Python312\python.exe` | 3.12.10 (tags/v3.12.10:0cc8128, Apr  8 2025, 12:21:36) [MSC v.1943 64 bit (AMD64)] |
| tesseract | False | `` |  |
| ocrmypdf | True | `C:\Users\haili\AppData\Local\Programs\Python\Python312\Scripts\ocrmypdf.EXE` | 17.7.1 |
| qpdf | False | `` |  |
| ghostscript_gswin64c | False | `` |  |
| ghostscript_gs | False | `` |  |
| pdftoppm | False | `` |  |
| pdfinfo | False | `` |  |

## Tesseract Languages

- `chi_sim` available: False
- Languages: none detected

## Python Modules

| Module | Available |
| --- | --- |
| fitz | True |
| pymupdf4llm | True |
| pytesseract | True |
| PIL | True |
| ocrmypdf | True |

## Missing Or Needs Attention

- tesseract
- PDF command-line tools such as poppler/qpdf

## Minimal Install Command

```powershell
winget install UB-Mannheim.TesseractOCR
winget install ArtifexSoftware.Ghostscript
winget install qpdf.qpdf
winget install oschwartz10612.Poppler
python -m pip install -r requirements.txt
```

## Raw Language Probe

```
tesseract not found
```
