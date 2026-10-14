# Learning Log

## Phase 1

Date: 2026-10-08

What I learned: I learned how to set up a small Python project using `uv`, `pyproject.toml`, packages and modules. I also learned how to keep mock data in JSON files and read it from Python instead of hardcoding values in the chat flow.

JavaScript vs Python: Coming from JavaScript, Python imports and package structure felt stricter. I also learned that Python uses indentation as part of the language, so code formatting is more important than in JavaScript.

Resources and AI prompts: I used the take-home assignment document as the main checklist. I also used AI to ask basic Python questions, such as how dataclasses work, how to organize folders, and how to keep the code easy to explain.

Stuck points: `uv` was not installed at first, so I had to install it and understand the difference between `uv sync`, `uv run`, and running a Python module directly. I also had to fix the project setup so `uv run ayuvaid` worked cleanly.

AI usage during coding: Around 70 percent AI-assisted setup and 30 percent manual checking. I used AI for basic project structure help, but I manually ran the commands and checked the output.

Next: Build the basic terminal flow first, then connect the patient lookup and booking steps one by one.

## Phase 2

Date: 2026-10-09

What I learned: I learned how to use a shared `Session` dataclass to store the current patient, booking step, selected city, centre, doctor, date and time. I also learned how a handoff can be done by changing the active agent from IdentifyAgent to BookingAgent while keeping the same session state.

JavaScript vs Python: In JavaScript I would usually use plain objects for state. In Python, dataclasses made the state easier to see and explain. Enums also made the booking steps clearer than using many string values.

Resources and AI prompts: I used AI to understand how to separate responsibilities into simple files: models, services, repositories, tools and CLI. I kept asking for simpler explanations because I wanted the project to be easy to walk through in an interview.

Stuck points: I had to understand where validation should live. I learned that prompts should guide the conversation, but Python tools should validate phone numbers, names, cities, doctors, dates and time slots.

AI usage during coding: Around 65 percent AI-assisted implementation and 35 percent manual testing, changing inputs, checking edge cases and simplifying confusing parts.

Next: Add guardrails such as typo matching, two-failure transfer to human, and booking confirmation before saving.

## Phase 3

Date: 2026-10-10

What I learned: I learned the basics of `pytest` and how to test Python code without calling the OpenAI API. I also learned how to use a fake offline model so the conversation tests are predictable and free to run.

JavaScript vs Python: Pytest felt simpler than some JavaScript test setups because the tests are just Python functions with `assert`. I also learned how `tmp_path` helps tests use temporary data instead of changing the real `data/` files.

Resources and AI prompts: I used the assignment scoring points to decide what to test: happy path booking, escalation after two failures, typo matching, invalid phone numbers, invalid names, taken slots and duplicate bookings.

Stuck points: Date and time handling needed careful testing. I had to make sure the app offered dates in the next 7 days, did not offer already-booked slots, and did not create duplicate bookings.

AI usage during coding: Around 60 percent AI-assisted test drafting and 40 percent manual verification by running the terminal app, trying wrong inputs, and checking the output.

Next: Keep the final version clean for submission, with README steps, `.env.example`, `uv.lock`, tests and a simple walkthrough guide.

## Phase 4

Date: 2026-10-12

What I learned: I learned how important edge-case testing is for a chat flow. I tested invalid phone numbers, invalid names, typo inputs, already-booked slots, duplicate bookings, unclear time inputs and the transfer-to-human path.

JavaScript vs Python: In JavaScript I usually test flows manually in the browser or console. In Python, I learned to put these checks into `pytest` functions so the same cases can be repeated quickly.

Resources and AI prompts: I used AI to think through possible bad inputs a real user may type, such as extra digits in a phone number, random text instead of a city, or entering only `11` when both `11:00` and `11:30` are available.

Stuck points: Some edge cases looked correct in one mode but behaved differently in real OpenAI mode. I fixed this by forcing the current Python tool to run and by making sure the tool receives the exact user text.

AI usage during coding: Around 50 percent AI-assisted review and 50 percent manual terminal testing. I personally ran the app with different wrong inputs and checked whether the bot response made sense.

Next: Do a final demo run from a clean setup using `uv sync`, `uv run ayuvaid`, and `uv run pytest`.

## Phase 5

Date: 2026-10-14

What I learned: I learned how to clean a Python project before submission. I checked which files should be shared, which files should stay local, and how to make the app run with a simple command: `uv run ayuvaid`.

JavaScript vs Python: In JavaScript projects I am used to `npm install` and `npm run`. In this Python project, I learned the similar flow with `uv sync`, `uv run ayuvaid`, and `uv run pytest`.

Resources and AI prompts: I used AI to review the final project structure, `.gitignore`, README, docs and learning log. I also asked for interview-style review notes so I could understand the Python code line by line.

Stuck points: The project initially showed a `uv` packaging warning because the app command was not installed as an entry point. I fixed the project configuration so `uv sync` installs the package and `uv run ayuvaid` works.

AI usage during coding: Around 50 percent AI-assisted cleanup and 50 percent manual checking. I manually checked the run commands, ignored files, tests and final folders before preparing for submission.

Next: Share the GitHub repository with the reviewer, run one final demo, and be ready to explain the code walkthrough and live-change areas.
