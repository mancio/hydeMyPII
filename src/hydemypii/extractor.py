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


# Initialize TESSDATA_PREFIX at module level (before any pytesseract imports)
# This must be set before pytesseract is imported anywhere in the application
def _init_tessdata_prefix() -> None:
    """Set TESSDATA_PREFIX environment variable if not already set."""
    if "TESSDATA_PREFIX" not in os.environ:
        # Check common Tesseract installation paths for tessdata directory
        candidates = [
            Path("C:\\Program Files\\Tesseract-OCR\\tessdata"),
            Path("C:\\Program Files (x86)\\Tesseract-OCR\\tessdata"),
        ]
        
        program_files = os.environ.get("ProgramFiles")
        if program_files:
            candidates.append(Path(program_files) / "Tesseract-OCR" / "tessdata")
        
        for path in candidates:
            if path.is_dir():
                # Tesseract expects the directory path WITHOUT trailing separator
                os.environ["TESSDATA_PREFIX"] = str(path)
                break


# Run at module import time
_init_tessdata_prefix()


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


def _get_tessdata_path() -> Path | None:
    """Find the tessdata directory containing Tesseract language files."""
    # Check TESSDATA_PREFIX environment variable first
    tessdata_env = os.environ.get("TESSDATA_PREFIX")
    if tessdata_env:
        tessdata_path = Path(tessdata_env)
        if tessdata_path.is_dir():
            return tessdata_path
    
    # Check common Tesseract installation paths
    candidates = [
        Path("C:\\Program Files\\Tesseract-OCR\\tessdata"),
        Path("C:\\Program Files (x86)\\Tesseract-OCR\\tessdata"),
    ]
    
    program_files = os.environ.get("ProgramFiles")
    if program_files:
        candidates.append(Path(program_files) / "Tesseract-OCR" / "tessdata")
    
    program_files_x86 = os.environ.get("ProgramFiles(x86)")
    if program_files_x86:
        candidates.append(Path(program_files_x86) / "Tesseract-OCR" / "tessdata")
    
    for path in candidates:
        if path.is_dir():
            return path
    
    return None


def _get_available_languages() -> set[str]:
    """Get set of language codes that have training data available."""
    tessdata_path = _get_tessdata_path()
    if not tessdata_path:
        return {"eng"}  # Default to English if tessdata not found
    
    # Look for .traineddata files and extract language codes
    available = set()
    for traineddata_file in tessdata_path.glob("*.traineddata"):
        lang_code = traineddata_file.stem
        # Skip special files like osd (orientation) and equ (equation)
        if lang_code not in ("osd", "equ"):
            available.add(lang_code)
    
    return available if available else {"eng"}


def _filter_available_languages(ocr_lang: str) -> str:
    """
    Filter language codes to only those with available training data.
    Falls back to 'eng' for unavailable languages.
    
    Args:
        ocr_lang: Tesseract language code(s), e.g. 'eng' or 'eng+pol+deu'
    
    Returns:
        Filtered language code(s) with only available languages
    """
    available = _get_available_languages()
    
    # Handle multi-language input like "eng+pol+deu"
    requested_langs = ocr_lang.split("+")
    filtered_langs = [lang for lang in requested_langs if lang in available]
    
    if filtered_langs:
        return "+".join(filtered_langs)
    
    # No available languages found, fall back to English
    return "eng"


def _has_meaningful_text(text: str, min_alphanum: int = 50) -> bool:
    """Check if text contains meaningful content (not just whitespace/symbols)."""
    if not text:
        return False
    alphanum_count = sum(1 for char in text if char.isalnum())
    return alphanum_count >= min_alphanum


# Mapping from langdetect ISO 639-1 codes to Tesseract language codes
_LANG_DETECT_TO_TESSERACT = {
    "en": "eng",
    "pl": "pol",
    "de": "deu",
    "fr": "fra",
    "es": "spa",
    "it": "ita",
    "pt": "por",
    "nl": "nld",
    "ru": "rus",
    "ar": "ara",
    "zh-cn": "chi_sim",
    "zh-tw": "chi_tra",
    "ja": "jpn",
    "ko": "kor",
    "tr": "tur",
    "cs": "ces",
    "da": "dan",
    "fi": "fin",
    "el": "ell",
    "he": "heb",
    "hi": "hin",
    "hu": "hun",
    "id": "ind",
    "no": "nor",
    "ro": "ron",
    "sk": "slk",
    "sv": "swe",
    "th": "tha",
    "uk": "ukr",
    "vi": "vie",
}


