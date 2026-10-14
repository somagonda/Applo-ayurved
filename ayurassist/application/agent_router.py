from ayurassist.agents.base_agent import Agent
from ayurassist.agents.booking_agent import BOOKING_AGENT
from ayurassist.agents.identify_agent import IDENTIFY_AGENT
from ayurassist.domain.enums import BookingStep
from ayurassist.domain.models import Session


class AgentRouter:
    def current_agent(self, session: Session) -> Agent:
        if session.step == BookingStep.IDENTIFY:
            return IDENTIFY_AGENT
        return BOOKING_AGENT

