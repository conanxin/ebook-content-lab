from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import shutil
import subprocess
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAPIDOCR_ENGINE = None
RAPIDOCR_DOC = None
RAPIDOCR_ZOOM = 1.6


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def needs_review_text(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < 80:
        return True
    weird = sum(1 for ch in stripped if ch in "�□■◆◇")
    ascii_noise = sum(1 for ch in stripped if ch in "|~`^_")
    return weird > 5 or ascii_noise / max(len(stripped), 1) > 0.04


def extract_pages_from_pdf(pdf_path: Path, engine: str) -> list[dict]:
    import fitz

    rows: list[dict] = []
    with fitz.open(pdf_path) as doc:
        for index, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            rows.append(
                {
                    "page": index,
                    "text": text.rstrip(),
                    "char_count": len(text.strip()),
                    "ocr_engine": engine,
                    "needs_review": needs_review_text(text),
                }
            )
    return rows


def run_ocrmypdf(input_pdf: Path, output_pdf: Path, lang: str) -> tuple[bool, str]:
    if not shutil.which("ocrmypdf"):
        return False, "ocrmypdf command not found"
    cmd = [
        "ocrmypdf",
        "--language",
        lang,
        "--rotate-pages",
        "--deskew",
        "--clean",
        "--optimize",
        "1",
        "--skip-text",
        str(input_pdf),
        str(output_pdf),
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=None,
        )
    except Exception as exc:
        return False, repr(exc)
    log = (proc.stdout + "\n" + proc.stderr).strip()
    return proc.returncode == 0 and output_pdf.exists(), log


def fallback_pytesseract(input_pdf: Path, output_pdf: Path, lang: str, debug_dir: Path) -> tuple[list[dict], str]:
    if not shutil.which("tesseract"):
        raise RuntimeError("tesseract command not found")

    import fitz
    import pytesseract

    rows: list[dict] = []
    log_lines = ["fallback=pymupdf+pytesseract"]
    out_doc = fitz.open()
    debug_dir.mkdir(parents=True, exist_ok=True)

    with fitz.open(input_pdf) as doc:
        total = doc.page_count
        for index, page in enumerate(doc, start=1):
            zoom = 2.2
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            image = None
            try:
                from PIL import Image

                image = Image.open(BytesIO(pix.tobytes("png")))
                text = pytesseract.image_to_string(image, lang=lang)
                pdf_bytes = pytesseract.image_to_pdf_or_hocr(image, lang=lang, extension="pdf")
                page_pdf = fitz.open("pdf", pdf_bytes)
                out_doc.insert_pdf(page_pdf)
                page_pdf.close()
            except Exception as exc:
                text = ""
                log_lines.append(f"page {index}/{total} failed: {exc!r}")
                # Keep a raster-only page so page counts remain aligned.
                rect = page.rect
                new_page = out_doc.new_page(width=rect.width, height=rect.height)
                new_page.show_pdf_page(rect, doc, index - 1)
            finally:
                if image is not None:
                    image.close()
            rows.append(
                {
                    "page": index,
                    "text": text.rstrip(),
                    "char_count": len(text.strip()),
                    "ocr_engine": "pymupdf+pytesseract",
                    "needs_review": needs_review_text(text),
                }
            )
            if index % 10 == 0:
                print(f"OCR fallback progress: {index}/{total}", flush=True)

    out_doc.save(output_pdf)
    out_doc.close()
    return rows, "\n".join(log_lines)


def _rapidocr_worker_init(input_pdf: str, zoom: float) -> None:
    import fitz
    from rapidocr_onnxruntime import RapidOCR

    global RAPIDOCR_DOC, RAPIDOCR_ENGINE, RAPIDOCR_ZOOM
    RAPIDOCR_DOC = fitz.open(input_pdf)
    RAPIDOCR_ENGINE = RapidOCR()
    RAPIDOCR_ZOOM = zoom


def _rapidocr_page_worker(page_number: int) -> dict:
    import fitz
    import numpy as np
    from PIL import Image

    if RAPIDOCR_DOC is None or RAPIDOCR_ENGINE is None:
        raise RuntimeError("RapidOCR worker is not initialized")
    page = RAPIDOCR_DOC[page_number - 1]
    pix = page.get_pixmap(matrix=fitz.Matrix(RAPIDOCR_ZOOM, RAPIDOCR_ZOOM), alpha=False)
    image = Image.open(BytesIO(pix.tobytes("png"))).convert("RGB")
    try:
        result, elapsed = RAPIDOCR_ENGINE(np.array(image))
    finally:
        image.close()

    items = result or []

    def key(item):
        box = item[0]
        xs = [pt[0] for pt in box]
        ys = [pt[1] for pt in box]
        return (min(ys), min(xs))

    serial_items = []
    for item in sorted(items, key=key):
        if len(item) < 2:
            continue
        box = [[float(pt[0]), float(pt[1])] for pt in item[0]]
        text = str(item[1]).strip()
        score = float(item[2]) if len(item) >= 3 and isinstance(item[2], (int, float)) else None
        if text:
            serial_items.append({"box": box, "text": text, "score": score})

    text = "\n".join(item["text"] for item in serial_items)
    scores = [item["score"] for item in serial_items if item["score"] is not None]
    avg_score = sum(scores) / len(scores) if scores else 0.0
    return {
        "page": page_number,
        "text": text,
        "items": serial_items,
        "avg_score": avg_score,
        "elapsed": elapsed,
    }


def _insert_rapidocr_text(new_page, items: list[dict], zoom: float, log_lines: list[str], page_number: int) -> None:
    import fitz

    for item in items:
        box, line_text = item["box"], item["text"]
        xs = [pt[0] / zoom for pt in box]
        ys = [pt[1] / zoom for pt in box]
        bbox = fitz.Rect(min(xs), min(ys), max(xs), max(ys))
        fontsize = max(4, min(12, bbox.height * 0.8))
        try:
            new_page.insert_textbox(
                bbox,
                line_text,
                fontsize=fontsize,
                fontname="china-s",
                render_mode=3,
            )
        except Exception:
            try:
                new_page.insert_textbox(bbox, line_text, fontsize=fontsize, render_mode=3)
            except Exception as exc:
                if page_number <= 3:
                    log_lines.append(f"page {page_number} invisible text insert failed: {exc!r}")
                break


def fallback_rapidocr(input_pdf: Path, output_pdf: Path, debug_dir: Path, jobs: int = 1) -> tuple[list[dict], str]:
    import fitz

    rows: list[dict] = []
    log_lines = [f"fallback=pymupdf+rapidocr-onnxruntime; jobs={jobs}"]
    out_doc = fitz.open()
    debug_dir.mkdir(parents=True, exist_ok=True)
    zoom = 1.6

    with fitz.open(input_pdf) as doc:
        total = doc.page_count
        if jobs <= 1:
            _rapidocr_worker_init(str(input_pdf), zoom)
            results = []
            for page_number in range(1, total + 1):
                try:
                    results.append(_rapidocr_page_worker(page_number))
                except Exception as exc:
                    log_lines.append(f"page {page_number}/{total} rapidocr failed: {exc!r}")
                    results.append({"page": page_number, "text": "", "items": [], "avg_score": 0.0, "elapsed": None})
                if page_number % 10 == 0 or page_number == total:
                    print(f"OCR rapidocr progress: {page_number}/{total}", flush=True)
        else:
            ctx = mp.get_context("spawn")
            results = []
            done = 0
            with ctx.Pool(processes=jobs, initializer=_rapidocr_worker_init, initargs=(str(input_pdf), zoom)) as pool:
                for result in pool.imap_unordered(_rapidocr_page_worker, range(1, total + 1), chunksize=1):
                    results.append(result)
                    done += 1
                    if done % 10 == 0 or done == total:
                        print(f"OCR rapidocr progress: {done}/{total}", flush=True)

        by_page = {result["page"]: result for result in results}
        for page_number in range(1, total + 1):
            result = by_page.get(page_number, {"page": page_number, "text": "", "items": [], "avg_score": 0.0})
            page = doc[page_number - 1]
            rect = page.rect
            new_page = out_doc.new_page(width=rect.width, height=rect.height)
            new_page.show_pdf_page(rect, doc, page_number - 1)
            _insert_rapidocr_text(new_page, result.get("items", []), zoom, log_lines, page_number)
            text = result.get("text", "")
            avg_score = float(result.get("avg_score") or 0.0)
            rows.append(
                {
                    "page": page_number,
                    "text": text.rstrip(),
                    "char_count": len(text.strip()),
                    "ocr_engine": "pymupdf+rapidocr",
                    "needs_review": needs_review_text(text) or avg_score < 0.55,
                    "ocr_avg_score": round(avg_score, 4),
                }
            )

    out_doc.save(output_pdf)
    out_doc.close()
    return rows, "\n".join(log_lines)


def write_book_markdown(rows: list[dict], path: Path) -> None:
    parts = ["# 从大都到上都 OCR 文本", ""]
    for row in rows:
        page = row["page"]
        parts.extend([f"<!-- page: {page} -->", f'<a id="p{page}"></a>', "", row.get("text", "").rstrip(), ""])
    path.write_text("\n".join(parts), encoding="utf-8")


def write_report(rows: list[dict], path: Path, ocr_log: str, output_pdf: Path) -> None:
    total = len(rows)
    empty = [r["page"] for r in rows if not r.get("text", "").strip()]
    short = [r["page"] for r in rows if 0 < r.get("char_count", 0) < 80]
    review = [r["page"] for r in rows if r.get("needs_review")]
    chars = [r.get("char_count", 0) for r in rows]
    avg = sum(chars) / total if total else 0
    success = total - len(empty)
    lines = [
        "# OCR 抽取报告",
        "",
        f"- Generated at: {datetime.now().isoformat(timespec='seconds')}",
        f"- OCR PDF: `{output_pdf}`",
        f"- 总页数: {total}",
        f"- OCR 成功页数: {success}",
        f"- 空文本页数: {len(empty)}",
        f"- 字符数过少页: {len(short)}",
        f"- 疑似识别错误页: {len(review)}",
        f"- 平均每页字符数: {avg:.1f}",
        f"- 是否需要人工复核: {'是' if empty or review else '否'}",
        "",
        "## 空文本页",
        "",
        ", ".join(map(str, empty)) if empty else "无",
        "",
        "## 字符数过少页",
        "",
        ", ".join(map(str, short)) if short else "无",
        "",
        "## 疑似识别错误页",
        "",
        ", ".join(map(str, review[:200])) + (" ..." if len(review) > 200 else "") if review else "无",
        "",
        "## OCR Log 摘要",
        "",
        "```text",
        ocr_log[-8000:] if ocr_log else "No OCR log captured.",
        "```",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_pdf", type=Path)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "data" / "ocr")
    parser.add_argument("--lang", default="chi_sim+eng")
    parser.add_argument("--jobs", type=int, default=1, help="Parallel workers for RapidOCR fallback.")
    args = parser.parse_args()

    input_pdf = args.input_pdf.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    output_pdf = out_dir / "book_ocr.pdf"
    data_dir = ROOT / "data"
    debug_dir = data_dir / "debug"

    if not input_pdf.exists():
        raise FileNotFoundError(input_pdf)

    print(f"OCR input: {input_pdf}")
    ok, log = run_ocrmypdf(input_pdf, output_pdf, args.lang)
    if ok:
        rows = extract_pages_from_pdf(output_pdf, "ocrmypdf+tesseract")
    else:
        print("OCRmyPDF unavailable or failed; falling back to PyMuPDF+pytesseract.", flush=True)
        try:
            rows, fallback_log = fallback_pytesseract(input_pdf, output_pdf, args.lang, debug_dir)
        except Exception as exc:
            print(f"PyMuPDF+pytesseract failed ({exc!r}); falling back to RapidOCR.", flush=True)
            rows, fallback_log = fallback_rapidocr(input_pdf, output_pdf, debug_dir, jobs=max(1, args.jobs))
        log = (log or "") + "\n\n" + fallback_log

    write_jsonl(data_dir / "book_pages.jsonl", rows)
    write_book_markdown(rows, data_dir / "book.md")
    write_report(rows, data_dir / "extraction_report.md", log, output_pdf)
    print(f"Wrote {output_pdf}")
    print(f"Wrote {data_dir / 'book_pages.jsonl'}")
    print(f"Wrote {data_dir / 'book.md'}")
    print(f"Wrote {data_dir / 'extraction_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