def _detect_languages(text: str, max_languages: int = 3) -> str:
    """
    Detect language(s) from text and return Tesseract language codes.
    
    Args:
        text: The text to analyze
        max_languages: Maximum number of languages to detect (default: 3)
    
    Returns:
        Tesseract language code(s), e.g., "eng" or "eng+pol+deu" for multi-language.
        Returns "eng" as fallback if detection fails.
    """
    if not text or not text.strip():
        return "eng"  # Default fallback
    
    try:
        from langdetect import detect_langs, LangDetectException
    except ImportError:
        return "eng"  # Fallback if langdetect not available
    
    try:
        # detect_langs returns list of Language objects with lang code and probability
        detected = detect_langs(text)
        
        # Filter by minimum probability and limit to max_languages
        languages = []
        for lang_obj in detected[:max_languages]:
            if lang_obj.prob > 0.1:  # Only include if >10% probability
                lang_code = lang_obj.lang.lower()
                tesseract_code = _LANG_DETECT_TO_TESSERACT.get(lang_code)
                if tesseract_code and tesseract_code not in languages:
                    languages.append(tesseract_code)
        
        if languages:
            return "+".join(languages)
        
    except LangDetectException:
        pass  # Fall through to default
    except Exception:
        pass  # Fall through to default
    
    return "eng"  # Default fallback


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


def _preprocess_image_for_ocr(image):
    """Apply aggressive preprocessing to improve OCR on scanned documents.
    
    Handles low-quality, skewed, or faded scans by:
    - Grayscale conversion for better text detection
    - Aggressive contrast enhancement (2.5x)
    - Brightness adjustment for dark/light scans
    - Sharpness enhancement for crisper text edges
    - Median filtering to reduce noise
    - Histogram equalization for better contrast
    - Thresholding for extremely poor quality scans
    """
    try:
        from PIL import ImageEnhance, ImageFilter, ImageOps
        import numpy as np
        
        # Convert to grayscale if not already
        if image.mode != "L":
            image = image.convert("L")
        
        # Apply aggressive contrast enhancement for faded scans
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.5)  # Balanced aggressiveness
        
        # Correct brightness for very dark or washed out scans
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.15)
        
        # Sharpen to make text edges crisper
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        
        # Apply median filter for noise reduction
        try:
            image = image.filter(ImageFilter.MedianFilter(size=3))
        except Exception:
            pass  # MedianFilter might not be available
        
        # Try to auto-level (normalize histogram) for better contrast
        try:
            image = ImageOps.autocontrast(image, cutoff=5)
        except Exception:
            pass
        
        # For extremely poor quality scans, apply adaptive thresholding
        # to convert to pure black and white, eliminating gray noise
        try:
            img_array = np.array(image)
            # Use automatic threshold around median pixel value
            # This preserves text while removing faint noise
            threshold = np.median(img_array)
            # Adjust threshold slightly lower to preserve more text
            threshold = max(int(threshold - 20), 40)
            
            # Apply binary threshold: pixels > threshold become white, else black
            img_array = np.where(img_array > threshold, 255, 0).astype(np.uint8)
            from PIL import Image as PILImage
            image = PILImage.fromarray(img_array, mode="L")
        except Exception:
            # If thresholding fails, continue with current preprocessed image
            pass
        
        return image
    except Exception:
        # If any enhancement fails, return the image as-is
        return image


def extract_text(
    path: Path, 
    ocr_enabled: bool, 
    ocr_lang: str = "eng", 
    poppler_path: str | None = None,
    ocr_psm: str = "auto"
) -> ExtractionResult:
    """
    Extract text from various file formats.
    
    Args:
        path: Path to file
        ocr_enabled: Enable OCR for images and scanned PDFs
        ocr_lang: Tesseract language code (e.g., 'eng', 'pol', 'auto')
        poppler_path: Path to Poppler binaries
        ocr_psm: Page segmentation mode ('auto', 'single', 'multi-column', 'sparse')
    """
    suffix = path.suffix.lower()

    if suffix in _TEXT_EXTENSIONS:
        return _extract_text_file(path)
    if suffix == ".docx":
        return _extract_docx(path)
    if suffix == ".pdf":
        return _extract_pdf(path, ocr_enabled=ocr_enabled, ocr_lang=ocr_lang, poppler_path=poppler_path, ocr_psm=ocr_psm)
    if suffix in _IMAGE_EXTENSIONS:
        if not ocr_enabled:
            return ExtractionResult(
                source_path=path,
                text="",
                used_ocr=False,
                warnings=["Image input requires --ocr to be enabled."],
            )
        return _extract_image_ocr(path, ocr_lang=ocr_lang, ocr_psm=ocr_psm)

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


