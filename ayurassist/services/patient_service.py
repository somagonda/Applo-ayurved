from __future__ import annotations

from ayurassist.domain.models import Patient
from ayurassist.repositories.patient_repository import PatientRepository


class PatientService:
    def __init__(self, patients: PatientRepository) -> None:
        self.patients = patients

    def find_or_register(self, phone: str, name: str | None = None) -> Patient | None:
        known = self.patients.find(phone)
        if known:
            return Patient(
                phone=phone,
                name=known["name"],
                preferred_city=known.get("preferred_city"),
            )
        if name:
            return Patient(phone=phone, name=name, is_registered_now=True)
        return None
