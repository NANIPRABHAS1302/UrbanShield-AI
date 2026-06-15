"""Simulated SOS dispatch flow."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from .data_store import JsonDataStore
from .utils import now_utc_iso


class SOSSystem:
    """Stores SOS requests and returns the contacts that would be notified."""

    def __init__(self, store: JsonDataStore) -> None:
        self.store = store

    def trigger(
        self,
        user_name: str,
        zone_id: str,
        message: str = "",
        lat: float | None = None,
        lng: float | None = None,
        risk_level: str = "UNKNOWN",
        women_mode: bool = False,
        category: str = "unsafe_area",
    ) -> dict[str, Any]:
        zones = self.store.zones_by_id()
        if zone_id not in zones:
            raise ValueError(f"Unknown zone_id: {zone_id}")

        zone = zones[zone_id]
        contacts = sorted(
            self.store.read_json("emergency_contacts.json", default=[]),
            key=lambda item: item.get("priority", 99),
        )
        selected_contacts = [
            contact
            for contact in contacts
            if contact["type"] in {"police", "emergency", "women_safety"}
            or contact.get("priority") == 1
        ]

        event = {
            "id": f"SOS-{uuid4().hex[:8].upper()}",
            "user_name": user_name or "UrbanShield User",
            "zone_id": zone_id,
            "zone_name": zone["name"],
            "category": category,
            "lat": lat if lat is not None else zone.get("lat"),
            "lng": lng if lng is not None else zone.get("lng"),
            "message": message or "SOS triggered from UrbanShield AI",
            "risk_level": risk_level,
            "women_mode": women_mode,
            "status": "simulated_dispatch_sent",
            "created_at": now_utc_iso(),
            "notified_contacts": selected_contacts,
        }
        self.store.append_json("sos_events.json", event)
        return event

    def recent_events(self, limit: int = 10) -> list[dict[str, Any]]:
        events = self.store.read_json("sos_events.json", default=[])
        return list(reversed(events[-limit:]))
