"""Risk heatmap data generation for dashboard visualizations."""

from __future__ import annotations

from typing import Any

from .danger_zone_detector import DangerZoneDetector
from .data_store import JsonDataStore
from .utils import clamp


class HeatmapGenerator:
    """Produces per-zone risk points that the frontend can render."""

    def __init__(self, store: JsonDataStore, danger_detector: DangerZoneDetector) -> None:
        self.store = store
        self.danger_detector = danger_detector

    def generate(self, when: Any = None) -> list[dict[str, Any]]:
        zones = self.store.read_json("city_zones_metadata.json", default=[])
        cctv = self.store.read_json("simulated/mock_cctv_feed.json", default={})
        crowd = self.store.read_json("simulated/mock_crowd_density.json", default={})
        crime = self.store.read_json("simulated/mock_crime_history.json", default={})

        heatmap = []
        for zone in zones:
            zone_id = zone["id"]
            camera = cctv.get(zone_id, {})
            density = crowd.get(zone_id, {})
            history = crime.get(zone_id, {})
            danger_risk = self.danger_detector.zone_risk(zone_id, when)

            risk_score = clamp(
                zone.get("crime_index", 0.3) * 0.28
                + (1 - zone.get("lighting_score", 0.7)) * 0.18
                + (1 - zone.get("cctv_coverage", 0.7)) * 0.14
                + danger_risk * 0.22
                + camera.get("anomaly_score", 0.2) * 0.1
                + (1 - density.get("current_density", 0.5)) * 0.08
                + min(history.get("recent_incidents_30d", 0) / 30, 1) * 0.1
            )

            heatmap.append(
                {
                    "zone_id": zone_id,
                    "zone_name": zone["name"],
                    "category": zone["category"],
                    "lat": zone["lat"],
                    "lng": zone["lng"],
                    "risk_score": round(risk_score, 3),
                    "status": "critical" if risk_score >= 0.75 else "watch" if risk_score >= 0.5 else "stable",
                    "signals": {
                        "lighting_score": zone.get("lighting_score"),
                        "crowd_density": density.get("current_density", zone.get("crowd_density")),
                        "cctv_coverage": zone.get("cctv_coverage"),
                        "danger_risk": round(danger_risk, 3),
                    },
                }
            )

        return sorted(heatmap, key=lambda item: item["risk_score"], reverse=True)
