from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class ExtractionResult:
    source_path: Path
    text: str
    used_ocr: bool = False
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RedactionResult:
    source_path: Path
    output_path: Path
    replaced_text: str
    replacements_count: int
    entities_count: dict[str, int]
    used_ocr: bool = False
    warnings: list[str] = field(default_factory=list)
