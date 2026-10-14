from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from ayurassist.domain.enums import BookingStep


@dataclass
class Patient:
    phone: str
    name: str
    preferred_city: str | None = None
    is_registered_now: bool = False


@dataclass
class Doctor:
    id: str
    name: str
    speciality: str


@dataclass
class AppointmentChoice:
    city: str | None = None
    centre: str | None = None
    doctor_id: str | None = None
    doctor_name: str | None = None
    date: date | None = None
    time: str | None = None


@dataclass
class Session:
    patient: Patient | None = None
    pending_phone: str | None = None
    step: BookingStep = BookingStep.IDENTIFY
    choices: AppointmentChoice = field(default_factory=AppointmentChoice)
    miss_count: int = 0
    ended: bool = False
