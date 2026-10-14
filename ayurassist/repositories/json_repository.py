from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonRepository:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def read(self, filename: str) -> Any:
        path = self.data_dir / filename
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def write(self, filename: str, data: Any) -> None:
        path = self.data_dir / filename
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)
            file.write("\n")
