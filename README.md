# Hyde My PII

A Python CLI and GUI app that takes PDF, image, text, and document files, detects sensitive information, and replaces it with realistic fake data.

## Features

- **Graphical Interface** - Easy-to-use GUI for drag-and-drop file processing
- **Command Line** - Powerful CLI for automation and batch processing
- Processes single files or whole directories
- Supports: `txt`, `md`, `csv`, `json`, `log`, `docx`, `pdf`, and common images
- **OCR with automatic language detection** - Tesseract OCR with auto-detection for multi-language documents
- Replaces detected entities with consistent fake values per run
- Organized multi-file architecture (not a single script)

## Detected sensitive data

The app detects and replaces the following sensitive information patterns:

- **Person names** - All-caps names (GABRIEL, MANCINI, etc.)
- **Dates** - Various formats (DD-MM-YYYY, DD/MM/YYYY, YYYY-MM-DD, DD.MM.YYYY)
- **PESEL numbers** - Polish national ID (11 digits, with or without formatting)
- **Email addresses** - Standard email format
- **Phone numbers** - International and local formats
- **Social Security Numbers (SSN)** - Format XXX-XX-XXXX
- **Credit card numbers** - 13-19 digit sequences (Luhn algorithm compatible)
- **IPv4 addresses** - Internet Protocol v4 addresses
- **IBAN/Bank account numbers** - International Bank Account Number patterns

## Supported file formats

**Text and Documents:**
- `.txt` - Plain text
- `.md` - Markdown
- `.csv` - Comma-separated values
- `.json` - JSON data
- `.log` - Log files
- `.yaml`, `.yml` - YAML configs
- `.xml`, `.html`, `.htm` - Markup files
- `.docx` - Microsoft Word documents
- `.pdf` - PDF files (text extraction or OCR)

**Images (with OCR):**
- `.png`, `.jpg`, `.jpeg` - Common image formats
- `.bmp`, `.tif`, `.tiff` - Bitmap formats
- `.webp` - Modern web image format

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

### Installing additional OCR languages

By default, Tesseract only includes English language data. To support other languages, you need to add training data files:

**Option 1: Download from Tesseract GitHub** (recommended)
1. Go to: https://github.com/UB-Mannheim/tesseract/wiki#languages
2. Download the `.traineddata` files for the languages you need (e.g., `pol.traineddata`, `deu.traineddata`)
3. Place them in: `C:\Program Files\Tesseract-OCR\tessdata\`

**Option 2: Use environment variable (advanced)**
- Set `TESSDATA_PREFIX` environment variable to your custom tessdata directory
- Example: `$env:TESSDATA_PREFIX = "C:\path\to\your\tessdata"`

**Available languages:** The app will auto-detect and fall back to English if a language's training data is missing. Check what languages you have installed with:
```powershell
ls "C:\Program Files\Tesseract-OCR\tessdata\*.traineddata"
```

### Automatic language detection

The app automatically detects document language when you use `--ocr` or the GUI with "auto" language setting (default).

**How it works:**
1. App analyzes text from the document
2. Detects primary language(s) using `langdetect`
3. Checks if Tesseract has training data for detected language(s)
4. **Gracefully falls back to English** if detected language isn't installed

**Example:**
- Document is in Polish + English mix
- Detection finds: Polish detected, English detected
- Only English .traineddata available
- Fallback: Uses English without errors or stopping

If auto-detection doesn't work well, you can manually specify language with `--ocr-lang eng` (CLI) or dropdown menu (GUI).

### OCR optimization for poor quality scans

When processing low-quality or faded scans, the app uses an advanced preprocessing pipeline:

1. **Contrast enhancement** (2.5x) - Brightens faded text
2. **Brightness adjustment** (1.15x) - Helps with very dark scans
3. **Sharpness enhancement** (2.0x) - Makes text edges crisper
4. **Median filtering** - Removes noise while preserving text
5. **Histogram equalization** - Balances lighting across document
6. **Binary thresholding** - Converts to pure black/white for extremely poor scans

This pipeline is automatically applied to PDF pages during OCR conversion, resulting in:
- Better text recognition on faded documents
- Fewer OCR artifacts and noise
- Higher accuracy on degraded/aged paper scans
- Works seamlessly without user configuration

### Environment variables (advanced)

If auto-detection fails to find OCR tools, you can set:
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
- Configure OCR with automatic language detection
- See real-time processing progress
- View results and warnings

**Features:**
- Drag-and-drop file selection
- **Automatic language detection** - Auto-detects document language or manually select any installed language
- Dynamically shows only available OCR languages (based on installed Tesseract data files)
- Faker locale selection for realistic fake data
- Process individual files or entire directories
- Real-time progress log with detailed warnings

### Command Line Mode (Advanced)

```bash
hydemypii INPUT_PATH -o output --ocr
```

Examples:

```bash
# Process one PDF with automatic language detection
hydemypii ./invoices/report.pdf -o ./sanitized --ocr

# Process all supported files in a folder
hydemypii ./documents -o ./sanitized

# Use specific OCR language (instead of automatic detection)
hydemypii ./documents -o ./sanitized --ocr --ocr-lang eng

# Process multi-language document with auto-detection
hydemypii ./mixed_lang.pdf -o ./sanitized --ocr --ocr-lang auto

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

- **PII Detection**: Regex-based detection is fast and practical for most use cases, but not perfect. Complex or unusual formats might not be detected. Contributions welcome!
- **OCR Optional**: OCR tools are only needed if processing scanned PDFs or images. Plain text and document files work without OCR.
- **Missing Dependencies**: If OCR tools are missing, the app gracefully skips OCR-dependent files and prints helpful warnings.
- **Data Consistency**: All PII replacements within a single run use consistent fake data (same email always replaced with same fake email).
- **Output Format**: All output files are saved as `.sanitized.txt` in the output directory, regardless of input format.
- **Performance**: Processing time depends on file size and OCR complexity. OCR processing is typically slower than text extraction.
