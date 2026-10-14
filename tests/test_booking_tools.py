from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import shutil

from ayurassist.application.conversation_manager import ConversationManager
from ayurassist.llm.offline_demo_model import OfflineDemoModel
from ayurassist.repositories.booking_repository import BookingRepository
from ayurassist.repositories.clinic_repository import ClinicRepository
from ayurassist.repositories.json_repository import JsonRepository
from ayurassist.repositories.patient_repository import PatientRepository
from ayurassist.repositories.slot_repository import SlotRepository
from ayurassist.services.availability_service import AvailabilityService
from ayurassist.services.booking_service import BookingService
from ayurassist.services.matching_service import MatchingService
from ayurassist.services.patient_service import PatientService
from ayurassist.tools.toolbox import BookingToolbox
from ayurassist.domain.models import Session
from ayurassist.domain.enums import BookingStep


def copy_data(tmp_path: Path) -> Path:
    source = Path(__file__).resolve().parents[1] / "data"
    destination = tmp_path / "data"
    shutil.copytree(source, destination)
    (destination / "bookings.json").write_text("[]\n", encoding="utf-8")
    return destination


def make_toolbox(data_dir: Path, today: date = date(2026, 10, 6)) -> BookingToolbox:
    store = JsonRepository(data_dir)
    booking_repository = BookingRepository(store)
    return BookingToolbox(
        session=Session(),
        patients=PatientService(PatientRepository(store)),
        clinics=ClinicRepository(store),
        availability=AvailabilityService(SlotRepository(store), booking_repository, today=today),
        bookings=BookingService(booking_repository),
        matcher=MatchingService(),
    )


