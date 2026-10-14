from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re

from ayurassist.domain.enums import BookingStep
from ayurassist.domain.models import Session
from ayurassist.services.availability_service import AvailabilityService
from ayurassist.services.booking_service import BookingService
from ayurassist.services.matching_service import MatchingService, normalize
from ayurassist.services.patient_service import PatientService
from ayurassist.repositories.clinic_repository import ClinicRepository
from ayurassist.tools.results import ToolResult


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    argument_name: str
    argument_description: str


class BookingToolbox:
    """Python tools exposed to the agents.

    This is the main live-change file. Each public method below maps to one
    booking step from the assignment.
    """

    def __init__(
        self,
        session: Session,
        patients: PatientService,
        clinics: ClinicRepository,
        availability: AvailabilityService,
        bookings: BookingService,
        matcher: MatchingService,
    ) -> None:
        self.session = session
        self.patients = patients
        self.clinics = clinics
        self.availability = availability
        self.bookings = bookings
        self.matcher = matcher

    def specs_for_current_agent(self) -> list[ToolSpec]:
        specs = {
            BookingStep.IDENTIFY: ToolSpec(
                "find_patient",
                "Find or register a patient by phone.",
                "phone_or_name",
                "Phone number, or a name if the phone was unknown.",
            ),
            BookingStep.CITY: ToolSpec(
                "select_city",
                "Validate the requested city.",
                "city",
                "City requested by the user.",
            ),
            BookingStep.CENTRE: ToolSpec(
                "select_centre",
                "Validate the requested centre.",
                "centre",
                "Centre requested by the user.",
            ),
            BookingStep.DOCTOR: ToolSpec(
                "select_doctor",
                "Validate the requested doctor.",
                "doctor",
                "Doctor requested by the user.",
            ),
            BookingStep.DATE: ToolSpec(
                "select_date",
                "Validate the requested date.",
                "date_text",
                "Date requested by the user.",
            ),
            BookingStep.TIME: ToolSpec(
                "select_time_slot",
                "Validate the requested time slot.",
                "time_text",
                "Time requested by the user.",
            ),
            BookingStep.CONFIRM: ToolSpec(
                "confirm_booking",
                "Save the booking only after explicit confirmation.",
                "confirmation",
                "User confirmation text.",
            ),
        }
        if self.session.step in specs:
            return [specs[self.session.step]]
        return []

    def call(self, name: str, argument: str) -> ToolResult:
        if name == "find_patient":
            return self.find_patient(argument)
        if name == "select_city":
            return self.select_city(argument)
        if name == "select_centre":
            return self.select_centre(argument)
        if name == "select_doctor":
            return self.select_doctor(argument)
        if name == "select_date":
            return self.select_date(argument)
        if name == "select_time_slot":
            return self.select_time_slot(argument)
        if name == "confirm_booking":
            return self.confirm_booking(argument)
        raise ValueError(f"Unknown tool: {name}")

    # IdentifyAgent step
    def find_patient(self, phone_or_name: str) -> ToolResult:
        text = phone_or_name.strip()
        if self.session.pending_phone is not None:
            if not self._is_valid_name(text):
                return ToolResult("Please enter a valid name using letters only.")
            phone = self.session.pending_phone
            self.session.patient = self.patients.find_or_register(phone, text)
            self.session.pending_phone = None
            self.session.step = BookingStep.CITY
            cities = ", ".join(self.clinics.cities())
            return ToolResult(f"Thanks, {text}. Which city would you like to visit? We have {cities}.")

        if text.isdigit() and len(text) != 10:
            return ToolResult("Please enter a valid 10-digit mobile number.")

        if text.isdigit() and len(text) == 10:
            patient = self.patients.find_or_register(text)
            if not patient:
                self.session.pending_phone = text
                return ToolResult("I could not find that mobile number. May I have your name?")
            self.session.patient = patient
            self.session.step = BookingStep.CITY
            cities = ", ".join(self.clinics.cities())
            return ToolResult(f"Welcome back, {patient.name}. Which city would you like to visit? We have {cities}.")

        if self.session.patient is None and self.session.pending_phone is None:
            return ToolResult("Please enter your registered 10-digit mobile number first.")

        return ToolResult("May I have your registered 10-digit mobile number?")

    # BookingAgent steps
    def select_city(self, city: str) -> ToolResult:
        match = self._match_or_escalate(city, self.clinics.cities())
        if not match:
            return self._retry("city", self.clinics.cities())
        self.session.choices.city = match
        self.session.step = BookingStep.CENTRE
        self.session.miss_count = 0
        centres = self.clinics.centres_for_city(match)
        return ToolResult(f"{match} has {len(centres)} centre(s): {', '.join(centres)}. Which one?")

    def select_centre(self, centre: str) -> ToolResult:
        city = self._require(self.session.choices.city, "Please choose a city first.")
        if isinstance(city, ToolResult):
            return city
        centres = self.clinics.centres_for_city(city)
        match = self._match_or_escalate(centre, centres)
        if not match:
            return self._retry("centre", centres)
        self.session.choices.centre = match
        self.session.step = BookingStep.DOCTOR
        self.session.miss_count = 0
        doctors = self.clinics.doctors_for_centre(city, match)
        doctor_labels = []
        for doctor in doctors:
            doctor_labels.append(f"{doctor.name} ({doctor.speciality})")
        options = ", ".join(doctor_labels)
        return ToolResult(f"At {match} you can see {options}. Which doctor would you prefer?")

    def select_doctor(self, doctor: str) -> ToolResult:
        city = self._require(self.session.choices.city, "Please choose a city first.")
        centre = self._require(self.session.choices.centre, "Please choose a centre first.")
        if isinstance(city, ToolResult):
            return city
        if isinstance(centre, ToolResult):
            return centre
        doctors = self.clinics.doctors_for_centre(city, centre)
        doctor_options = {}
        for item in doctors:
            doctor_options[item.name] = item
        match = self._match_or_escalate(doctor, doctor_options.keys())
        if not match:
            return self._retry("doctor", doctor_options.keys())
        selected = doctor_options[match]
        self.session.choices.doctor_id = selected.id
        self.session.choices.doctor_name = selected.name
        self.session.step = BookingStep.DATE
        self.session.miss_count = 0
        options = []
        for item in self._available_dates_with_times(selected.id):
            options.append(item.strftime("%a %d %b"))
        if not options:
            return self._transfer()
        return ToolResult(f"{selected.name} is available on {', '.join(options)}. Which date works for you?")

    def select_date(self, date_text: str) -> ToolResult:
        doctor_id = self._require(self.session.choices.doctor_id, "Please choose a doctor first.")
        if isinstance(doctor_id, ToolResult):
            return doctor_id
        dates = self._available_dates_with_times(doctor_id)
        labels = {}
        iso_labels = {}
        for item in dates:
            labels[item.strftime("%a %d %b")] = item
            iso_labels[item.isoformat()] = item
        match = self._match_date(date_text, labels, iso_labels)
        if not match:
            self.session.miss_count += 1
            if self.session.miss_count >= 2:
                return self._transfer()
            return ToolResult(f"I could not match that date. Please choose one of: {', '.join(labels.keys())}.")
        selected_date = labels.get(match) or iso_labels[match]
        self.session.choices.date = selected_date
        self.session.step = BookingStep.TIME
        self.session.miss_count = 0
        times = self.availability.available_times(doctor_id, selected_date)
        formatted_date = selected_date.strftime("%a %d %b")
        return ToolResult(f"For {formatted_date}, available times are {', '.join(times)}. Which time would you like?")

    def select_time_slot(self, time_text: str) -> ToolResult:
        doctor_id = self._require(self.session.choices.doctor_id, "Please choose a doctor first.")
        appointment_date = self._require(self.session.choices.date, "Please choose a date first.")
        if isinstance(doctor_id, ToolResult):
            return doctor_id
        if isinstance(appointment_date, ToolResult):
            return appointment_date
        times = self.availability.available_times(doctor_id, appointment_date)
        match = self._match_time(time_text, times)
        if not match:
            return self._retry("time", times)
        self.session.choices.time = match
        self.session.step = BookingStep.CONFIRM
        self.session.miss_count = 0
        summary = self._summary()
        return ToolResult(f"Please confirm this booking: {summary}. Reply yes to confirm or no to cancel.")

    def confirm_booking(self, confirmation: str) -> ToolResult:
        normalized = confirmation.strip().lower()
        if normalized not in {"yes", "y", "confirm", "confirmed", "ok", "okay"}:
            self.session.step = BookingStep.COMPLETE
            self.session.ended = True
            return ToolResult("No problem, I have not saved the booking. You can start again when ready.")
        try:
            booking = self.bookings.save(self.session)
        except ValueError as error:
            return self._handle_save_error(str(error))
        self.session.step = BookingStep.COMPLETE
        self.session.ended = True
        return ToolResult(f"Booked: {booking['doctor_name']}, {booking['centre']}, {booking['date']}, {booking['time']}. Thank you.")

    # Shared helpers and guardrails
    def _match_or_escalate(self, user_text: str, options) -> str | None:
        return self.matcher.best_match(user_text, options)

    def _retry(self, label: str, options) -> ToolResult:
        self.session.miss_count += 1
        if self.session.miss_count >= 2:
            return self._transfer()
        return ToolResult(f"I could not match that {label}. Please choose one of: {', '.join(options)}.")

    def _transfer(self) -> ToolResult:
        self.session.step = BookingStep.TRANSFERRED
        self.session.ended = True
        return ToolResult("I will connect you to a person now.\n[TRANSFER TO HUMAN]", transferred=True)

    def _handle_save_error(self, message: str) -> ToolResult:
        choices = self.session.choices
        choices.time = None
        self.session.step = BookingStep.TIME
        self.session.miss_count = 0

        if not choices.doctor_id or not choices.date:
            return ToolResult(message)

        times = self.availability.available_times(choices.doctor_id, choices.date)
        if not times:
            return ToolResult(f"{message} I do not see any other times for this date.")
        return ToolResult(f"{message} Available times are {', '.join(times)}. Which time would you like?")

    def _match_time(self, user_text: str, options: list[str]) -> str | None:
        text = user_text.strip().lower().replace(".", ":")
        if text in options:
            return text

        if text.isdigit():
            hour = int(text)
            exact_hour = f"{hour:02d}:00"
            if exact_hour in options:
                return exact_hour
            hour_matches = []
            for option in options:
                if option.startswith(f"{hour:02d}:"):
                    hour_matches.append(option)
            if len(hour_matches) == 1:
                return hour_matches[0]
            return None

        parts = text.split(":")
        parts_are_digits = True
        for part in parts:
            if not part.isdigit():
                parts_are_digits = False
        if len(parts) == 2 and parts_are_digits:
            hour = int(parts[0])
            minute = int(parts[1])
            normalized = f"{hour:02d}:{minute:02d}"
            if normalized in options:
                return normalized
            return None

        return None

    def _is_valid_name(self, user_text: str) -> bool:
        text = user_text.strip()
        if not text:
            return False
        for character in text:
            if not character.isalpha() and not character.isspace():
                return False
        return True

    def _match_date(self, user_text: str, labels: dict[str, date], iso_labels: dict[str, date]) -> str | None:
        normalized_input = normalize(user_text)
        for label in list(labels) + list(iso_labels):
            if normalized_input == normalize(label):
                return label
        day_only_match = self._match_day_only(normalized_input, labels)
        if day_only_match:
            return day_only_match
        for label, appointment_date in labels.items():
            if self._date_parts_match(normalized_input, appointment_date):
                return label
        return None

    def _match_day_only(self, normalized_input: str, labels: dict[str, date]) -> str | None:
        if not normalized_input.isdigit():
            return None
        matches = []
        for label, appointment_date in labels.items():
            if str(appointment_date.day) == normalized_input:
                matches.append(label)
        if len(matches) == 1:
            return matches[0]
        return None

    def _date_parts_match(self, normalized_input: str, appointment_date: date) -> bool:
        tokens = normalized_input.split()
        if not tokens:
            return False

        day = str(appointment_date.day)
        weekday = appointment_date.strftime("%a").lower()
        month = appointment_date.strftime("%b").lower()
        has_day = day in tokens
        has_weekday = False
        has_month = False
        for token in tokens:
            if token.isdigit():
                continue
            if weekday.startswith(token) or token.startswith(weekday):
                has_weekday = True
            if month.startswith(token) or token.startswith(month):
                has_month = True
        has_year = str(appointment_date.year) in tokens

        if has_year:
            return has_day and (has_month or has_weekday)
        return has_day and (has_month or has_weekday) and bool(re.search(r"[a-z]", normalized_input))

    def _require(self, value, message: str):
        if value is None:
            return ToolResult(message)
        return value

    def _available_dates_with_times(self, doctor_id: str) -> list[date]:
        available_dates = []
        for item in self.availability.available_dates(doctor_id):
            if self.availability.available_times(doctor_id, item):
                available_dates.append(item)
        return available_dates

    def _summary(self) -> str:
        choices = self.session.choices
        if isinstance(choices.date, date):
            formatted_date = choices.date.strftime("%a %d %b")
        else:
            formatted_date = choices.date
        return f"{choices.doctor_name}, {choices.centre}, {formatted_date}, {choices.time}"
