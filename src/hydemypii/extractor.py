from __future__ import annotations

import os
import platform
import shutil
from pathlib import Path

from hydemypii.types import ExtractionResult

_TEXT_EXTENSIONS = {
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
}
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


def _resolve_poppler_bin_dir(override_path: str | None = None) -> str | None:
    if override_path:
        override_dir = Path(override_path)
        if override_dir.is_dir() and (override_dir / "pdftoppm.exe").exists():
            return str(override_dir)
        if override_dir.is_dir():
            found = next(override_dir.rglob("pdftoppm.exe"), None)
            if found:
                return str(found.parent)

    pdftoppm_exe = shutil.which("pdftoppm")
    if pdftoppm_exe:
        return str(Path(pdftoppm_exe).resolve().parent)

    poppler_env = os.environ.get("POPPLER_PATH")
    if poppler_env:
        poppler_dir = Path(poppler_env)
        if poppler_dir.is_dir() and (poppler_dir / "pdftoppm.exe").exists():
            return str(poppler_dir)

    candidates: list[Path] = []
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        winget_packages = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages"
        if winget_packages.exists():
            candidates.extend(winget_packages.glob("*Poppler*"))

    program_files = os.environ.get("ProgramFiles")
    if program_files:
        candidates.append(Path(program_files) / "poppler" / "Library" / "bin")

    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        candidates.append(Path(user_profile) / "scoop" / "apps" / "poppler" / "current" / "Library" / "bin")

    for candidate in candidates:
        if candidate.is_dir() and (candidate / "pdftoppm.exe").exists():
            return str(candidate)
        if candidate.is_dir():
            found = next(candidate.rglob("pdftoppm.exe"), None)
            if found:
                return str(found.parent)

    return None


def _resolve_tesseract_cmd() -> str | None:
    tesseract_exe = shutil.which("tesseract")
    if tesseract_exe:
        return str(Path(tesseract_exe).resolve())

    tesseract_env = os.environ.get("TESSERACT_CMD")
    if tesseract_env:
        tesseract_path = Path(tesseract_env)
        if tesseract_path.is_file() and tesseract_path.exists():
            return str(tesseract_path)

    candidates: list[Path] = []
    program_files = os.environ.get("ProgramFiles")
    if program_files:
        candidates.append(Path(program_files) / "Tesseract-OCR" / "tesseract.exe")

    program_files_x86 = os.environ.get("ProgramFiles(x86)")
    if program_files_x86:
        candidates.append(Path(program_files_x86) / "Tesseract-OCR" / "tesseract.exe")

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        winget_packages = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages"
        if winget_packages.exists():
            for pkg_dir in winget_packages.glob("*Tesseract*"):
                found = next(pkg_dir.rglob("tesseract.exe"), None)
                if found:
                    candidates.append(found)

    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        candidates.append(Path(user_profile) / "scoop" / "apps" / "tesseract" / "current" / "tesseract.exe")

    for candidate in candidates:
        if candidate.is_file() and candidate.exists():
            return str(candidate)

    return None


def _pdf_ocr_error_message(exc: Exception) -> str:
    base = f"PDF OCR conversion failed: {exc}"
    message_lower = str(exc).lower()
    if "poppler" not in message_lower and "page count" not in message_lower:
        return base

    if platform.system() == "Windows":
        return (
            f"{base}. Poppler is required for scanned PDF OCR. "
            "Install with `winget install oschwartz10612.poppler` (or choco/scoop), "
            "then reopen the terminal so PATH refreshes."
        )

    return (
        f"{base}. Poppler is required for scanned PDF OCR. "
        "Install Poppler and ensure `pdftoppm` is available in PATH."
    )


def extract_text(path: Path, ocr_enabled: bool, ocr_lang: str = "eng", poppler_path: str | None = None) -> ExtractionResult:
    suffix = path.suffix.lower()

    if suffix in _TEXT_EXTENSIONS:
        return _extract_text_file(path)
    if suffix == ".docx":
        return _extract_docx(path)
    if suffix == ".pdf":
        return _extract_pdf(path, ocr_enabled=ocr_enabled, ocr_lang=ocr_lang, poppler_path=poppler_path)
    if suffix in _IMAGE_EXTENSIONS:
        if not ocr_enabled:
            return ExtractionResult(
                source_path=path,
                text="",
                used_ocr=False,
                warnings=["Image input requires --ocr to be enabled."],
            )
        return _extract_image_ocr(path, ocr_lang=ocr_lang)

    return ExtractionResult(
        source_path=path,
        text="",
        used_ocr=False,
        warnings=[f"Unsupported file type: {suffix or '<no extension>'}"],
    )


def _extract_text_file(path: Path) -> ExtractionResult:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = path.read_text(encoding="latin-1", errors="replace")
    return ExtractionResult(source_path=path, text=content)


