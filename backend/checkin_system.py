"""Safety Command Center — aggregates system-wide status for the dashboard."""

from __future__ import annotations

from typing import Any

from .data_store import JsonDataStore


class SafetyCommandCenter:
    """Provides real-time aggregated safety telemetry for the command center dashboard."""

    def __init__(self, store: JsonDataStore) -> None:
        self.store = store

    def get_status(self) -> dict[str, Any]:
        """Return a full command center status snapshot."""
        zones = self.store.read_json("city_zones_metadata.json", default=[])
        guardians = self.store.read_json("guardian_contacts.json", default=[])
        profile = self.store.read_json("user_profiles.json", default={})
        police = self.store.read_json("police_stations.json", default={"stations": []})
        hospitals = self.store.read_json("hospitals.json", default={"hospitals": []})
        incidents = self.store.read_json("incident_reports.json", default=[])
        danger = self.store.read_json("danger_zones.json", default=[])

        # Calculate city-wide safety average
        if zones:
            avg_safety = 1 - (sum(z.get("crime_index", 0.5) for z in zones) / len(zones))
        else:
            avg_safety = 0.5

        # Active danger zones count
        active_dangers = len(danger)

        # Total incidents in last 30 days
        total_incidents = len(incidents)

        return {
            "city_safety_score": round(avg_safety, 2),
            "total_zones": len(zones),
            "active_danger_zones": active_dangers,
            "total_incidents": total_incidents,
            "guardian_count": len(guardians),
            "max_guardians": 5,
            "profile_complete": bool(profile.get("name")),
            "police_stations_count": len(police.get("stations", [])),
            "hospitals_count": len(hospitals.get("hospitals", [])),
            "profile_name": profile.get("name", "Not Set"),
        }
