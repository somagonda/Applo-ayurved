from __future__ import annotations

from datetime import date

from ayurassist.domain.models import Session
from ayurassist.repositories.booking_repository import BookingRepository


class BookingService:
    def __init__(self, bookings: BookingRepository) -> None:
        self.bookings = bookings

    def save(self, session: Session) -> dict:
        if not session.patient:
            raise ValueError("Cannot save a booking without a patient.")
        choices = session.choices

        booking_is_complete = True
        required_values = [choices.city, choices.centre, choices.doctor_id, choices.date, choices.time]
        for value in required_values:
            if not value:
                booking_is_complete = False

        if not booking_is_complete:
            raise ValueError("Cannot save an incomplete booking.")

        if isinstance(choices.date, date):
            booking_date = choices.date.isoformat()
        else:
            booking_date = choices.date

        booking = {
            "patient_phone": session.patient.phone,
            "patient_name": session.patient.name,
            "city": choices.city,
            "centre": choices.centre,
            "doctor_id": choices.doctor_id,
            "doctor_name": choices.doctor_name,
            "date": booking_date,
            "time": choices.time,
        }
        if self._already_booked(booking):
            raise ValueError("That slot is no longer available.")
        self.bookings.append(booking)
        return booking

    def _already_booked(self, booking: dict) -> bool:
        for existing in self.bookings.all():
            same_doctor = existing["doctor_id"] == booking["doctor_id"]
            same_date = existing["date"] == booking["date"]
            same_time = existing["time"] == booking["time"]
            if same_doctor and same_date and same_time:
                return True
        return False
