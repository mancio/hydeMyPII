# Hyde My PII

A Python CLI and GUI app that takes PDF, image, text, and document files, detects sensitive information, and replaces it with realistic fake data.

## Features

- **Graphical Interface** - Easy-to-use GUI for drag-and-drop file processing
- **Command Line** - Powerful CLI for automation and batch processing
- Processes single files or whole directories
- Supports: `txt`, `md`, `csv`, `json`, `log`, `docx`, `pdf`, and common images
- OCR support for scanned PDFs and image files (via Tesseract)
- Replaces detected entities with consistent fake values per run
- Organized multi-file architecture (not a single script)

## Detected sensitive data (current)

- **Person names** - All-caps names (GABRIEL, MANCINI, etc.)
- **Dates** - Various formats (DD-MM-YYYY, DD/MM/YYYY, YYYY-MM-DD)
- **PESEL numbers** - Polish national ID (11 digits or formatted)
- **Email addresses**
- **Phone numbers**
- **SSN format** (`123-45-6789`)
- **Credit-card-like numbers**
- **IPv4 addresses**
- **IBAN-like strings**

## Install

```bash
pip install -e .
```

## OCR prerequisites

Install Tesseract OCR and Poppler on your machine.

**Note:** The app automatically detects these tools from common install locations on Windows, so restarting your terminal is optional (not required).

### Windows quick setup

```powershell
winget install UB-Mannheim.TesseractOCR
winget install oschwartz10612.poppler
```

You can verify installation with:

```powershell
tesseract --version
pdftoppm -h
```

If auto-detection fails, you can set:
- `TESSERACT_CMD` environment variable to your `tesseract.exe` path
- `POPPLER_PATH` environment variable to your Poppler `bin` folder
- Or use `--poppler-path` CLI option

## Usage

### GUI Mode (Easy)

```bash
hydemypii-gui
```

Or alternatively:
```bash
python run_gui.py      # Cross-platform
run_gui.bat            # Windows shortcut
```

This opens a graphical interface where you can:
- Browse and select files or folders
- Configure OCR and output options
- See real-time processing progress
- View results and warnings

**Features:**
- Drag-and-drop file selection
- OCR language selection (English, Polish, German, French, Spanish, Italian, Portuguese)
- Faker locale selection for realistic fake data
- Process individual files or entire directories
- Real-time progress log

### Command Line Mode (Advanced)

```bash
hydemypii INPUT_PATH -o output --ocr
```

Examples:

```bash
# Process one PDF
hydemypii ./invoices/report.pdf -o ./sanitized --ocr

# Process all supported files in a folder
hydemypii ./documents -o ./sanitized

# Try all files, even unknown extensions
hydemypii ./documents -o ./sanitized --all-files --ocr

# Explicitly specify Poppler location (if auto-detection fails)
hydemypii ./scan.pdf -o ./output --ocr --poppler-path "C:/path/to/poppler/bin"
```

Output files are written as `.sanitized.txt` into the output directory.

## Project structure

```text
src/hydemypii/
  __main__.py
  cli.py           # Command-line interface
  gui.py           # Graphical interface
  detector.py      # PII detection patterns
  extractor.py     # Text extraction + OCR
  faker_engine.py  # Fake data generation
  redactor.py      # PII replacement engine
  types.py         # Data structures
```

## Notes

- This is regex-based PII detection. It is fast and practical, but not perfect.
- If OCR tools are missing, the app will skip OCR-dependent files and print warnings.
