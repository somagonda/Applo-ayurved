from __future__ import annotations

from difflib import SequenceMatcher
import re
from typing import Iterable


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


class MatchingService:
    def __init__(self, threshold: int = 58) -> None:
        self.threshold = threshold

    def best_match(self, user_text: str, options: Iterable[str]) -> str | None:
        choices = list(options)
        if not choices:
            return None

        normalized_input = normalize(user_text)
        normalized_options = {}
        for option in choices:
            normalized_options[option] = normalize(option)

        for option, normalized_option in normalized_options.items():
            if normalized_input == normalized_option:
                return option
            if normalized_input and normalized_input in normalized_option:
                return option

        try:
            from rapidfuzz import process

            match = process.extractOne(
                normalized_input,
                list(normalized_options.values()),
                score_cutoff=self.threshold,
            )
            if not match:
                return None
            matched_normalized = match[0]
            for option, normalized in normalized_options.items():
                if normalized == matched_normalized:
                    return option
            return None
        except ImportError:
            return self._difflib_match(normalized_input, normalized_options)

    def _difflib_match(self, text: str, normalized_options: dict[str, str]) -> str | None:
        scored = []
        for option, normalized in normalized_options.items():
            score = SequenceMatcher(None, text, normalized).ratio() * 100
            scored.append((score, option))
        score, option = max(scored, default=(0, None))
        if option and score >= self.threshold:
            return option
        return None
