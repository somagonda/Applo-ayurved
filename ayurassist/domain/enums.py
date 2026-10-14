from enum import Enum


class BookingStep(str, Enum):
    IDENTIFY = "identify"
    CITY = "city"
    CENTRE = "centre"
    DOCTOR = "doctor"
    DATE = "date"
    TIME = "time"
    CONFIRM = "confirm"
    COMPLETE = "complete"
    TRANSFERRED = "transferred"

