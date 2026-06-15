"""Small JSON data-store layer used by the demo MVP.

The project intentionally avoids a database so it stays hackathon-friendly:
all seed data, incident reports, and simulated SOS events live in JSON files.
"""

from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


class JsonDataStore:
    """Read and write JSON files with simple validation and atomic saves."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "simulated").mkdir(parents=True, exist_ok=True)

    def seed(self) -> None:
        """Ensure append-only runtime files exist for first-run demos."""
        self.read_json("incidents.json", default=[])
        self.read_json("sos_events.json", default=[])

    def path_for(self, filename: str) -> Path:
        return self.data_dir / filename

    def read_json(self, filename: str, default: Any | None = None) -> Any:
        path = self.path_for(filename)
        if not path.exists() or path.stat().st_size == 0:
            if default is None:
                raise FileNotFoundError(f"Missing data file: {filename}")
            self.write_json(filename, default)
            return default

        try:
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except JSONDecodeError as exc:
            if default is None:
                raise ValueError(f"Invalid JSON in {filename}: {exc}") from exc
            self.write_json(filename, default)
            return default

    def write_json(self, filename: str, payload: Any) -> None:
        path = self.path_for(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_suffix(path.suffix + ".tmp")
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)
            file.write("\n")
        temp_path.replace(path)

    def append_json(self, filename: str, item: dict[str, Any]) -> list[dict[str, Any]]:
        items = self.read_json(filename, default=[])
        if not isinstance(items, list):
            raise ValueError(f"{filename} must contain a JSON list")
        items.append(item)
        self.write_json(filename, items)
        return items

    def zones_by_id(self) -> dict[str, dict[str, Any]]:
        return {zone["id"]: zone for zone in self.read_json("city_zones_metadata.json", default=[])}
