from __future__ import annotations

from datetime import date
from pathlib import Path

from ayurassist.application.agent_router import AgentRouter
from ayurassist.domain.models import Session
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


class ConversationManager:
    """Manages the chat.

    It stores the conversation history, keeps the current session, picks the
    current agent, and sends the user message to the model/tools.
    """

    def __init__(self, data_dir: Path, model, today: date | None = None) -> None:
        store = JsonRepository(data_dir)
        booking_repository = BookingRepository(store)
        self.session = Session()
        self.history: list[dict] = []
        self.router = AgentRouter()
        self.model = model
        self.toolbox = BookingToolbox(
            session=self.session,
            patients=PatientService(PatientRepository(store)),
            clinics=ClinicRepository(store),
            availability=AvailabilityService(SlotRepository(store), booking_repository, today=today),
            bookings=BookingService(booking_repository),
            matcher=MatchingService(),
        )

    def start_message(self) -> str:
        return (
            "Namaste! Welcome to Apollo AyurVAID. 🌿\n\n"
            "I can help you find a centre, choose a doctor,\n"
            "and book your consultation.\n\n"
            "To get started, may I have your registered\n"
            "mobile number?"
        )

    def handle_user_message(self, text: str) -> str:
        self.history.append({"role": "user", "content": text})
        agent = self.router.current_agent(self.session)
        answer = self.model.reply(agent, self.history, self.toolbox)
        self.history.append({"role": "assistant", "content": answer})
        return answer
