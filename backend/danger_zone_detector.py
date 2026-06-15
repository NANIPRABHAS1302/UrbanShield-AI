"""Danger-zone lookup and active-window scoring."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .data_store import JsonDataStore
from .utils import clamp, coerce_datetime


def _minutes(value: str) -> int:
    hour, minute = value.split(":")
    return int(hour) * 60 + int(minute)


def _is_active(active_from: str, active_to: str, when: datetime) -> bool:
    start = _minutes(active_from)
    end = _minutes(active_to)
    current = when.hour * 60 + when.minute
    if start <= end:
        return start <= current <= end
    return current >= start or current <= end


class DangerZoneDetector:
    """Combines static danger zones with the current time window."""

    def __init__(self, store: JsonDataStore) -> None:
        self.store = store

    def list_danger_zones(self, when: Any = None) -> list[dict[str, Any]]:
        departure = coerce_datetime(when)
        zones = self.store.zones_by_id()
        danger_zones = self.store.read_json("danger_zones.json", default=[])
        output = []

        for item in danger_zones:
            zone = zones.get(item["zone_id"], {})
            active = _is_active(item["active_from"], item["active_to"], departure)
            output.append(
                {
                    **item,
                    "zone_name": zone.get("name", item["zone_id"]),
                    "category": zone.get("category", "Unknown"),
                    "lat": zone.get("lat"),
                    "lng": zone.get("lng"),
                    "active_now": active,
                    "effective_risk": clamp(item["severity"] if active else item["severity"] * 0.45),
                }
            )

        return sorted(output, key=lambda value: value["effective_risk"], reverse=True)

    def zone_risk(self, zone_id: str, when: Any = None) -> float:
        for item in self.list_danger_zones(when):
            if item["zone_id"] == zone_id:
                return float(item["effective_risk"])
        return 0.0