def test_city_tool_accepts_typo_and_moves_to_centre(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    tools.find_patient("4444444441")
    result = tools.select_city("banglore")

    assert "Whitefield" in result.message
    assert tools.session.choices.city == "Bengaluru"


def test_identify_rejects_non_ten_digit_number(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    invalid_numbers = ["123456789", "854456768976", "987654567878888"]

    for number in invalid_numbers:
        result = tools.find_patient(number)

        assert "10-digit mobile number" in result.message
        assert tools.session.patient is None
        assert tools.session.pending_phone is None


def test_identify_rejects_name_before_valid_unknown_phone(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    result = tools.find_patient("dfcvghjkjhgfd")

    assert "10-digit mobile number first" in result.message
    assert tools.session.patient is None


def test_unknown_ten_digit_number_registers_name_in_session(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    first = tools.find_patient("8544567890")
    second = tools.find_patient("Somagonda")

    assert "May I have your name" in first.message
    assert "Thanks, Somagonda" in second.message
    assert tools.session.patient is not None
    assert tools.session.patient.phone == "8544567890"


def test_pending_unknown_phone_rejects_number_as_name(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    tools.find_patient("8544567890")
    result = tools.find_patient("2345678765432")

    assert "letters only" in result.message
    assert tools.session.patient is None
    assert tools.session.pending_phone == "8544567890"


def test_pending_unknown_phone_rejects_mixed_letters_and_numbers_as_name(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    tools.find_patient("8544567890")
    result = tools.find_patient("2345sdfg")

    assert "letters only" in result.message
    assert tools.session.patient is None
    assert tools.session.pending_phone == "8544567890"


def test_pending_unknown_phone_rejects_empty_name(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    tools.find_patient("8544567890")
    result = tools.find_patient("   ")

    assert "letters only" in result.message
    assert tools.session.patient is None
    assert tools.session.pending_phone == "8544567890"


def test_only_current_step_tool_is_exposed(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    expected = {
        BookingStep.IDENTIFY: "find_patient",
        BookingStep.CITY: "select_city",
        BookingStep.CENTRE: "select_centre",
        BookingStep.DOCTOR: "select_doctor",
        BookingStep.DATE: "select_date",
        BookingStep.TIME: "select_time_slot",
        BookingStep.CONFIRM: "confirm_booking",
    }

    for step, tool_name in expected.items():
        tools.session.step = step
        specs = tools.specs_for_current_agent()
        assert [spec.name for spec in specs] == [tool_name]


def test_centre_step_requires_city_first(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    result = tools.select_centre("Jayanagar")

    assert "choose a city first" in result.message
    assert tools.session.choices.centre is None


def test_doctor_step_requires_centre_first(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    tools.session.choices.city = "Bengaluru"
    result = tools.select_doctor("Geeta")

    assert "choose a centre first" in result.message
    assert tools.session.choices.doctor_id is None


def test_taken_slot_is_not_offered(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    tools.find_patient("4444444441")
    tools.select_city("Bengaluru")
    tools.select_centre("Jayanagar")
    tools.select_doctor("Geeta")
    tools.select_date("Fri 09 Oct")

    result = tools.select_time_slot("10:00")

    assert "could not match" in result.message


def test_iso_date_input_is_accepted(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    tools.find_patient("4444444441")
    tools.select_city("Bengaluru")
    tools.select_centre("Jayanagar")
    tools.select_doctor("Geeta")
    result = tools.select_date("2026-10-09")

    assert "For Fri 09 Oct" in result.message
    assert "10:30" in result.message
    assert tools.session.choices.date == date(2026, 10, 9)
    assert tools.session.step == BookingStep.TIME


def test_date_accepts_weekday_and_day_without_month(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    tools.find_patient("4444444441")
    tools.select_city("Pune")
    tools.select_centre("Kothrud")
    tools.select_doctor("Neha")
    result = tools.select_date("tue 13")

    assert "12:00" in result.message
    assert tools.session.choices.date == date(2026, 10, 13)
    assert tools.session.step == BookingStep.TIME


def test_date_accepts_day_and_month_without_weekday(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    tools.find_patient("4444444441")
    tools.select_city("Pune")
    tools.select_centre("Kothrud")
    tools.select_doctor("Neha")
    result = tools.select_date("13 oct")

    assert "12:00" in result.message
    assert tools.session.choices.date == date(2026, 10, 13)
    assert tools.session.step == BookingStep.TIME


def test_date_accepts_unique_day_number(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir, today=date(2026, 10, 12))

    tools.find_patient("4444444441")
    tools.select_city("Kochi")
    tools.select_centre("Kadavanthra")
    tools.select_doctor("Rahul")
    result = tools.select_date("19")

    assert "17:00" in result.message
    assert tools.session.choices.date == date(2026, 10, 19)
    assert tools.session.step == BookingStep.TIME


def test_date_with_no_remaining_times_is_not_offered_or_accepted(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    bookings_path = data_dir / "bookings.json"
    bookings_path.write_text(
        json.dumps(
            [
                {
                    "patient_phone": "4444444442",
                    "patient_name": "Ravi Kumar",
                    "city": "Bengaluru",
                    "centre": "Jayanagar",
                    "doctor_id": "D4",
                    "doctor_name": "Dr. Geeta Rao",
                    "date": "2026-10-09",
                    "time": "10:30",
                },
                {
                    "patient_phone": "4444444443",
                    "patient_name": "Fatima Shaikh",
                    "city": "Bengaluru",
                    "centre": "Jayanagar",
                    "doctor_id": "D4",
                    "doctor_name": "Dr. Geeta Rao",
                    "date": "2026-10-09",
                    "time": "11:00",
                },
            ],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    tools = make_toolbox(data_dir)

    tools.find_patient("4444444441")
    tools.select_city("Bengaluru")
    tools.select_centre("Jayanagar")
    doctor_result = tools.select_doctor("Geeta")
    date_result = tools.select_date("Fri 09 Oct")

    assert "Fri 09 Oct" not in doctor_result.message
    assert "could not match that date" in date_result.message
    assert tools.session.step == BookingStep.DATE
    assert tools.session.choices.date is None


def test_single_available_hour_can_be_entered_without_minutes(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    tools.find_patient("4444444441")
    tools.select_city("Bengaluru")
    tools.select_centre("Jayanagar")
    tools.select_doctor("Geeta")
    tools.select_date("Tue 13 Oct")

    result = tools.select_time_slot("11")

    assert "Please confirm" in result.message
    assert tools.session.choices.time == "11:00"


def test_time_with_single_digit_hour_and_minutes_is_normalized(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    tools.find_patient("4444444441")
    tools.select_city("Bengaluru")
    tools.select_centre("Whitefield")
    tools.select_doctor("Kavya")
    tools.select_date("Tue 06 Oct")

    result = tools.select_time_slot("9:30")

    assert "Please confirm" in result.message
    assert tools.session.choices.time == "09:30"


def test_single_available_time_accepts_dot_format(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    tools.find_patient("4444444441")
    tools.select_city("Bengaluru")
    tools.select_centre("Jayanagar")
    tools.select_doctor("Geeta")
    tools.select_date("Tue 13 Oct")

    result = tools.select_time_slot("11.0")

    assert "Please confirm" in result.message
    assert tools.session.choices.time == "11:00"


def test_confirmed_booking_removes_slot_from_future_availability(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    tools.find_patient("4444444441")
    tools.select_city("Bengaluru")
    tools.select_centre("Jayanagar")
    tools.select_doctor("Geeta")
    tools.select_date("Fri 09 Oct")
    tools.select_time_slot("10:30")
    tools.confirm_booking("yes")

    next_tools = make_toolbox(data_dir)
    next_tools.find_patient("4444444442")
    next_tools.select_city("Bengaluru")
    next_tools.select_centre("Jayanagar")
    next_tools.select_doctor("Geeta")
    result = next_tools.select_date("Fri 09 Oct")

    assert "11:00" in result.message
    assert "10:30" not in result.message


def test_duplicate_booking_is_rejected_at_confirmation(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    first = make_toolbox(data_dir)
    second = make_toolbox(data_dir)

    for tools, phone in [(first, "4444444441"), (second, "4444444442")]:
        tools.find_patient(phone)
        tools.select_city("Bengaluru")
        tools.select_centre("Jayanagar")
        tools.select_doctor("Geeta")
        tools.select_date("Fri 09 Oct")
        tools.session.choices.time = "10:30"

    first.confirm_booking("yes")
    result = second.confirm_booking("yes")

    assert "no longer available" in result.message
    assert "Available times" in result.message
    assert second.session.step == BookingStep.TIME
    assert second.session.choices.time is None


def test_whole_hour_prefers_exact_zero_minute_slot(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    tools.find_patient("4444444441")
    tools.select_city("Pune")
    tools.select_centre("Kothrud")
    tools.select_doctor("Neha")
    tools.select_date("Tue 06 Oct")

    result = tools.select_time_slot("12")

    assert "Please confirm" in result.message
    assert tools.session.choices.time == "12:00"
    assert tools.session.step == BookingStep.CONFIRM
    assert tools.session.miss_count == 0


def test_time_accepts_single_digit_minute_format(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    tools.find_patient("4444444441")
    tools.select_city("Pune")
    tools.select_centre("Aundh")
    tools.select_doctor("Vikram")
    tools.select_date("Wed 07 Oct")
    result = tools.select_time_slot("11:0")

    assert "Please confirm" in result.message
    assert tools.session.choices.time == "11:00"


def test_two_bad_time_answers_transfer_to_human(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    tools.find_patient("4444444441")
    tools.select_city("Bengaluru")
    tools.select_centre("Jayanagar")
    tools.select_doctor("Geeta")
    tools.select_date("Tue 13 Oct")
    first = tools.select_time_slot("08:00")
    second = tools.select_time_slot("18:00")

    assert "could not match" in first.message
    assert "[TRANSFER TO HUMAN]" in second.message
    assert second.transferred is True
    assert tools.session.ended is True


def test_negative_confirmation_does_not_save_booking(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    tools.find_patient("4444444441")
    tools.select_city("Bengaluru")
    tools.select_centre("Jayanagar")
    tools.select_doctor("Geeta")
    tools.select_date("Fri 09 Oct")
    tools.select_time_slot("10:30")
    result = tools.confirm_booking("no")

    assert "not saved" in result.message
    assert JsonRepository(data_dir).read("bookings.json") == []
    assert tools.session.step == BookingStep.COMPLETE
    assert tools.session.ended is True


def test_confirmation_accepts_case_and_whitespace(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    tools = make_toolbox(data_dir)

    tools.find_patient("4444444441")
    tools.select_city("Bengaluru")
    tools.select_centre("Jayanagar")
    tools.select_doctor("Geeta")
    tools.select_date("Fri 09 Oct")
    tools.select_time_slot("10:30")
    result = tools.confirm_booking("  OKAY  ")

    assert "Booked" in result.message
    assert tools.session.step == BookingStep.COMPLETE
    assert tools.session.ended is True


def test_conversation_happy_path(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    app = ConversationManager(data_dir, OfflineDemoModel(), today=date(2026, 10, 6))

    assert "Welcome back, Anita" in app.handle_user_message("4444444441")
    assert "Jayanagar" in app.handle_user_message("banglore")
    assert "Dr. Geeta Rao" in app.handle_user_message("jaynagar")
    assert "Fri 09 Oct" in app.handle_user_message("geeta")
    assert "10:30" in app.handle_user_message("Fri 09 Oct")
    assert "Please confirm" in app.handle_user_message("10:30")
    assert "Booked" in app.handle_user_message("yes")


def test_conversation_escalates_after_two_bad_step_answers(tmp_path: Path) -> None:
    data_dir = copy_data(tmp_path)
    app = ConversationManager(data_dir, OfflineDemoModel())

    app.handle_user_message("4444444441")
    first = app.handle_user_message("Atlantis")
    second = app.handle_user_message("Moon")

    assert "could not match" in first
    assert "[TRANSFER TO HUMAN]" in second
    assert app.session.ended is True
