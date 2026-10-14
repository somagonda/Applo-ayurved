from __future__ import annotations

from datetime import date, timedelta

from ayurassist.repositories.booking_repository import BookingRepository
from ayurassist.repositories.slot_repository import SlotRepository


class AvailabilityService:
    def __init__(self, slots: SlotRepository, bookings: BookingRepository | None = None, today: date | None = None) -> None:
        self.slots = slots
        self.bookings = bookings
        self.today = today or date.today()

    def available_dates(self, doctor_id: str) -> list[date]:
        schedule = self.slots.schedule_for_doctor(doctor_id)
        result = []
        for offset in range(0, 8):
            candidate = self.today + timedelta(days=offset)
            if candidate.strftime("%a") in schedule:
                result.append(candidate)
        return result

    def available_times(self, doctor_id: str, appointment_date: date) -> list[str]:
        weekday = appointment_date.strftime("%a")
        times = list(self.slots.schedule_for_doctor(doctor_id).get(weekday, []))
        if self.bookings:
            confirmed_bookings = self.bookings.all()
        else:
            confirmed_bookings = []

        weekly_taken = set()
        for item in self.slots.booked_slots():
            same_doctor = item["doctor_id"] == doctor_id
            same_weekday = item["weekday"] == weekday
            if same_doctor and same_weekday:
                weekly_taken.add(item["time"])

        confirmed_taken = set()
        for item in confirmed_bookings:
            same_doctor = item["doctor_id"] == doctor_id
            same_date = item["date"] == appointment_date.isoformat()
            if same_doctor and same_date:
                confirmed_taken.add(item["time"])

        taken = weekly_taken | confirmed_taken
        available = []
        for time in times:
            if time not in taken:
                available.append(time)
        return available
