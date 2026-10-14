from __future__ import annotations

from ayurassist.repositories.json_repository import JsonRepository


class SlotRepository:
    def __init__(self, store: JsonRepository) -> None:
        self.store = store

    def all(self) -> dict:
        return self.store.read("slots.json")

    def schedule_for_doctor(self, doctor_id: str) -> dict[str, list[str]]:
        return self.all().get(doctor_id, {})

    def booked_slots(self) -> list[dict]:
        return self.all().get("booked", [])
