"""Incident reporting and incident-derived risk scoring."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from .data_store import JsonDataStore
from .utils import clamp, now_utc_iso


SEVERITY_SCORES = {
    "low": 0.25,
    "medium": 0.5,
    "high": 0.75,
    "critical": 0.95,
}


class IncidentReporter:
    """Persists citizen reports and converts recent history into risk."""

    def __init__(self, store: JsonDataStore) -> None:
        self.store = store

    def report(
        self,
        zone_id: str,
        incident_type: str,
        description: str = "",
        severity: str = "medium",
    ) -> dict[str, Any]:
        if zone_id not in self.store.zones_by_id():
            raise ValueError(f"Unknown zone_id: {zone_id}")

        severity_key = severity.lower()
        incident = {
            "id": f"INC-{uuid4().hex[:8].upper()}",
            "zone_id": zone_id,
            "incident_type": incident_type,
            "description": description,
            "severity": severity_key,
            "severity_score": SEVERITY_SCORES.get(severity_key, 0.5),
            "status": "received",
            "created_at": now_utc_iso(),
        }
        self.store.append_json("incidents.json", incident)
        return incident

    def list_incidents(self, limit: int = 20) -> list[dict[str, Any]]:
        incidents = self.store.read_json("incidents.json", default=[])
        zones = self.store.zones_by_id()
        out = []
        for inc in incidents:
            zone = zones.get(inc.get("zone_id"))
            inc_copy = dict(inc)
            if zone:
                inc_copy["zone_name"] = zone["name"]
            out.append(inc_copy)
        return list(reversed(out[-limit:]))

    def route_incident_risk(self, route: list[str]) -> float:
        history = self.store.read_json("simulated/mock_crime_history.json", default={})
        live_incidents = self.store.read_json("incidents.json", default=[])
        route_set = set(route)

        history_score = 0.0
        for zone_id in route:
            zone_history = history.get(zone_id, {})
            history_score += min(zone_history.get("recent_incidents_30d", 0) / 30, 1) * 0.7
            history_score += min(zone_history.get("harassment_reports", 0) / 10, 1) * 0.3

        live_score = sum(
            incident.get("severity_score", 0.5)
            for incident in live_incidents
            if incident.get("zone_id") in route_set
        )
        route_length = max(len(route), 1)
        return clamp((history_score / route_length) * 0.75 + min(live_score / 5, 1) * 0.25)
