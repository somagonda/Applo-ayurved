# AyurAssist

AyurAssist is a terminal chat app for booking a fictional Ayurveda clinic consultation. It follows the assignment rule that the LLM handles conversation while Python owns facts, validation, state, guardrails and persistence.

## Run in 5 commands

```bash
uv sync
cp .env.example .env
uv run ayuvaid --offline-demo
uv run ayuvaid
uv run pytest
```

Use `--offline-demo` for the walkthrough if the OpenAI key or internet connection is not ready. The normal mode uses the official OpenAI Python SDK directly with tool calling. The `ayuvaid` command is installed by `uv sync`.

## Walkthrough Map

- `ayurassist/main.py` starts the terminal app.
- `ayurassist/application/conversation_manager.py` keeps conversation history, shared session state and the current agent.
- `ayurassist/agents/` contains the two prompts: `IdentifyAgent` and `BookingAgent`.
- `ayurassist/tools/toolbox.py` is the best file for a live change. Each booking step has one obvious method.
- `ayurassist/services/` contains business rules for matching, availability, patient lookup and booking persistence.
- `ayurassist/repositories/` is the only layer that reads or writes JSON files.
- `tests/` proves the tools and conversation flow without calling OpenAI.

For a fuller file-by-file map, see `docs/project_structure.md`.

## Design Choices

The project is intentionally small enough to explain in a 20 minute code walkthrough. The handoff is a prompt and toolset switch driven by `Session.step`; the same `Session` dataclass survives across both agents. Tool methods validate every user choice against JSON data before the bot says it back to the user.

Dependencies:

- `openai`: required by the exercise for direct SDK tool calling.
- `rapidfuzz`: typo and partial-name matching, with a small `difflib` fallback for local demos.
- `python-dotenv`: loads `.env` locally without committing secrets.
- `pytest`: deterministic tests.

## Demo Script

```text
4444444441
banglore
jaynagar
geeta
<choose one of the dates printed by AyuAssist>
10:30
yes
```

Dates depend on the day you run the app. In the demo, choose one of the dates printed by AyuAssist, then choose one of the printed times.

## Assumptions

Unknown patients are registered only in session memory, because the assignment says to register them in memory. Bookings are appended to `data/bookings.json` only after explicit confirmation.
