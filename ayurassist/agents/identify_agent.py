from ayurassist.agents.base_agent import Agent


IDENTIFY_AGENT = Agent(
    name="IdentifyAgent",
    system_prompt=(
        "You identify the patient. Ask for a 10-digit registered mobile number. "
        "Call find_patient with the exact phone number. If the tool says the number "
        "is unknown, ask for the user's name and call find_patient with that name. "
        "Do not invent patient details."
    ),
)

