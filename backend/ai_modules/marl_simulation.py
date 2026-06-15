"""Simulated multi-agent reinforcement learning response planner."""

from __future__ import annotations

from typing import Any

from ..data_store import JsonDataStore
from ..utils import clamp, mean


class MARLSimulation:
    """Approximates how multiple safety agents would reduce route risk."""

    def __init__(self, store: JsonDataStore) -> None:
        self.store = store

    def simulate(self, route: list[str], base_risk: float, women_mode: bool = False) -> dict[str, Any]:
        zones = self.store.zones_by_id()
        route_zones = [zones[zone_id] for zone_id in route if zone_id in zones]

        avg_police_eta = mean([zone.get("police_eta_min", 10) for zone in route_zones], default=10)
        avg_cctv = mean([zone.get("cctv_coverage", 0.5) for zone in route_zones], default=0.5)
        avg_crowd = mean([zone.get("crowd_density", 0.5) for zone in route_zones], default=0.5)
        help_points = sum(zone.get("help_points", 0) for zone in route_zones)

        patrol_mitigation = clamp((1 - min(avg_police_eta / 20, 1)) * 0.11 + avg_cctv * 0.06)
        crowd_mitigation = clamp(avg_crowd * 0.07)
        escort_mitigation = clamp((help_points / max(len(route_zones), 1)) * 0.05 + (0.06 if women_mode else 0))
        total_mitigation = clamp(patrol_mitigation + crowd_mitigation + escort_mitigation, 0.0, 0.32)
        residual_risk = clamp(base_risk * (1 - total_mitigation))

        return {
            "model": "Simulated-MARL",
            "base_risk": round(base_risk, 3),
            "risk_score": round(residual_risk, 3),
            "mitigation_score": round(total_mitigation, 3),
            "agents": [
                {
                    "name": "PatrolAgent",
                    "action": "prioritize patrol visibility near slow-response zones",
                    "mitigation": round(patrol_mitigation, 3),
                },
                {
                    "name": "CrowdFlowAgent",
                    "action": "prefer well-populated connectors without routing through crowd crush points",
                    "mitigation": round(crowd_mitigation, 3),
                },
                {
                    "name": "EscortAgent",
                    "action": "surface help points and guarded pickup areas",
                    "mitigation": round(escort_mitigation, 3),
                },
            ],
        }
