# Project Structure

This project is organized so each folder has one simple job.

## Main Flow

```text
ayurassist/main.py
  starts the terminal app

ayurassist/cli/interface.py
  prints You and AyuAssist messages

ayurassist/application/conversation_manager.py
  keeps chat history, session state, current agent and tool wiring

ayurassist/application/agent_router.py
  switches IdentifyAgent to BookingAgent using Session.step
```

## Agent Layer

```text
ayurassist/agents/identify_agent.py
  prompt for patient identification

ayurassist/agents/booking_agent.py
  prompt for booking flow
```

The prompts guide conversation only. They do not own clinic facts or booking decisions.

## State and Business Logic

```text
ayurassist/domain/models.py
  dataclasses for Patient, Session and selected appointment choices

ayurassist/domain/enums.py
  BookingStep values: identify, city, centre, doctor, date, time, confirm

ayurassist/tools/toolbox.py
  the main editable booking flow; one public method per step

ayurassist/services/
  reusable business logic such as matching, availability and saving bookings
```

## Data Access

```text
ayurassist/repositories/
  small JSON read/write classes

data/
  patients.json, centres.json, slots.json and bookings.json
```

Only repositories touch JSON files directly.

## LLM Adapters

```text
ayurassist/llm/openai_client.py
  real OpenAI SDK tool-calling adapter

ayurassist/llm/offline_demo_model.py
  fake deterministic adapter for tests and demo without API calls
```

## Common Live Changes

Add or edit a validation rule:
`ayurassist/tools/toolbox.py`

Change typo matching:
`ayurassist/services/matching_service.py`

Change available dates or duplicate-slot logic:
`ayurassist/services/availability_service.py`

Add a patient, city, centre, doctor or slot:
`data/*.json`

Add or update tests:
`tests/test_booking_tools.py`
