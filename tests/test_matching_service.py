from ayurassist.services.matching_service import MatchingService


def test_fuzzy_city_match_handles_typo() -> None:
    matcher = MatchingService()

    assert matcher.best_match("banglore", ["Bengaluru", "Kochi", "Pune"]) == "Bengaluru"


def test_partial_doctor_match() -> None:
    matcher = MatchingService()

    assert matcher.best_match("Dr Fatima", ["Dr. Fatima Shaikh", "Dr. Geeta Rao"]) == "Dr. Fatima Shaikh"

