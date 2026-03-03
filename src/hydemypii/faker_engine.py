from __future__ import annotations

from collections import defaultdict

from faker import Faker


class FakeDataEngine:
    def __init__(self, locale: str = "en_US") -> None:
        self._faker = Faker(locale)
        self._cache: dict[tuple[str, str], str] = {}
        self._count_by_entity: dict[str, int] = defaultdict(int)

    @property
    def count_by_entity(self) -> dict[str, int]:
        return dict(self._count_by_entity)

    def fake_value(self, entity_type: str, original_value: str) -> str:
        cache_key = (entity_type, original_value)
        if cache_key in self._cache:
            return self._cache[cache_key]

        generated = self._generate(entity_type)
        self._cache[cache_key] = generated
        self._count_by_entity[entity_type] += 1
        return generated

    def _generate(self, entity_type: str) -> str:
        if entity_type == "email":
            return self._faker.email()
        if entity_type == "phone":
            return self._faker.phone_number()
        if entity_type == "ssn":
            return self._faker.ssn()
        if entity_type == "credit_card":
            return self._faker.credit_card_number()
        if entity_type == "ipv4":
            return self._faker.ipv4_private()
        if entity_type == "iban":
            return self._faker.iban()
        if entity_type == "pesel":
            return "".join(self._faker.random_choices("0123456789", length=11))
        if entity_type == "date":
            return self._faker.date(pattern="%d-%m-%Y")
        if entity_type == "person_name":
            return self._faker.last_name().upper()
        return self._faker.word()
