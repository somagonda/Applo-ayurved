# Walkthrough Notes

Use this as a 60 minute call guide.

## 10 minute demo

Run:

```bash
uv run ayuvaid --offline-demo
```

Suggested inputs:

```text
4444444441
banglore
jaynagar
geeta
<choose one of the dates printed by AyuAssist>
10:30
yes
```

Choose one of the dates and times printed by AyuAssist during the demo.

## 20 minute code walkthrough

1. Start at `ayurassist/main.py`.
2. Move to `ayurassist/application/conversation_manager.py` to show shared `Session` state.
3. Open `ayurassist/application/agent_router.py` to show the IdentifyAgent to BookingAgent handoff.
4. Open `ayurassist/tools/toolbox.py`; this is the core of the booking flow.
5. Open `ayurassist/services/matching_service.py` and `ayurassist/services/availability_service.py` for guardrails.
6. Open `tests/test_booking_tools.py` to show happy path and escalation tests.

## 20 minute live change

Good live-change options:

- Add a new city, centre, doctor and slots in `data/centres.json` and `data/slots.json`.
- Change the escalation message in `BookingToolbox._transfer`.
- Add a unit test for an already-booked slot.

## 10 minute unfamiliar code

Explain a file by following names:

- Repository files read and write JSON.
- Service files make business decisions.
- Tool methods change session state.
- The conversation manager connects user messages, agents and tools.
