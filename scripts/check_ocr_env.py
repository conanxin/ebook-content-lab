from __future__ import annotations

import importlib.util
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data" / "ocr_env_report.md"


def run_command(args: list[str], timeout: int = 20) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return proc.returncode, (proc.stdout + proc.stderr).strip()
    except FileNotFoundError:
        return 127, "not found"
    except subprocess.TimeoutExpired:
        return 124, "timeout"


def command_version(command: str, version_args: list[str] | None = None) -> dict[str, str | bool]:
    path = shutil.which(command)
    if not path:
        return {"available": False, "path": "", "version": ""}
    args = [command] + (version_args or ["--version"])
    code, output = run_command(args)
    first_line = output.splitlines()[0] if output else f"exit {code}"
    return {"available": True, "path": path, "version": first_line}


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def detect_tesseract_langs() -> tuple[bool, list[str], str]:
    if not shutil.which("tesseract"):
        return False, [], "tesseract not found"
    code, output = run_command(["tesseract", "--list-langs"])
    langs = [line.strip() for line in output.splitlines() if line.strip() and "List of available languages" not in line]
    return code == 0 and "chi_sim" in langs, langs, output


def install_hint(system: str) -> str:
    if system == "Windows":
        return """```powershell
winget install UB-Mannheim.TesseractOCR
winget install ArtifexSoftware.Ghostscript
winget install qpdf.qpdf
winget install oschwartz10612.Poppler
python -m pip install -r requirements.txt
```"""
    if system == "Darwin":
        return """```bash
brew install tesseract tesseract-lang ocrmypdf poppler ghostscript qpdf
python -m pip install -r requirements.txt
```"""
    return """```bash
sudo apt update
sudo apt install -y tesseract-ocr tesseract-ocr-chi-sim ocrmypdf poppler-utils ghostscript qpdf
python -m pip install -r requirements.txt
```"""


def main() -> int:
    system = platform.system()
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    checks = {
        "python": {
            "available": True,
            "path": sys.executable,
            "version": sys.version.replace("\n", " "),
        },
        "tesseract": command_version("tesseract"),
        "ocrmypdf": command_version("ocrmypdf"),
        "qpdf": command_version("qpdf"),
        "ghostscript_gswin64c": command_version("gswin64c"),
        "ghostscript_gs": command_version("gs"),
        "pdftoppm": command_version("pdftoppm", ["-v"]),
        "pdfinfo": command_version("pdfinfo", ["-v"]),
    }
    chi_sim_ok, langs, lang_output = detect_tesseract_langs()
    modules = {
        "fitz": module_available("fitz"),
        "pymupdf4llm": module_available("pymupdf4llm"),
        "pytesseract": module_available("pytesseract"),
        "PIL": module_available("PIL"),
        "ocrmypdf": module_available("ocrmypdf"),
    }

    missing = []
    if not checks["tesseract"]["available"]:
        missing.append("tesseract")
    if checks["tesseract"]["available"] and not chi_sim_ok:
        missing.append("tesseract chi_sim language data")
    if not checks["ocrmypdf"]["available"]:
        missing.append("ocrmypdf command")
    if not (checks["pdftoppm"]["available"] or checks["pdfinfo"]["available"] or checks["qpdf"]["available"]):
        missing.append("PDF command-line tools such as poppler/qpdf")

    lines = [
        "# OCR 环境检测报告",
        "",
        f"- Generated at: {datetime.now().isoformat(timespec='seconds')}",
        f"- System: {system} {platform.release()}",
        f"- Machine: {platform.machine()}",
        "",
        "## Command Checks",
        "",
        "| Item | Available | Path | Version |",
        "| --- | --- | --- | --- |",
    ]
    for name, info in checks.items():
        lines.append(
            f"| {name} | {info['available']} | `{info['path']}` | {str(info['version']).replace('|', '/')} |"
        )
    lines.extend(
        [
            "",
            "## Tesseract Languages",
            "",
            f"- `chi_sim` available: {chi_sim_ok}",
            f"- Languages: {', '.join(langs) if langs else 'none detected'}",
            "",
            "## Python Modules",
            "",
            "| Module | Available |",
            "| --- | --- |",
        ]
    )
    for name, ok in modules.items():
        lines.append(f"| {name} | {ok} |")
    lines.extend(["", "## Missing Or Needs Attention", ""])
    if missing:
        for item in missing:
            lines.append(f"- {item}")
    else:
        lines.append("- None detected for the requested OCR path.")
    lines.extend(["", "## Minimal Install Command", "", install_hint(system), ""])
    if lang_output and not langs:
        lines.extend(["## Raw Language Probe", "", "```", lang_output[:4000], "```", ""])

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT}")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
