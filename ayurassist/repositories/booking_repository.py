from ayurassist.repositories.json_repository import JsonRepository


class BookingRepository:
    def __init__(self, store: JsonRepository) -> None:
        self.store = store

    def all(self) -> list[dict]:
        return self.store.read("bookings.json")

    def append(self, booking: dict) -> None:
        bookings = self.all()
        bookings.append(booking)
        self.store.write("bookings.json", bookings)
