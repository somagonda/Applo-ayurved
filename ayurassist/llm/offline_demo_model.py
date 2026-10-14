from __future__ import annotations

from ayurassist.agents.base_agent import Agent
from ayurassist.domain.enums import BookingStep
from ayurassist.tools.toolbox import BookingToolbox


class OfflineDemoModel:
    """Deterministic stand-in for demos and tests; it never calls OpenAI."""

    def reply(self, agent: Agent, history: list[dict], toolbox: BookingToolbox) -> str:
        user_text = history[-1]["content"]
        step = toolbox.session.step
        tool_by_step = {
            BookingStep.IDENTIFY: "find_patient",
            BookingStep.CITY: "select_city",
            BookingStep.CENTRE: "select_centre",
            BookingStep.DOCTOR: "select_doctor",
            BookingStep.DATE: "select_date",
            BookingStep.TIME: "select_time_slot",
            BookingStep.CONFIRM: "confirm_booking",
        }
        tool_name = tool_by_step.get(step)
        if not tool_name:
            return "This session is complete."
        return toolbox.call(tool_name, user_text).message
