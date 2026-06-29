# 脚本说明

- `check_ocr_env.py`：检测 Python、Tesseract、中文语言包、OCRmyPDF、PDF 工具，输出 `data/ocr_env_report.md`。
- `ocr_pdf.py`：对 `source/book.pdf` 做 OCR，输出可搜索 PDF、逐页 JSONL、Markdown 和 OCR 报告。
- `identify_book.py`：基于子项目本地 PDF/OCR 文本识别书名、作者、出版信息、目录结构、语言、OCR 状态和适合的项目类型。
- `clean_ocr_text.py`：清理常见 OCR 噪声，保留页码并标记可疑页。
- `chunk_book.py`：按页和自然段切分为大模型可读 JSONL chunks。
- `geocode_places.py`：在不改变书中路线的前提下为地点补坐标。
- `build_geojson.py`：从路线 JSON 生成路线和地点 GeoJSON。
- `validate_route.py`：校验路线数据完整性和可追溯性。
- `export_gpx.py`：导出可下载 GPX，并同步复制到 `web/public/data/route.gpx`。
