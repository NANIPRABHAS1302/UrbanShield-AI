"""Simulated CNN module.

For the MVP we do not run real computer vision. Instead, this module behaves
like a CNN inference wrapper by consuming precomputed CCTV-like signals and
returning a normalized safety risk score.
"""

from __future__ import annotations

from typing import Any

from ..data_store import JsonDataStore
from ..utils import clamp, mean


class SimulatedCNNModule:
    """Converts mock CCTV telemetry into risk classifications."""

    def __init__(self, store: JsonDataStore) -> None:
        self.store = store

    def analyze_zone(self, zone_id: str) -> dict[str, Any]:
        feed = self.store.read_json("simulated/mock_cctv_feed.json", default={}).get(zone_id, {})
        risk_score = clamp(
            feed.get("anomaly_score", 0.2) * 0.42
            + (1 - feed.get("lighting_quality", 0.75)) * 0.24
            + (1 - feed.get("motion_stability", 0.7)) * 0.18
            + (1 - feed.get("camera_health", 0.8)) * 0.16
        )
        label = "normal"
        if risk_score >= 0.65:
            label = "alert"
        elif risk_score >= 0.4:
            label = "watch"

        return {
            "zone_id": zone_id,
            "risk_score": round(risk_score, 3),
            "classification": label,
            "simulated": True,
            "signals": feed,
        }

    def analyze_route(self, route: list[str]) -> dict[str, Any]:
        zones = [self.analyze_zone(zone_id) for zone_id in route]
        scores = [zone["risk_score"] for zone in zones]
        return {
            "model": "SimulatedCNN",
            "route_risk": round(mean(scores), 3),
            "max_zone_risk": round(max(scores) if scores else 0.0, 3),
            "zone_predictions": zones,
            "hotspots": [zone for zone in zones if zone["risk_score"] >= 0.4],
        }
