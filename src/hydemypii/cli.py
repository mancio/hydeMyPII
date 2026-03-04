from __future__ import annotations

import argparse
from pathlib import Path

from hydemypii.extractor import extract_text
from hydemypii.redactor import PIIRedactor

_SUPPORTED_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".log",
    ".yaml",
    ".yml",
    ".xml",
    ".html",
    ".htm",
    ".docx",
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hydemypii",
        description="Replace sensitive info with fake data in files (text/docs/pdf/images).",
    )
    parser.add_argument("input", help="Input file or directory path")
    parser.add_argument("-o", "--output", default="output", help="Output directory")
    parser.add_argument("--ocr", action="store_true", help="Enable OCR for images and scanned PDFs")
    parser.add_argument("--ocr-lang", default="auto", help="Tesseract language code (default: auto) - use 'auto' for automatic detection, or codes like 'eng', 'pol', 'deu'")
    parser.add_argument("--poppler-path", help="Explicit path to Poppler bin directory (for PDF OCR)")
    parser.add_argument("--locale", default="en_US", help="Faker locale (default: en_US)")
    parser.add_argument(
        "--all-files",
        action="store_true",
        help="Try processing all files (not only known extensions)",
    )
    return parser


def _collect_files(input_path: Path, include_unknown: bool) -> list[Path]:
    if input_path.is_file():
        return [input_path]

    files = [path for path in input_path.rglob("*") if path.is_file()]
    if include_unknown:
        return files
    return [path for path in files if path.suffix.lower() in _SUPPORTED_EXTENSIONS]


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()

    if not input_path.exists():
        parser.error(f"Input path does not exist: {input_path}")

    redactor = PIIRedactor(locale=args.locale)
    files = _collect_files(input_path, include_unknown=args.all_files)
    if not files:
        print("No files found to process.")
        return 1

    processed = 0
    total_replacements = 0

    for file_path in files:
        extraction = extract_text(file_path, ocr_enabled=args.ocr, ocr_lang=args.ocr_lang, poppler_path=args.poppler_path)
        if not extraction.text.strip():
            joined = "; ".join(extraction.warnings) if extraction.warnings else "No text extracted"
            print(f"[SKIP] {file_path} -> {joined}")
            continue

        result = redactor.redact(extraction, output_dir=output_dir)
        processed += 1
        total_replacements += result.replacements_count

        message = f"[OK] {file_path} -> {result.output_path} (replacements: {result.replacements_count})"
        if result.used_ocr:
            message += " [OCR]"
        print(message)

        if result.warnings:
            print(f"      warnings: {'; '.join(result.warnings)}")

    print(f"Done. Files processed: {processed}/{len(files)}. Total replacements: {total_replacements}")
    return 0 if processed else 2


if __name__ == "__main__":
    raise SystemExit(main())
