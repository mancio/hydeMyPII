from __future__ import annotations

from pathlib import Path

from hydemypii.detector import detect_entities
from hydemypii.faker_engine import FakeDataEngine
from hydemypii.types import ExtractionResult, RedactionResult


class PIIRedactor:
    def __init__(self, locale: str = "en_US") -> None:
        self._fake_data = FakeDataEngine(locale=locale)

    def redact(self, extraction: ExtractionResult, output_dir: Path) -> RedactionResult:
        source_text = extraction.text
        entities = detect_entities(source_text)

        chunks: list[str] = []
        cursor = 0
        replacements = 0
        for entity in entities:
            chunks.append(source_text[cursor:entity.start])
            fake_value = self._fake_data.fake_value(entity.entity_type, entity.value)
            chunks.append(fake_value)
            cursor = entity.end
            replacements += 1

        chunks.append(source_text[cursor:])
        redacted_text = "".join(chunks)

        output_dir.mkdir(parents=True, exist_ok=True)
        out_name = f"{extraction.source_path.stem}.sanitized.txt"
        output_path = output_dir / out_name
        output_path.write_text(redacted_text, encoding="utf-8")

        return RedactionResult(
            source_path=extraction.source_path,
            output_path=output_path,
            replaced_text=redacted_text,
            replacements_count=replacements,
            entities_count=self._fake_data.count_by_entity,
            used_ocr=extraction.used_ocr,
            warnings=list(extraction.warnings),
        )