def _extract_pdf(path: Path, ocr_enabled: bool, ocr_lang: str, poppler_path: str | None = None, ocr_psm: str = "auto") -> ExtractionResult:
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
    
    # Check if extracted text is meaningful (not just whitespace/garbage)
    if _has_meaningful_text(text):
        return ExtractionResult(source_path=path, text=text, used_ocr=False)

    if not ocr_enabled:
        msg = "No readable text found in PDF (possibly scanned). Re-run with --ocr."
        if text:
            msg += f" (Extracted {len(text)} chars but insufficient readable content)"
        warnings.append(msg)
        return ExtractionResult(source_path=path, text="", used_ocr=False, warnings=warnings)

    # Fallback to OCR for scanned PDFs
    if text:
        warnings.append(f"PDF text extraction returned {len(text)} chars but insufficient readable content. Using OCR.")
    
    # Try OCRmyPDF first (better quality for PDFs)
    ocr_result = _extract_pdf_with_ocrmypdf(path, ocr_lang=ocr_lang, ocr_psm=ocr_psm)
    
    # If OCRmyPDF fails or is unavailable, fall back to pdf2image + pytesseract
    if not ocr_result.text.strip() or ocr_result.warnings:
        fallback_result = _extract_pdf_with_pytesseract(path, ocr_lang=ocr_lang, poppler_path=poppler_path, ocr_psm=ocr_psm)
        # Merge warnings from both attempts
        ocr_result.warnings.extend(fallback_result.warnings)
        # Use fallback text if OCRmyPDF produced nothing
        if not ocr_result.text.strip() and fallback_result.text.strip():
            ocr_result = fallback_result
    
    ocr_result.warnings.extend(warnings)
    return ocr_result


def _extract_pdf_with_ocrmypdf(path: Path, ocr_lang: str | None = None, ocr_psm: str = "auto") -> ExtractionResult:
    """
    Extract text from PDF using OCRmyPDF (preferred method for PDFs).
    OCRmyPDF adds a text layer to the PDF, preserving document structure.
    """
    import tempfile
    warnings: list[str] = []
    
    try:
        import ocrmypdf
    except ImportError:
        return ExtractionResult(
            source_path=path,
            text="",
            used_ocr=False,
            warnings=["ocrmypdf is not installed. Install with: pip install ocrmypdf"],
        )
    
    # Determine language for OCR
    current_lang = ocr_lang if ocr_lang and ocr_lang.lower() != "auto" else "eng"
    
    # Filter to available languages
    if current_lang:
        filtered = _filter_available_languages(current_lang)
        if filtered != current_lang and current_lang != "eng":
            warnings.append(f"Language(s) {current_lang} not available for OCRmyPDF. Using: {filtered}")
        current_lang = filtered
    
    # Create temporary output PDF
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
    
    try:
        # Run OCRmyPDF to add text layer
        ocrmypdf.ocr(
            str(path),
            str(tmp_path),
            language=current_lang,
            skip_text=False,  # OCR even if text exists
            force_ocr=True,   # Force OCR on all pages
            optimize=0,       # No optimization (faster)
            progress_bar=False,
            use_threads=True,
            tesseract_pagesegmode=_get_psm_value(ocr_psm),  # User-configurable PSM mode
        )
        
        # Extract text from OCR'd PDF
        try:
            from pypdf import PdfReader
        except ImportError:
            return ExtractionResult(
                source_path=path,
                text="",
                used_ocr=False,
                warnings=["pypdf is not installed."],
            )
        
        reader = PdfReader(tmp_path)
        extracted_pages = []
        for page in reader.pages:
            extracted_pages.append(page.extract_text() or "")
        
        text = "\n\n".join(extracted_pages).strip()
        
        if not text:
            warnings.append("OCRmyPDF completed but extracted no text")
        
        return ExtractionResult(
            source_path=path,
            text=text,
            used_ocr=True,
            warnings=warnings
        )
        
    except Exception as exc:
        warnings.append(f"OCRmyPDF failed: {str(exc)}")
        return ExtractionResult(
            source_path=path,
            text="",
            used_ocr=False,
            warnings=warnings
        )
    finally:
        # Clean up temporary file
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except:
                pass


def _get_psm_value(ocr_psm: str) -> int:
    """
    Convert user-friendly PSM mode to Tesseract PSM value.
    
    Args:
        ocr_psm: User-friendly mode name
        
    Returns:
        Tesseract PSM integer value
    """
    psm_mapping = {
        "auto": 3,          # Fully automatic page segmentation (good default)
        "single": 6,        # Single uniform block of text
        "multi-column": 3,  # Multiple columns (same as auto)
        "sparse": 11,       # Sparse text (find as much text as possible)
    }
    return psm_mapping.get(ocr_psm, 3)  # Default to auto (PSM 3)


