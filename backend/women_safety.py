"""Women safety mode adjustments and recommendations."""

from __future__ import annotations

from typing import Any

from .danger_zone_detector import DangerZoneDetector
from .data_store import JsonDataStore
from .utils import clamp, coerce_datetime


class WomenSafetyMode:
    """Adds context-aware checks for women-focused route safety mode."""

    def __init__(self, store: JsonDataStore, danger_detector: DangerZoneDetector) -> None:
        self.store = store
        self.danger_detector = danger_detector

    def evaluate(self, route: list[str], departure_time: Any = None, enabled: bool = False) -> dict[str, Any]:
        if not enabled:
            return {
                "enabled": False,
                "risk_score": 0.0,
                "risk_adjustment": 0.0,
                "checks": [],
                "recommendations": [],
            }

        when = coerce_datetime(departure_time)
        zones = self.store.zones_by_id()
        low_light = [
            zones[zone_id]["name"]
            for zone_id in route
            if zones.get(zone_id, {}).get("lighting_score", 1.0) < 0.6
        ]
        limited_help = [
            zones[zone_id]["name"]
            for zone_id in route
            if zones.get(zone_id, {}).get("help_points", 0) == 0
        ]
        active_danger = [
            item["zone_name"]
            for item in self.danger_detector.list_danger_zones(when)
            if item["zone_id"] in route and item["active_now"]
        ]
        after_dark = when.hour >= 19 or when.hour <= 5

        risk_score = clamp(
            (0.18 if after_dark else 0.0)
            + min(len(low_light) / max(len(route), 1), 1) * 0.28
            + min(len(limited_help) / max(len(route), 1), 1) * 0.2
            + min(len(active_danger) / max(len(route), 1), 1) * 0.34
        )

        recommendations = [
            "Share live location before departure.",
            "Prefer pickup or drop-off at zones with help points.",
        ]
        if low_light:
            recommendations.append(f"Avoid low-light stretch: {', '.join(low_light)}.")
        if active_danger:
            recommendations.append(f"Active safety alert on: {', '.join(active_danger)}.")

        return {
            "enabled": True,
            "risk_score": round(risk_score, 3),
            "risk_adjustment": round(risk_score * 0.1, 3),
            "checks": [
                {"name": "After dark", "triggered": after_dark},
                {"name": "Low lighting", "triggered": bool(low_light), "zones": low_light},
                {"name": "Limited help points", "triggered": bool(limited_help), "zones": limited_help},
                {"name": "Active danger zone", "triggered": bool(active_danger), "zones": active_danger},
            ],
            "recommendations": recommendations,
        }
