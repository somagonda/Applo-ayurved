from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


@dataclass(frozen=True)
class Settings:
    data_dir: Path = DATA_DIR
    model: str = os.getenv("OPENAI_MODEL", "gpt-5-nano")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")


def load_settings() -> Settings:
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    return Settings(
        data_dir=DATA_DIR,
        model=os.getenv("OPENAI_MODEL", "gpt-5-nano"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )
