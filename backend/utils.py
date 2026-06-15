"""Shared utility helpers for the UrbanShield backend."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    """Keep a numeric score inside a predictable 0..1 range."""
    return max(minimum, min(maximum, float(value)))


def mean(values: Iterable[float], default: float = 0.0) -> float:
    numbers = [float(value) for value in values]
    if not numbers:
        return default
    return sum(numbers) / len(numbers)


def coerce_datetime(value: Any = None) -> datetime:
    """Accept datetime objects or ISO strings from APIs and normalize them."""
    if isinstance(value, datetime):
        return value
    if not value:
        return datetime.now()
    if isinstance(value, str):
        clean_value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(clean_value)
    raise ValueError("departure_time must be an ISO datetime string")


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
