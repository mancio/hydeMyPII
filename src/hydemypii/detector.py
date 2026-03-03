from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(slots=True)
class EntityMatch:
    entity_type: str
    value: str
    start: int
    end: int


_ENTITY_PATTERNS: dict[str, re.Pattern[str]] = {
    "pesel": re.compile(r"\b\d{3}-\d{3}-\d{4}[xX]?\d{5}\b|\b\d{11}\b"),
    "date": re.compile(r"\b\d{1,2}[-/.]\d{1,2}[-/.]\d{4}\b|\b\d{4}[-/.]\d{1,2}[-/.]\d{1,2}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"\b(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)\d{3,4}[\s.-]?\d{3,4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    "ipv4": re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"),
    "iban": re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"),
    "person_name": re.compile(r"\b[A-Z][A-Z]{2,}\b"),
}


def detect_entities(text: str) -> list[EntityMatch]:
    matches: list[EntityMatch] = []
    for entity_type, pattern in _ENTITY_PATTERNS.items():
        for hit in pattern.finditer(text):
            matches.append(
                EntityMatch(
                    entity_type=entity_type,
                    value=hit.group(0),
                    start=hit.start(),
                    end=hit.end(),
                )
            )

    matches.sort(key=lambda item: (item.start, -(item.end - item.start)))

    merged: list[EntityMatch] = []
    last_end = -1
    for match in matches:
        if match.start < last_end:
            continue
        merged.append(match)
        last_end = match.end

    return merged
