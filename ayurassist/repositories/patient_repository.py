from __future__ import annotations

from ayurassist.repositories.json_repository import JsonRepository


class PatientRepository:
    def __init__(self, store: JsonRepository) -> None:
        self.store = store

    def find(self, phone: str) -> dict | None:
        return self.store.read("patients.json").get(phone)
