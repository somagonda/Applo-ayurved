from __future__ import annotations

from ayurassist.domain.models import Doctor
from ayurassist.repositories.json_repository import JsonRepository


class ClinicRepository:
    def __init__(self, store: JsonRepository) -> None:
        self.store = store

    def all(self) -> dict:
        return self.store.read("centres.json")

    def cities(self) -> list[str]:
        return list(self.all().keys())

    def centres_for_city(self, city: str) -> list[str]:
        return list(self.all()[city].keys())

    def doctors_for_centre(self, city: str, centre: str) -> list[Doctor]:
        doctors = []
        for doctor in self.all()[city][centre]:
            doctors.append(Doctor(**doctor))
        return doctors
