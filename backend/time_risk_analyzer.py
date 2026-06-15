"""Time-of-day risk scoring."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .data_store import JsonDataStore
from .utils import coerce_datetime


class TimeRiskAnalyzer:
    """Classifies a departure time into a risk bucket."""

    def __init__(self, store: JsonDataStore) -> None:
        self.store = store

    def analyze(self, departure_time: Any = None) -> dict[str, Any]:
        when = coerce_datetime(departure_time)
        config = self.store.read_json("time_risk_weights.json", default={})
        hour = when.hour

        for key, bucket in config.items():
            start_hour, end_hour = bucket.get("hours", [0, 23])
            if start_hour <= hour <= end_hour:
                return {
                    "period": key,
                    "label": bucket.get("label", key.title()),
                    "hour": hour,
                    "risk_score": float(bucket.get("risk", 0.3)),
                    "departure_time": when.isoformat(),
                }

        return {
            "period": "unknown",
            "label": "Unknown",
            "hour": hour,
            "risk_score": 0.3,
            "departure_time": when.isoformat(),
        }
