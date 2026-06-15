"""Central orchestration layer for UrbanShield AI."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .ai_modules.cnn_module import SimulatedCNNModule
from .ai_modules.gnn_module import GraphSafetyAnalyzer
from .ai_modules.marl_simulation import MARLSimulation
from .ai_modules.risk_classifier import RiskClassifier
from .danger_zone_detector import DangerZoneDetector
from .data_store import JsonDataStore
from .heatmap_generator import HeatmapGenerator
from .incident_reporter import IncidentReporter
from .route_optimizer import RouteOptimizer
from .sos_system import SOSSystem
from .time_risk_analyzer import TimeRiskAnalyzer
from .utils import clamp, coerce_datetime, mean
from .women_safety import WomenSafetyMode


class SafetyEngine:
    """Coordinates all safety modules behind the FastAPI endpoints."""

    def __init__(self) -> None:
        self.store = JsonDataStore()
        self.store.seed()
        self.danger_detector = DangerZoneDetector(self.store)
        self.heatmap_generator = HeatmapGenerator(self.store, self.danger_detector)
        self.time_analyzer = TimeRiskAnalyzer(self.store)
        self.cnn = SimulatedCNNModule(self.store)
        self.gnn = GraphSafetyAnalyzer(self.store)
        self.marl = MARLSimulation(self.store)
        self.classifier = RiskClassifier()
        self.women_mode = WomenSafetyMode(self.store, self.danger_detector)
        self.route_optimizer = RouteOptimizer(self.store, self.gnn)
        self.incidents = IncidentReporter(self.store)
        self.sos = SOSSystem(self.store)

    def zones(self) -> list[dict[str, Any]]:
        return self.store.read_json("city_zones_metadata.json", default=[])

    def dashboard(self) -> dict[str, Any]:
        heatmap = self.heatmap_generator.generate(datetime.now())
        danger_zones = self.danger_detector.list_danger_zones(datetime.now())
        incidents = self.incidents.list_incidents(limit=8)
        sos_events = self.sos.recent_events(limit=5)
        return {
            "project": "UrbanShield AI",
            "status": "online",
            "zones_count": len(self.zones()),
            "high_risk_zones": [zone for zone in heatmap if zone["risk_score"] >= 0.55],
            "heatmap": heatmap,
            "danger_zones": danger_zones,
            "recent_incidents": incidents,
            "recent_sos_events": sos_events,
            "model_pipeline": [
                "Simulated CNN",
                "NetworkX GNN",
                "Simulated MARL Agents",
                "Risk Classifier",
                "Women Safety Mode",
                "SOS System",
            ],
        }

    def analyze_route(
        self,
        start_zone: str,
        end_zone: str,
        departure_time: Any = None,
        women_mode: bool = False,
        route_preference: str = "safest",
    ) -> dict[str, Any]:
        zones = self.store.zones_by_id()
        if start_zone not in zones:
            raise ValueError(f"Unknown start_zone: {start_zone}")
        if end_zone not in zones:
            raise ValueError(f"Unknown end_zone: {end_zone}")
        if start_zone == end_zone:
            raise ValueError("start_zone and end_zone must be different")

        departure = coerce_datetime(departure_time)
        time_context = self.time_analyzer.analyze(departure)
        candidates = self.route_optimizer.alternatives(start_zone, end_zone, women_mode=women_mode)
        evaluated = [
            self._evaluate_route(candidate, departure, time_context, women_mode)
            for candidate in candidates
        ]
        evaluated = self._sort_routes(evaluated, route_preference)

        return {
            "query": {
                "start_zone": start_zone,
                "start_name": zones[start_zone]["name"],
                "end_zone": end_zone,
                "end_name": zones[end_zone]["name"],
                "departure_time": departure.isoformat(),
                "women_mode": women_mode,
                "route_preference": route_preference,
            },
            "recommended_route": evaluated[0],
            "alternatives": evaluated,
            "time_context": time_context,
            "available_zones": self.zone_options(),
        }

    def _evaluate_route(
        self,
        candidate: dict[str, Any],
        departure: datetime,
        time_context: dict[str, Any],
        women_mode: bool,
    ) -> dict[str, Any]:
        route = candidate["zone_ids"]
        zones = self.store.zones_by_id()
        weights = self.store.read_json("safety_weights_config.json", default={})

        cnn_result = self.cnn.analyze_route(route)
        gnn_result = candidate["metrics"]
        incident_risk = self.incidents.route_incident_risk(route)
        marl_base = mean([cnn_result["route_risk"], gnn_result["route_risk"], incident_risk])
        marl_result = self.marl.simulate(route, marl_base, women_mode=women_mode)
        women_result = self.women_mode.evaluate(route, departure, enabled=women_mode)

        signals = {
            "cnn": cnn_result["route_risk"],
            "gnn": gnn_result["route_risk"],
            "marl": marl_result["risk_score"],
            "time": time_context["risk_score"],
            "incident": incident_risk,
            "women_mode": women_result["risk_score"],
        }
        classification = self.classifier.combine(signals, weights)

        return {
            "preference": candidate["preference"],
            "zone_ids": route,
            "zone_names": [zones[zone_id]["name"] for zone_id in route],
            "distance_km": gnn_result["distance_km"],
            "travel_time_min": gnn_result["travel_time_min"],
            "risk": classification,
            "model_outputs": {
                "cnn": cnn_result,
                "gnn": gnn_result,
                "marl": marl_result,
                "women_safety": women_result,
                "incident_risk": round(clamp(incident_risk), 3),
            },
            "recommendations": self._recommendations(classification, women_result, cnn_result),
        }

    def _sort_routes(self, routes: list[dict[str, Any]], preference: str) -> list[dict[str, Any]]:
        if preference == "fastest":
            return sorted(routes, key=lambda route: (route["travel_time_min"], route["risk"]["score"]))
        if preference == "balanced":
            return sorted(routes, key=lambda route: route["risk"]["score"] * 0.7 + route["travel_time_min"] / 100)
        return sorted(routes, key=lambda route: route["risk"]["score"])

    def _recommendations(
        self,
        classification: dict[str, Any],
        women_result: dict[str, Any],
        cnn_result: dict[str, Any],
    ) -> list[str]:
        recommendations = [classification["action"]]
        if cnn_result.get("hotspots"):
            hotspot_ids = [item["zone_id"] for item in cnn_result["hotspots"]]
            zone_names = self.store.zones_by_id()
            recommendations.append(
                "Camera simulation flagged: "
                + ", ".join(zone_names[zone_id]["name"] for zone_id in hotspot_ids if zone_id in zone_names)
                + "."
            )
        recommendations.extend(women_result.get("recommendations", []))
        return recommendations

    def zone_options(self) -> list[dict[str, str]]:
        return [{"id": zone["id"], "name": zone["name"]} for zone in self.zones()]

    def danger_zones(self, departure_time: Any = None) -> list[dict[str, Any]]:
        return self.danger_detector.list_danger_zones(departure_time)

    def report_incident(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.incidents.report(
            zone_id=payload["zone_id"],
            incident_type=payload.get("incident_type", "suspicious_activity"),
            description=payload.get("description", ""),
            severity=payload.get("severity", "medium"),
        )

    def trigger_sos(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.sos.trigger(
            user_name=payload.get("user_name", "UrbanShield User"),
            zone_id=payload["zone_id"],
            message=payload.get("message", ""),
            lat=payload.get("lat"),
            lng=payload.get("lng"),
            risk_level=payload.get("risk_level", "UNKNOWN"),
            women_mode=payload.get("women_mode", False),
            category=payload.get("sos_category", "unsafe_area"),
        )