def _extract_docx(path: Path) -> ExtractionResult:
    try:
        from docx import Document
    except ImportError:
        return ExtractionResult(
            source_path=path,
            text="",
            warnings=["python-docx is not installed."],
        )

    doc = Document(str(path))
    text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
    return ExtractionResult(source_path=path, text=text)


def _extract_pdf(path: Path, ocr_enabled: bool, ocr_lang: str, poppler_path: str | None = None) -> ExtractionResult:
    warnings: list[str] = []

    try:
        from pypdf import PdfReader
    except ImportError:
        return ExtractionResult(
            source_path=path,
            text="",
            warnings=["pypdf is not installed."],
        )

    reader = PdfReader(str(path))
    extracted_pages: list[str] = []
    for page in reader.pages:
        extracted_pages.append(page.extract_text() or "")

    text = "\n\n".join(extracted_pages).strip()
    if text:
        return ExtractionResult(source_path=path, text=text, used_ocr=False)

    if not ocr_enabled:
        warnings.append("No machine-readable text found in PDF. Re-run with --ocr.")
        return ExtractionResult(source_path=path, text="", used_ocr=False, warnings=warnings)

    ocr_result = _extract_pdf_with_ocr(path, ocr_lang=ocr_lang, poppler_path=poppler_path)
    ocr_result.warnings.extend(warnings)
    return ocr_result


def _extract_pdf_with_ocr(path: Path, ocr_lang: str, poppler_path: str | None = None) -> ExtractionResult:
    warnings: list[str] = []
    poppler_bin = _resolve_poppler_bin_dir(override_path=poppler_path)

    try:
        from pdf2image import convert_from_path
    except ImportError:
        return ExtractionResult(
            source_path=path,
            text="",
            used_ocr=False,
            warnings=["pdf2image is not installed."],
        )

    try:
        import pytesseract
    except ImportError:
        return ExtractionResult(
            source_path=path,
            text="",
            used_ocr=False,
            warnings=["pytesseract is not installed."],
        )

    tesseract_cmd = _resolve_tesseract_cmd()
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    try:
        if poppler_bin:
            images = convert_from_path(str(path), poppler_path=poppler_bin)
        else:
            images = convert_from_path(str(path))
    except Exception as exc:
        details = _pdf_ocr_error_message(exc)
        if not poppler_bin and platform.system() == "Windows":
            details += " You can also set POPPLER_PATH to your Poppler bin folder."
        return ExtractionResult(
            source_path=path,
            text="",
            used_ocr=False,
            warnings=[details],
        )

    pages_text: list[str] = []
    try:
        for image in images:
            pages_text.append(pytesseract.image_to_string(image, lang=ocr_lang))
    except pytesseract.TesseractNotFoundError:
        msg = "Tesseract OCR is not installed or not in PATH."
        if platform.system() == "Windows":
            msg += " Install with `winget install UB-Mannheim.TesseractOCR`."
            if not tesseract_cmd:
                msg += " You can also set TESSERACT_CMD to your tesseract.exe path."
        return ExtractionResult(
            source_path=path,
            text="",
            used_ocr=False,
            warnings=[msg],
        )
    except Exception as exc:
        return ExtractionResult(
            source_path=path,
            text="",
            used_ocr=False,
            warnings=[f"OCR processing failed: {exc}"],
        )

    text = "\n\n".join(pages_text).strip()
    if not text:
        warnings.append("OCR ran but no text was recognized.")

    return ExtractionResult(source_path=path, text=text, used_ocr=True, warnings=warnings)


def _extract_image_ocr(path: Path, ocr_lang: str) -> ExtractionResult:
    try:
        from PIL import Image
    except ImportError:
        return ExtractionResult(source_path=path, text="", warnings=["Pillow is not installed."])

    try:
        import pytesseract
    except ImportError:
        return ExtractionResult(source_path=path, text="", warnings=["pytesseract is not installed."])

    tesseract_cmd = _resolve_tesseract_cmd()
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    try:
        image = Image.open(path)
        text = pytesseract.image_to_string(image, lang=ocr_lang)
        return ExtractionResult(source_path=path, text=text, used_ocr=True)
    except pytesseract.TesseractNotFoundError:
        msg = "Tesseract OCR is not installed or not in PATH."
        if platform.system() == "Windows":
            msg += " Install with `winget install UB-Mannheim.TesseractOCR`."
            if not tesseract_cmd:
                msg += " You can also set TESSERACT_CMD to your tesseract.exe path."
        return ExtractionResult(
            source_path=path,
            text="",
            used_ocr=False,
            warnings=[msg],
        )
    except Exception as exc:
        return ExtractionResult(
            source_path=path,
            text="",
            used_ocr=False,
            warnings=[f"Image OCR failed: {exc}"],
        )