def _build_tesseract_config(ocr_psm: str = "auto") -> str:
    """
    Build Tesseract config string. 
    TESSDATA_PREFIX env var handles the data directory location.
    """
    psm_value = _get_psm_value(ocr_psm)
    return f"--psm {psm_value} --oem 3"


def _build_tesseract_config_multicolumn(base_config: str = "--psm 3 --oem 3") -> str:
    """
    Build Tesseract config for multi-column layouts.
    
    PSM 3 = Fully automatic page segmentation (handles multi-column layouts better)
    OEM 3 = Default OCR Engine Mode (both legacy and LSTM)
    """
    return base_config


def _extract_pdf_with_pytesseract(path: Path, ocr_lang: str, poppler_path: str | None = None, ocr_psm: str = "auto") -> ExtractionResult:
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
        # Use higher DPI for better OCR accuracy (300 is standard for documents)
        if poppler_bin:
            images = convert_from_path(str(path), dpi=300, poppler_path=poppler_bin)
        else:
            images = convert_from_path(str(path), dpi=300)
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
    detected_lang: str | None = None
    
    try:
        for idx, image in enumerate(images, 1):
            # Apply aggressive preprocessing for better OCR on scanned documents
            image = _preprocess_image_for_ocr(image)
            
            # Use language detection if requested
            current_lang = ocr_lang
            if not ocr_lang or ocr_lang.lower() == "auto":
                if detected_lang is None:
                    # Quick OCR pass to get sample text for detection
                    sample_text = pytesseract.image_to_string(image, lang="eng", config=_build_tesseract_config("auto"))
                    if sample_text.strip():
                        detected_lang = _detect_languages(sample_text)
                        # Filter to only available languages
                        detected_lang = _filter_available_languages(detected_lang)
                        warnings.append(f"Auto-detected language(s): {detected_lang}")
                    else:
                        detected_lang = "eng"
                current_lang = detected_lang
            else:
                # Filter user-specified language(s) to available ones
                filtered = _filter_available_languages(current_lang)
                if filtered != current_lang:
                    warnings.append(f"Language(s) {current_lang} not available. Using: {filtered}")
                current_lang = filtered
            
            # Use configured PSM mode for image-based OCR
            page_text = pytesseract.image_to_string(
                image, 
                lang=current_lang,
                config=_build_tesseract_config(ocr_psm)
            )
            pages_text.append(page_text)
            
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
        # Use the detected language if auto-detection was used, otherwise use the specified one
        lang_used = detected_lang if detected_lang else ocr_lang
        warnings.append(
            f"OCR ran on {len(images)} page(s) but no text was recognized. "
            f"Check: 1) OCR language setting (current: {lang_used}), "
            "2) document quality/resolution, 3) document might be in a different language."
        )

    return ExtractionResult(source_path=path, text=text, used_ocr=True, warnings=warnings)


def _extract_image_ocr(path: Path, ocr_lang: str, ocr_psm: str = "auto") -> ExtractionResult:
    try:
        from PIL import Image, ImageEnhance
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
        
        # Upscale very small images (width < 800px) for better OCR
        # Tesseract requires adequate resolution to recognize text reliably
        if image.width < 800:
            scale_factor = max(2, 800 // image.width)
            new_width = image.width * scale_factor
            new_height = image.height * scale_factor
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Apply aggressive preprocessing for better OCR on scanned documents
        image = _preprocess_image_for_ocr(image)
        
        # Use language detection if requested
        current_lang = ocr_lang
        warnings: list[str] = []
        
        if not ocr_lang or ocr_lang.lower() == "auto":
            # Quick OCR pass with English to get sample text for detection
            sample_text = pytesseract.image_to_string(image, lang="eng", config=_build_tesseract_config("auto"))
            if sample_text.strip():
                current_lang = _detect_languages(sample_text)
                # Filter to only available languages
                current_lang = _filter_available_languages(current_lang)
                warnings.append(f"Auto-detected language(s): {current_lang}")
            else:
                current_lang = "eng"
        else:
            # Filter user-specified language(s) to available ones
            filtered = _filter_available_languages(ocr_lang)
            if filtered != ocr_lang:
                warnings.append(f"Language(s) {ocr_lang} not available. Using: {filtered}")
            current_lang = filtered
        
        text = pytesseract.image_to_string(
            image, 
            lang=current_lang,
            config=_build_tesseract_config(ocr_psm)
        )
        
        if not text.strip():
            return ExtractionResult(
                source_path=path,
                text="",
                used_ocr=True,
                warnings=[
                    f"OCR ran but no text was recognized. "
                    f"Check: 1) OCR language (current: {current_lang}), "
                    "2) image quality, 3) image might be in a different language."
                ],
            )
        
        return ExtractionResult(source_path=path, text=text, used_ocr=True, warnings=warnings)
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
