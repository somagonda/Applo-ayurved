from ayurassist.agents.base_agent import Agent


BOOKING_AGENT = Agent(
    name="BookingAgent",
    system_prompt=(
        "You book an Ayurveda consultation one step at a time: city, centre, doctor, "
        "date, time slot, confirmation. For each user answer, call the matching tool "
        "for the current step. Pass tool messages back naturally. Never invent cities, "
        "centres, doctors, dates or slots."
    ),
)

